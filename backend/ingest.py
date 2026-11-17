import hashlib
from pathlib import Path
import re
from pgvector import Vector
from backend.database.db import (update_document_in_db, delete_chunks_in_db, insert_chunk_in_db, insert_document_into_db, search_by_keyword, search_by_vector)
from backend.embedder import embed, chunker, tokenize, get_embedder_model_max_seg_length
from helper import retrieve_val_from_env
from backend.schema import SearchPlanningPolicy

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

def update_document(connection, text : str, document_id, source_key, file_path, title, source_version, content_hash):
    chunks = chunker(text)
    embeddings = embed(chunks)
    update_document_in_db(connection, document_id, source_key, str(file_path), title, source_version, content_hash)
    delete_chunks_in_db(connection, document_id)
    for chunk_index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True), start = 1):
        insert_chunk_in_db(connection, document_id, chunk_index, content, Vector(embedding))
        
def insert_document(connection, text, source_key, file_path, title, source_version, content_hash):
    id = insert_document_into_db(connection, source_key, str(file_path), title, source_version, content_hash)
    chunks = chunker(text)
    embeddings = embed(chunks)
    for chunk_index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True), start = 1):
        insert_chunk_in_db(connection, id, chunk_index, content, Vector(embedding))
        
def prepare_search_plan(query: str, history=None, planner=None, policy: SearchPlanningPolicy = SearchPlanningPolicy):
    query = query.strip()
    
    if not query:
        print("Error! Query cannot be empty!")
        return "Failed"
    
    limit = get_embedder_model_max_seg_length()
    
    token_cnt, _ = tokenize(query + ",".join(history))
    
    if token_cnt <= limit:
        search_text = [query + ",".join(history)]
    else:
        if planner is None:
            print("Error! Planner cannot be empty!")
            return "Failed"
        
        search_text = planner(
            query=query,
            history=history or [],
            max_queries=SearchPlanningPolicy.max_planner_calls,
            token_limit=
            # more input to tell the what prompt to use
        )

def retrieve_candidates():
    pass

def process_query(query: str, planner=None, history=None, force_plan=False, max_queries=4):
    query = query.strip()
    
    if not query:
        raise ValueError("Empty query!")
    
    limit = get_embedder_model_max_seg_length()
    
    def count_tokens(text):
        token_cnt, _ = tokenize(text, add_special_tokens=True, truncation=False)
        return token_cnt
    
    if count_tokens() <= limit and not force_plan: # question within embedder limits (easiest and fastest)
        search_text = [query]
    else:
        if planner is None: 
            raise ValueError("A query planner is requied for this request")
        
        search_texts = planner(
            query=query,
            history=history or [],
            token_limit=limit,
            max_queries=max_queries,
        )
        
    if not isinstance(search_texts, list) or not search_texts:
        raise ValueError("Planner must return a non-empty list of strings")
    
    if any(not isinstance(text, str) or 
           not text.strip() for text in search_texts):
        raise ValueError("Each search query must be a non-empty string")
    
    search_texts = list(dict.fromkeys(text.strip() for text in search_text))
    
    if len(search_text) > max_queries:
        raise ValueError("Too many search queries; narrow the request")
    
    for text in search_text:
        if count_tokens(text) > limit:
            raise ValueError("A prepared query still exceeds the embedding limit")
        
    vectors = embed(search_text)
    
    return list(zip(search_texts, vectors, strict=True))
    
def compute_rrf(top_keyword_results, top_embedding_results, k=60, top=8):
    
    rrf_scores = {}
    for hits in (top_keyword_results, top_embedding_results):
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