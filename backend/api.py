from fastapi import FastAPI, HTTPException, Request
from backend.schema import ChatRequest
from main import chat_and_run
from pathlib import Path
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from backend.auth import router as auth_router
from backend.helper import retrieve_val_from_env
from uuid import UUID
from backend.database.db import get_connection, get_session, get_session_messages, get_user_sessions

app = FastAPI()
session_secret = retrieve_val_from_env("SESSION_SECRET", "")
if not session_secret:
    raise RuntimeError("Set SESSION_SECRET in backend/.env")

app.add_middleware(SessionMiddleware, secret_key=session_secret)
app.include_router(auth_router)

project_root = Path(__file__).resolve().parents[1]

def require_user_id(request: Request) -> UUID:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(401, "Sign in first.")
    return UUID(user_id)

@app.post("/chat")
def receive(payload: ChatRequest, request: Request):
    return chat_and_run(payload.query, payload.session_id, user_id=require_user_id(request))

@app.get("/chats")
def list_chats(request: Request):
    user_id = require_user_id(request)
    with get_connection() as connection:
        sessions = get_user_sessions(connection, user_id)
    return [{"session_id": session_id, "title": title} for session_id, title in sessions]

@app.get("/chat/{session_id}/messages")
def get_chat_messages(session_id: UUID, request: Request):
    user_id = require_user_id(request)
    with get_connection() as connection:
        if get_session(connection, session_id, user_id) is None:
            raise HTTPException(404, "Chat not found.")
        messages = get_session_messages(connection, session_id, user_id)
    return [{"role": role, "content": content} for _, role, content in messages]

@app.get("/")
def chat_page():
    return FileResponse(project_root/"frontend"/"chat.html")

@app.get("/script.js")
def chat_script():
    return FileResponse(project_root/"frontend"/"script.js")
