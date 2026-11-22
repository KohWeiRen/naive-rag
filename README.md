# Document RAG Chatbot

An authenticated web chatbot that answers questions over 100 synthetic company documents. It retrieves supporting passages, includes source citations in the answer, and saves chat history for each signed-in user. The retrieval pipeline is implemented in Python without a RAG orchestration framework.

## Implementation

1. **Ingest and index.** Python extracts text from PDF, HTML, JSON, Markdown, and plain-text files. A tokenizer splits the text into overlapping chunks, and Sentence Transformers generates embeddings with `all-MiniLM-L6-v2`. PostgreSQL stores the original document reference, version, content hash, chunk text, and vector. Newer document versions replace their previous chunks in a single transaction.
2. **Plan and retrieve.** A standalone question that fits the embedding model’s input limit is embedded directly. Follow-ups and longer queries go through a planner that can rewrite the question, break it into focused searches, or ask for clarification. General retrieval combines PostgreSQL full-text search with pgvector cosine search using reciprocal rank fusion (RRF). The schema has a GIN index for full-text search and an HNSW index for cosine search.
3. **Generate an answer.** The application sends the current question, conversation history, and up to eight ranked chunks to the answer model. The prompt labels each chunk and asks the model to ground factual claims in the retrieved text and cite its sources.
4. **Serve and persist chat.** FastAPI serves the HTML, CSS, and JavaScript interface. Authlib handles Google sign-in through OpenID Connect. PostgreSQL stores each user’s conversations and messages, and the API checks session ownership before returning chat history.

## Retrieval evaluation

The [evaluation set](eval/eval.json) pairs questions with an expected source document and labeled supporting passages. The [runner](eval/eval.py) records each candidate list, the final ranked chunks, evidence coverage, and planning and retrieval latency. A hit means at least one labeled passage appears in the final eight chunks.

| Retrieval configuration | Standalone questions with evidence in the top eight |
| --- | ---: |
| Baseline hybrid search | 14 of 22 (64%) |
| Exact document ID lookup and keyword fallback | 22 of 22 (100%) |

The baseline and improved runs use the same standalone questions and evidence labels. The figures measure passage retrieval on this curated set. Final-answer correctness is a separate metric.

### What changed

The question `What is ENG-016 about?` originally returned zero keyword candidates and missed the expected evidence in the final shortlist. The chunker had decoded `ENG-016` as `eng - 016`, so PostgreSQL indexed `eng` and `016`. The original full-text query searched for `eng` followed by `-016`.

The shared retriever now recognizes `ENG-016`, `ENG 016`, and `ENG016` in the original question. It resolves the code against indexed filenames, then ranks chunks from matching documents by vector similarity. When no matching chunks are available, the retriever uses hybrid search. If keyword search returns no hits for a hyphenated phrase such as `fourth-quarter`, it can retry with `fourth quarter` while preserving numeric ranges such as `1-2`. A successful exact-ID lookup limits retrieval to the named documents, so a related document mentioned only by topic can be missed.

With the database populated and the app configuration set, run the retrieval eval from the repo root:

```powershell
py -m eval.eval --retrieval-only
```

This skips final answer generation. Cases with conversation history can still call the query planner.

## Run locally

1. Create and activate a Python virtual environment, then install dependencies with `python -m pip install -r requirements.txt`.
2. Copy `backend/.env.example` to `backend/.env`. Generate a database password and a separate session signing secret by running `python -c "import secrets; print(secrets.token_urlsafe(32))"` twice. Enter the database password in both `POSTGRES_PASSWORD` and `DATABASE_URL`, and set `SESSION_SECRET` to the other value. For an existing PostgreSQL volume, use the password already configured in that database.
3. Set your Google OAuth client credentials and register `http://127.0.0.1:8000/auth/callback` as the authorized redirect URI. Add your OpenCode API key. The app sends questions and retrieved passages to OpenCode for inference.
4. With Docker running, run the commands below from the repository root. When `main.py` prompts, select `ingest`, then `quit` when ingestion finishes. Once Uvicorn starts, open `http://127.0.0.1:8000`.

```powershell
docker compose --env-file ./backend/.env -f ./backend/compose.yml up -d --wait
python main.py
python -m uvicorn backend.api:app --no-access-log
```

`--no-access-log` keeps OAuth callback URLs out of Uvicorn’s access logs. For an HTTPS deployment, set `SESSION_COOKIE_SECURE=true` and register that deployment’s callback URL with Google. Store real environment files, chat data, logs, and raw evaluation reports locally.

## Technology stack

| Layer | Technology |
| --- | --- |
| Application and web API | Python, FastAPI, Pydantic, Uvicorn |
| Browser interface and sign-in | HTML, CSS, JavaScript, Google OpenID Connect, Authlib, Starlette sessions |
| Ingestion and embeddings | pypdf, Beautiful Soup, Sentence Transformers, MiniLM |
| Storage and retrieval | PostgreSQL 17, pgvector, Psycopg 3, Docker Compose |
| Model integration | OpenCode API via the OpenAI Python SDK |
