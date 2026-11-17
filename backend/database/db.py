import psycopg
from pgvector.psycopg import register_vector
from pgvector import Vector
from getpass import getpass
from pathlib import Path

def get_connection():
    return psycopg.connect(host="127.0.0.1",
        port=5433,
        dbname="rag",
        user="rag",
        password=getpass("Database password: "))
    
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
    return connection.execute(
    """
    SELECT id, source_version, content_hash
    FROM documents
    WHERE source_key = %s
    """,
    (source_key,),
    ).fetchone()

def insert_document_into_db(connection, source_key, file_path, title, source_version, content_hash):
    row = connection.execute("""
                             INSERT INTO documents 
                             (source_key, file_path, title, source_version, content_hash)
                             VALUES (%s, %s, %s, %s, %s)
                             RETURNING id
                             """,
                             (source_key, file_path, title, source_version, content_hash),
                             ).fetchone()
    return row[0]

def update_document_in_db(connection, id, source_key, file_path, title, source_version, content_hash):
    row = connection.execute("""
                             UPDATE documents 
                             SET source_key = %s, file_path = %s, title = %s, source_version = %s, content_hash = %s, updated_at = now()
                             WHERE id = %s
                             RETURNING id
                             """,
                             (source_key, file_path, title, source_version, content_hash, id)
                             ).fetchone()
    if row is None:
        raise LookupError(f"Document not found: {id}")
    return row[0]

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

def insert_session_in_db(connection):
    row = connection.execute("INSERT INTO sessions DEFAULT VALUES RETURNING id").fetchone()
    return row[0]

def update_session_in_db(connection, session_id):
    connection.execute("""UPDATE sessions
                       SET end_time = now()
                       WHERE id = %s
                       """,
                       (session_id,)
                       )
    
def insert_session_message_in_db(connection, session_id, message_index, message_role, message_content):
    connection.execute("""
                       INSERT INTO session_messages (session_id, message_index, message_role, content) VALUES (%s, %s, %s, %s)
                       """,
                       (session_id, message_index, message_role, message_content))
    
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
    
if __name__ == "__main__":
    connection = init_db()
    connection.commit()