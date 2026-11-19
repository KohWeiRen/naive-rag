import hashlib
from pathlib import Path
import re, json, time
from pgvector import Vector
from backend.database.db import (
    replace_document_and_chunks,
    search_by_keyword,
    search_by_vector,
)
from backend.embedder import embed, chunker, tokenize, get_embedder_model_max_seg_length
from backend.helper import retrieve_val_from_env
from backend.schema import SearchPlanningPolicy
from backend.extractor import extract_text_from_md_and_txt
from backend import schema
from backend.models.driver import call_llm

############################ variables ###############################
model = retrieve_val_from_env("OPENCODE_MODEL", "deepseek-v4.1-flash")
tasklist = { 
            "query_processing": "query_processing.md",
            "query_answering": "query_answering.md"
            }
root = Path(__file__).resolve().parent
prompts = root / "prompts"
############################ variables ###############################

def load_instructions(task : str) -> str:
    if task not in tasklist:
        raise ValueError(f"Unknown task: {task}")
    
    instructions = extract_text_from_md_and_txt(prompts/ tasklist[task])
    
    if not instructions:
        raise ValueError(f"Empty instructions for task {task}")
    
    return instructions

def calculate_file_hash(path : Path)-> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def identify_document(path : Path, documents_root: Path):
    match = re.fullmatch(
        r"(.+)_v([1-9][0-9]*)",
        path.stem,
        flags=re.IGNORECASE
    )
    
    if match is None:
        raise ValueError(f"Missing version suffix: {path.name}")
    
    base_name, version = match.groups()
    
    relative_path = path.relative_to(documents_root)
    source_key = relative_path.with_name(
        base_name + path.suffix
    ).as_posix()
    
    return source_key, int(version)

def save_document(connection, text, source_key, file_path, title, source_version, content_hash):
    chunks = chunker(text)
    if not chunks:
        print(f"No indexable text in {file_path.name}. Skipping.")
        return
    embeddings = embed(chunks)
    prepared_chunks = [
        (content, Vector(embedding))
        for content, embedding in zip(chunks, embeddings, strict=True)
    ]

    document_id = replace_document_and_chunks(
        connection,
        source_key=source_key,
        file_path=str(file_path),
        title=title,
        source_version=source_version,
        content_hash=content_hash,
        chunks=prepared_chunks,
    )
    if document_id is None:
        print(f"Skipping {file_path.name}: this version or a newer one is already indexed.")
    return document_id
        
def prepare_search_plan(session_id, query, history : list[dict] = [], policy: SearchPlanningPolicy = SearchPlanningPolicy):
    def calculate_elapsed_time(start, end, text):
        print(f"Elapsed: {end - start} for {text}")
        
    function_start = time.perf_counter()
    task = "query_processing"
    
    limit = get_embedder_model_max_seg_length()
    
    def count_tokens(text):
        token_cnt, _ = tokenize(text, add_special_tokens=True, truncation=False)
        return token_cnt
    
    # assume with history we always need a rewrite even if its within token limit as some question require historical context to be rewritten
    if count_tokens(query["content"]) <= limit and not history: 
        search_texts = [query["content"]]
    else:
        
        instructions = {"role": "system", "content": load_instructions(task)}
        
        payload = {
            "current_query" : query["content"],
            "history": history,
            "token_limit": limit,
            "max_search_queries": policy.max_search_queries
        }
        
        # for decomposition and rewriting
        inference_start = time.perf_counter()
        response = call_llm(
            messages=[
                {
                    "role" : "system", "content" : load_instructions(task=task)
                },
                {
                    "role" : "user", "content" : json.dumps(payload)
                }
            ], # insert instruction, current query, past history and limits
            max_output_tokens=policy.max_token_output,
            session_id=session_id
        )
        calculate_elapsed_time(inference_start, time.perf_counter(), "Inference")
        
        if not isinstance(response, dict):
            raise ValueError("Error! LLM returned invalid output!")
        
        content = json.loads(response["content"])
        
        if not isinstance(content, dict):
            raise ValueError("Planner output must be a json object!")
        
        clarification = content.get("clarification_question", "") # llm has some clarifications to make
        if clarification:
            calculate_elapsed_time(function_start, time.perf_counter(), "Clarification")
            return {"status": "needs_clarification", "search_text": [], "vectors": [], "clarification_question": clarification}
        
        rewritten = content.get("rewritten_query", "").strip()
        decomposed = content.get("decomposed_queries", [])
        if not rewritten and not decomposed:
            raise ValueError("Query was not rewritten OR decomposed!")
        
        decomposed = list(dict.fromkeys(text.strip() for text in decomposed))
        combined = list(dict.fromkeys(text.strip() for text in [rewritten, *decomposed]))
        
        token_counts = {text: count_tokens(text) for text in combined}
        
        def fits(queries):
            return( 0 < len(queries) <= policy.max_search_queries and
                   all(text and token_counts[text] <= limit for text in queries))
        
        if fits(combined):
            search_texts = combined
        elif fits(decomposed):
            search_texts = decomposed
        elif fits([rewritten]):
            search_texts = [rewritten]
        else:
            calculate_elapsed_time(function_start, time.perf_counter(), "Clarification")
            return {"status": "needs_clarification", "search_text": [], "vectors": [], "clarification_question": "Could you narrow your request to one or two specific questions?"}
    
    vectors = embed(search_texts)
    calculate_elapsed_time(function_start, time.perf_counter(), "function end")
    return {"status": "ready", "search_text": search_texts, "vectors": vectors, "clarification_question": None}

def retrieve_candidates(connection, search_dict: dict, limit=20):
    ranked_list = []
    if not isinstance(search_dict, dict):
        print("Empty dictionary! Returning empty list...")
        return ranked_list
    
    search_texts = search_dict.get("search_text")
    search_vectors = search_dict.get("vectors")
    
    with connection.transaction():
        for text, vector in zip(search_texts, search_vectors, strict=True):
            ranked_list.append(search_by_keyword(connection, text, limit=limit))
            ranked_list.append(search_by_vector(connection, vector, limit=limit))
        
    return ranked_list
    
def rank_chunks_with_rrf(ranked_list, k=60, top=8):
    
    rrf_scores = {}
    for hits in ranked_list:
        for rank, (document_id, chunk_index, content) in enumerate(hits, start=1):
            key = (document_id, chunk_index)
            
            if key not in rrf_scores:
                rrf_scores[key] = {
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "content": content,
                    "rrf_score": 0.0,
                }

            rrf_scores[key]["rrf_score"] += 1 / (k + rank)
            
    return sorted(rrf_scores.values(), key=lambda item: item["rrf_score"], reverse=True)[:top]
