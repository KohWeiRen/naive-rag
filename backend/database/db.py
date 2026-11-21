import psycopg
from pgvector.psycopg import register_vector
from pgvector import Vector
from getpass import getpass
from pathlib import Path
from backend.helper import retrieve_val_from_env

def get_connection():
    database_url = retrieve_val_from_env("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("Set DATABASE_URL before starting the app!")
    return psycopg.connect(database_url, connect_timeout=5)
    
def init_db():
    connection = get_connection()
    try:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        connection.execute(schema)
        register_vector(connection)
        connection.commit()
        return connection
    except Exception:
        connection.close()
        raise
    
def get_document(connection, source_key : str):
    with connection.transaction():
        return connection.execute(
            """
            SELECT id, source_version, content_hash
            FROM documents
            WHERE source_key = %s
            """,
            (source_key,),
        ).fetchone()

def get_session(connection, session_id):
    with connection.transaction():
        return connection.execute("""
                                  SELECT id, user_id 
                                  FROM sessions
                                  WHERE id = %s
                                  """,
                                  (session_id,)).fetchone()

def get_session_messages(connection, session_id):
    with connection.transaction():
        return connection.execute("""
                                  SELECT message_index, message_role, content
                                  FROM session_messages
                                  WHERE session_id = %s
                                  ORDER BY created_at ASC
                                  """,
                                  (session_id,)).fetchall()

def upsert_document_in_db(connection, source_key, file_path, title, source_version, content_hash):
    """Return the document ID when a new or newer version is saved."""
    row = connection.execute("""
                             INSERT INTO documents
                             (source_key, file_path, title, source_version, content_hash)
                             VALUES (%s, %s, %s, %s, %s)
                             ON CONFLICT (source_key) DO UPDATE SET
                                 file_path = EXCLUDED.file_path,
                                 title = EXCLUDED.title,
                                 source_version = EXCLUDED.source_version,
                                 content_hash = EXCLUDED.content_hash,
                                 updated_at = now()
                             WHERE documents.source_version < EXCLUDED.source_version
                             RETURNING id
                             """,
                             (source_key, file_path, title, source_version, content_hash),
                             ).fetchone()
    return row[0] if row is not None else None

def delete_chunks_in_db(connection, document_id):
    connection.execute("""
                       DELETE FROM document_chunks WHERE document_id = %s 
                       """,
                       (document_id,))

def insert_chunk_in_db(connection, document_id, chunk_index, content, embedding):
    connection.execute("""
                       INSERT INTO document_chunks (document_id, chunk_index, content, embedding) 
                       VALUES (%s, %s, %s, %s)
                       """,
                       (document_id, chunk_index, content, embedding))

def replace_document_and_chunks(
    connection, *, source_key, file_path, title, source_version, content_hash, chunks
):
    """Save the document and its prepared chunks together. Return its ID, or None if skipped."""
    if not chunks:
        raise ValueError("A document replacement requires at least one chunk")

    with connection.transaction():
        document_id = upsert_document_in_db(
            connection, source_key, file_path, title, source_version, content_hash
        )
        if document_id is None:
            return None

        delete_chunks_in_db(connection, document_id)
        for chunk_index, (content, embedding) in enumerate(chunks, start=1):
            insert_chunk_in_db(connection, document_id, chunk_index, content, embedding)

    return document_id

def insert_session_in_db(connection):
    row = connection.execute("""
                             INSERT INTO sessions DEFAULT VALUES 
                             RETURNING id
                             """).fetchone()
    connection.commit()
    return row[0]

def update_session_endtime_in_db(connection, session_id):
    connection.execute("""UPDATE sessions
                       SET end_time = now()
                       WHERE id = %s
                       """,
                       (session_id,)
                       )
    connection.commit()
    
def update_session_userid_in_db(user_id, google_sub):
    with get_connection() as connection:
        return connection.execute("""UPDATE sessions
                        SET end_time = %s
                        WHERE google_sub = %s
                        """,
                        (user_id, google_sub)
                        ).fetchone()
    
def insert_session_message_in_db(connection, session_id, message_index, message_role, message_content):
    connection.execute("""
                       INSERT INTO session_messages (session_id, message_index, message_role, content) VALUES (%s, %s, %s, %s)
                       """,
                       (session_id, message_index, message_role, message_content))
    connection.commit()
    
def search_by_vector(connection, query_vector, limit=20):
    return connection.execute("""
                              SELECT document_id, chunk_index, content
                              FROM document_chunks
                              ORDER BY embedding <=> %s
                              LIMIT %s
                              """,
                              (Vector(query_vector), limit)
                              ).fetchall()
    
def search_by_keyword(connection, query, limit=20):
    return connection.execute("""
                              SELECT document_id, chunk_index, content
                              FROM document_chunks
                              WHERE search_text @@ websearch_to_tsquery('english', %s)
                              ORDER BY ts_rank_cd(
                                  search_text,
                                  websearch_to_tsquery('english', %s)
                              ) DESC
                              LIMIT %s
                              """,
                              (query, query, limit)).fetchall()

def get_or_create_google_user(google_sub:str):
    with get_connection() as connection:
        row = connection.execute("""
                                 INSERT INTO users (google_sub)
                                 VALUES (%s)
                                 ON CONFLICT (google_sub)
                                 DO UPDATE SET google_sub = EXCLUDED.google_sub
                                 RETURNING id
                                 """,
                                 (google_sub,)
                                ).fetchone()
    return row[0] 



def migrate_sessions(connection):
    with connection.transaction():
        connection.execute("""
                           ALTER TABLE sessions
                           ADD CONSTRAINTS session_user_id_fkey
                           FOREIGN KEY (user_id) REFERENCES users(id)
                           """)

if __name__ == "__main__":
    with init_db() as connection:
        migrate_sessions(connection=connection)
