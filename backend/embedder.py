from sentence_transformers import SentenceTransformer
from helper import retrieve_val_from_env

model=retrieve_val_from_env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
driver=retrieve_val_from_env("DRIVER", "cpu")

embedding_model = SentenceTransformer(model, device=driver)

def embed(chunks : list[str]):
    return embedding_model.encode(chunks, normalize_embeddings=True)

def chunker(text: str, max_tokens: int = 200, overlap: int = 50) -> list[str]:
    if not 0 <= overlap < max_tokens:
        raise ValueError("Require 0 <= overlap < max_tokens")
    
    tokenizer = embedding_model.tokenizer
    token_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    chunks = []
    step = max_tokens - overlap
    for start in range(0, len(token_ids), step):
        end = start + max_tokens
        content = tokenizer.decode(token_ids[start:end],
                                   skip_special_tokens=True)
        chunks.append(content)
        
        if end >= len(token_ids):
            break
        
    return chunks

def tokenize(text: str, add_special_tokens: bool = False, truncation: bool = False):
    tokenizer = embedding_model.tokenizer
    token_ids = tokenizer.encode(text, add_special_tokens=add_special_tokens, truncation=truncation)
    return (len(token_ids), token_ids)

def get_embedder_model_max_seg_length():
    return model.max_seq_length