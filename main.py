from pathlib import Path
from backend.extractor import extract_text_from_file
from backend.ingest import calculate_file_hash, identify_document, update_document, insert_document
from backend.database.db import init_db, get_document, update_session_in_db, insert_session_message_in_db, insert_session_in_db
import os, sys
from backend.helper import retrieve_val_from_env

max_loop = retrieve_val_from_env("LOOP_LIMIT", 5)

documents = Path(__file__).resolve().parent / "ternwell-docs"

def ingestion():
    with init_db() as connection:
        
        for root, _, files in os.walk(documents):
            for filename in files:
                file_path = Path(root) / filename
                source_key, source_version = identify_document(file_path, documents)
                curr_hash = calculate_file_hash(file_path)
                existing = get_document(connection, source_key)
                
                if existing is None:
                    text = extract_text_from_file(file_path)
                    if text is None or text == "":
                        print(f"Empty document {file_path.stem}. Nothing to insert!")
                        continue
                    insert_document(connection, text, source_key, file_path, file_path.stem, source_version, curr_hash)
                else:
                    document_id, stored_version, stored_hash = existing
                    if (curr_hash == stored_hash) and (source_version == stored_version): # same hash
                        print(f"Content of inserted document is the same as current hashed document with same version {stored_version}")
                        continue
                    
                    if int(stored_version) > int(source_version): # inserted is older version than stored (entering old documents to be stored)
                        print(f"Document {file_path.stem} stored version {stored_version} is newer than inserted version {source_version}")
                        continue
                    
                    if (source_version == stored_version) and (curr_hash != stored_hash): # same version number but content changed (should be same content same version)
                        print(f"Error! Version is {stored_version} for input and stored version but content is different!")
                        continue
                    
                    if int(stored_version) < int(source_version): # if newer version is in, update document
                        text = extract_text_from_file(file_path)
                        if text is None or text == "":
                            print(f"Empty document {file_path.stem}. Nothing to insert!")
                            continue
                        update_document(connection, text, document_id, source_key, file_path, file_path.stem, source_version, curr_hash)


def chat():
    with init_db() as connection:
        print("Starting a new query session: ")
        session_id = insert_session_in_db(connection)
        message = []
        message_index = 1
        while True:
            query = input("Enter your question or enter quit to stop: ").strip()
            if query.lower() == "quit":
                update_session_in_db(connection, session_id)
                connection.commit()
                print("Ending session...")
                break
        
            for _ in range(max_loop):
                message.append({"role": "user", "content": query})
                insert_session_message_in_db(connection, session_id, message_index, message[-1]["role"], message[-1]["content"])
                message_index += 1
            
            
                # process query (need processing? need decompose? need rewrite?)
                
                # send to llm and receive input
                
                # receive input - need to structure. need be able to let it do tools calling. so need to tell it what function is available and 
                # how to call it
                
                # parse llm output. check if tools call
                
                # determine if continue? count tokens == token_limit
                
                # present answer if done
                
                # exit loop to get next question
        

def main():
    while True:
        command = input("Enter chat, ingest or quit: ").strip().lower()
        if command == "ingest":
            ingestion()
        elif command == "chat":
            chat()
        elif command == "quit":
            print("Thank you and see you again! Quitting...")
            return
        else:
            print(f"Invalid command, only enter chat, injest or quit!")
        
if __name__ == "__main__":
    main()