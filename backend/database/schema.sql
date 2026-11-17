CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_key TEXT NOT NULL UNIQUE,
            file_path TEXT NOT NULL UNIQUE,
            title VARCHAR(255) NOT NULL,
            source_version INTEGER NOT NULL,
            content_hash VARCHAR(255) NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

-- CREATE TABLE IF NOT EXISTS documents_metadata(
--     document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
--     metadata_key VARCHAR(255) NOT NULL,
--     metadata_value TEXT NOT NULL,
--     PRIMARY KEY (document_id, metadata_key)
-- );

CREATE TABLE IF NOT EXISTS document_chunks(
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    search_text TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED, 
    PRIMARY KEY (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS document_chunks_search_idx ON document_chunks USING GIN(search_text);
CREATE INDEX IF NOT EXISTS document_chunks_hnsw_idx ON document_chunks USING hnsw (embedding vector_cosine_ops);


CREATE TABLE IF NOT EXISTS sessions(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_time TIMESTAMPTZ 
);

CREATE TABLE IF NOT EXISTS session_messages(
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL CHECK (message_index > 0),
    message_role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, message_index)
);