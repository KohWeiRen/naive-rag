import argparse
import json
import re
from pathlib import Path, PurePosixPath
from time import perf_counter
from uuid import uuid4

from pgvector.psycopg import register_vector

from backend.database.db import get_connection
from backend.ingest import identify_document, prepare_search_plan, rank_chunks_with_rrf, retrieve_candidates, load_instructions
from backend.schema import SearchPlanningPolicy
from backend.models.driver import call_llm

EVAL_SET_PATH = Path(__file__).with_name("eval.json")
TOP_K = 8


def normalize_evidence(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def expected_document(source):
    path = PurePosixPath(source.replace("\\", "/"))
    if "docs" in path.parts:
        path = PurePosixPath(*path.parts[path.parts.index("docs") + 1:])
    return identify_document(path, PurePosixPath("."))


def describe_chunk(documents, document_id, chunk_index, rank):
    source_key, source_version = documents[document_id]
    return {
        "rank": rank,
        "document_id": str(document_id),
        "chunk_index": chunk_index,
        "source_key": source_key,
        "source_version": source_version,
    }


def evaluate_retrieval(connection, documents, case, policy, *, generate_answer=True):
    start = perf_counter()
    expected_source, expected_version = expected_document(case["expected_source"])
    passages = case["expected_evidence"]
    if isinstance(passages, str):
        passages = [passages]
    normalized_passages = [normalize_evidence(passage) for passage in passages]
    if not normalized_passages or not all(normalized_passages):
        raise ValueError("Each retrieval case needs nonempty expected evidence.")
    session_id = uuid4()
    plan = prepare_search_plan(
        session_id=session_id,
        query={"role": "user", "content": case["question"]},
        history=case.get("history", []),
        policy=policy,
    )
    searches = []
    if plan["status"] == "ready":
        searches = retrieve_candidates(connection, plan, question=case["question"])
    shortlist = rank_chunks_with_rrf([hits for _, _, hits in searches], top=TOP_K)
    elapsed_ms = round((perf_counter() - start) * 1000, 2)

    def match_evidence(source, content):
        if source != expected_source:
            return []
        normalized_chunk = f" {normalize_evidence(content)} "
        return [
            index
            for index, passage in enumerate(normalized_passages)
            if f" {passage} " in normalized_chunk
        ]

    candidate_lists = []
    for method, search_text, hits in searches:
        candidates = []
        for rank, (document_id, chunk_index, content) in enumerate(hits, start=1):
            chunk = describe_chunk(documents, document_id, chunk_index, rank)
            chunk["evidence_matches"] = match_evidence(chunk["source_key"], content)
            candidates.append(chunk)
        candidate_lists.append({
            "search_text": search_text,
            "method": method,
            "chunks": candidates,
        })

    top_chunks = []
    for rank, hit in enumerate(shortlist, start=1):
        chunk = describe_chunk(documents, hit["document_id"], hit["chunk_index"], rank)
        chunk["rrf_score"] = hit["rrf_score"]
        chunk["evidence_matches"] = match_evidence(chunk["source_key"], hit["content"])
        top_chunks.append(chunk)

    answer = plan.get("clarification_question")
    if plan["status"] == "ready" and generate_answer:
        payload = {
            "current_query": case["question"],
            "history": case.get("history", []),
            "sources": [
                {"source_id": f"S{i}", "content": chunk["content"]}
                for i, chunk in enumerate(shortlist, start=1)
            ],
        }
        response = call_llm(
            messages=[
                {
                    "role" : "system", "content" : load_instructions(task="query_answering")
                },
                {
                    "role" : "user", "content" : json.dumps(payload)
                }
            ], # insert instruction, current query, past history and limits
            max_output_tokens=2048,
            session_id=session_id
        )
        answer = response["content"]

    covered = {index for chunk in top_chunks for index in chunk["evidence_matches"]}
    return {
        "question": case["question"],
        "expected_answer": case["expected_answer"],
        "expected_source": expected_source,
        "expected_version": expected_version,
        "expected_evidence": passages,
        "status": plan["status"],
        "clarification_question": plan.get("clarification_question"),
        "planning_and_retrieval_ms": elapsed_ms,
        "document_hit": any(chunk["source_key"] == expected_source for chunk in top_chunks),
        "candidate_evidence_hit": any(
            chunk["evidence_matches"] for candidates in candidate_lists for chunk in candidates["chunks"]
        ),
        "top_k_evidence_hit": bool(covered),
        "top_k_evidence_coverage": len(covered) / len(passages),
        "candidate_lists": candidate_lists,
        "top_chunks": top_chunks,
        "response": answer,
    }


def run_eval(*, generate_answer=True):
    cases = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8-sig"))
    if not cases:
        raise ValueError("No cases found in eval.json.")

    policy = SearchPlanningPolicy(max_search_queries=4)
    with get_connection() as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        register_vector(connection)
        documents = {
            document_id: (source_key, source_version)
            for document_id, source_key, source_version in connection.execute(
                "SELECT id, source_key, source_version FROM documents"
            ).fetchall()
        }
        results = {
            name: evaluate_retrieval(
                connection, documents, case, policy,
                generate_answer=generate_answer,
            )
            for name, case in cases.items()
        }

    return {
        "top_k": TOP_K,
        "retrieval_mode": "application",
        "case_count": len(results),
        "document_hit_rate": sum(result["document_hit"] for result in results.values()) / len(results),
        "evidence_hit_rate": sum(result["top_k_evidence_hit"] for result in results.values()) / len(results),
        "cases": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate document retrieval.")
    parser.add_argument("--retrieval-only", action="store_true",
                        help="Skip final answer generation. The query planner still runs as usual.")
    args = parser.parse_args()
    print(json.dumps(run_eval(generate_answer=not args.retrieval_only), indent=2))
