from contextlib import ExitStack
from pathlib import Path
from backend.extractor import extract_text_from_file
from backend.ingest import calculate_file_hash, identify_document, save_document
from backend.database.db import init_db, get_document, update_session_endtime_in_db, insert_session_message_in_db, insert_session_in_db, get_session, get_session_messages
import os, json, time
from backend.helper import retrieve_val_from_env

from backend.schema import SearchPlanningPolicy
from backend.ingest import prepare_search_plan, retrieve_candidates, rank_chunks_with_rrf, load_instructions
from backend.models.driver import call_llm
from fastapi import HTTPException
from backend.misc.logger import log_chat_session, logger

max_loop = retrieve_val_from_env("LOOP_LIMIT", 5)
model = retrieve_val_from_env("OPENCODE_MODEL", "deepseek-v4.1-flash")

documents = Path(__file__).resolve().parent / "docs"
searchPlanningPolicy = SearchPlanningPolicy(max_search_queries=4)

def ingestion():
    with init_db() as connection:
        
        for root, _, files in os.walk(documents):
            for filename in files:
                file_path = Path(root) / filename
                source_key, source_version = identify_document(file_path, documents)
                curr_hash = calculate_file_hash(file_path)
                existing = get_document(connection, source_key)

                if existing is not None:
                    _, stored_version, stored_hash = existing
                    if (curr_hash == stored_hash) and (source_version == stored_version): # same hash
                        # print(f"Content of inserted document is the same as current hashed document with same version {stored_version}")
                        logger.info(f"Content of inserted document is the same as current hashed document with same version {stored_version}")
                        continue
                    
                    if int(stored_version) > int(source_version): # inserted is older version than stored (entering old documents to be stored)
                        # print(f"Document {file_path.stem} stored version {stored_version} is newer than inserted version {source_version}")
                        logger.info(f"Document {file_path.stem} stored version {stored_version} is newer than inserted version {source_version}")                        
                        continue
                    
                    if (source_version == stored_version) and (curr_hash != stored_hash): # same version number but content changed (should be same content same version)
                        # print(f"Error! Version is {stored_version} for input and stored version but content is different!")
                        logger.info(f"Error! Version is {stored_version} for input and stored version but content is different!")
                        continue
                    
                text = extract_text_from_file(file_path)
                if not text:
                    # print(f"Empty document {file_path.stem}. Nothing to insert!")
                    logger.warning(f"Empty document {file_path.stem}. Nothing to insert!")
                    continue
                save_document(connection, text, source_key, file_path, file_path.stem, source_version, curr_hash)

# if using terminal
def chat():
    with init_db() as connection, ExitStack() as log_context:
        print("Starting a new query session: ")
        session_id = insert_session_in_db(connection, user_id=None)
        log_context.enter_context(log_chat_session(session_id))
        messages = []
        message_index = 1
        clarification = ""
        while True:
            if clarification:
                print(f"Answer the following clarification question: {clarification}")
                query = input("Enter answer: ").strip()
                clarification = ""
            else:
                query = input("Enter your question or enter quit to stop: ").strip()
                
            if query.lower() == "quit":
                update_session_endtime_in_db(connection, session_id)
                connection.commit()
                print("Ending session...")
                break
                
            if not query:
                print("Query cannot be empty! Enter a valid query.") # check if the query is valid or not
                continue
            
            current_query = {"role": "user", "content": query}
            insert_session_message_in_db(connection, session_id, message_index, current_query["role"], current_query["content"])
            plan = prepare_search_plan(query=current_query, history=messages, policy=searchPlanningPolicy, session_id=session_id) # send an inference call to llm for query preparation
            messages.append(current_query)
            message_index += 1
            
            if plan["status"] == "needs_clarification":
                clarification = plan["clarification_question"].strip()
                insert_session_message_in_db(connection, session_id, message_index, "assistant", clarification)
                messages.append({"role": "assistant", "content": clarification})
                message_index += 1
                continue
            
            searches = retrieve_candidates(connection, plan, question=current_query["content"])
            chunks = rank_chunks_with_rrf([hits for _, _, hits in searches])
            
            payload = {
                "current_query" : current_query["content"],
                "history": messages[:-1],
                "sources": [{"source_id": f"S{i}", "content": chunk["content"]} for i, chunk in enumerate(chunks, start=1)]
            }
            
            # for inference
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
            insert_session_message_in_db(connection=connection, session_id=session_id, message_index=message_index, message_role="assistant", message_content=answer)
            messages.append({"role": "assistant", "content": answer})
            message_index += 1
            print(answer)
        
        update_session_endtime_in_db(connection=connection, session_id=session_id)

def chat_and_run(query: str, session_id, user_id):
    start = time.perf_counter()
    with init_db() as connection, ExitStack() as log_context:
        messages = []
        if session_id is None:
            session_id = insert_session_in_db(connection=connection, user_id=user_id)
            message_index = 1
        else:
            session = get_session(connection, session_id, user_id)
            if session is None:
                logger.error("Session ID %s with user id %s not found", session_id, user_id)
                raise HTTPException(status_code=404, detail="Session ID with User ID not found!")
            message_rows = get_session_messages(connection, session_id, user_id)
            message_index = message_rows[-1][0] + 1 if message_rows else 1 # message rows return a tuple of  (message_index, message_role, message_content) in asc order. last message has latest message index and index 0 is message index
            # reconstruct history
            for _, role, content in message_rows:
                messages.append({"role": role, "content": content})
        
        log_context.enter_context(log_chat_session(session_id))
        logger.info("Start of chat and run")
        current_query = {"role": "user", "content": query}
        insert_session_message_in_db(connection=connection, session_id=session_id, message_index=message_index, message_role=current_query["role"], message_content=query)
        message_index += 1
        plan = prepare_search_plan(session_id=session_id, query=current_query, history=messages, policy=searchPlanningPolicy)
        
        if plan["status"] == "needs_clarification":
            clarification = plan["clarification_question"].strip()
            insert_session_message_in_db(connection, session_id, message_index, "assistant", clarification)
            logger.info(f"End of chat and run due clarification. Elapsed: {time.perf_counter()-start}")
            return {"session_id": session_id, "content": clarification} # ask the clarification question
            
        searches = retrieve_candidates(connection, plan, question=current_query["content"])
        chunks = rank_chunks_with_rrf([hits for _, _, hits in searches])
        
        payload = {
            "current_query" : current_query["content"],
            "history": messages,
            "sources": [{"source_id": f"S{i}", "content": chunk["content"]} for i, chunk in enumerate(chunks, start=1)]
        }
        
        # for inference
        
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
        insert_session_message_in_db(connection=connection, session_id=session_id, message_index=message_index, message_role="assistant", message_content=answer)
        # update_session_in_db(connection=connection, session_id=session_id)
        logger.info(f"End of chat and run. Elapsed: {time.perf_counter()-start}")
        return {"session_id": session_id, "content": answer}

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
