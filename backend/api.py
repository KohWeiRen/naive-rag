from fastapi import FastAPI
from backend.schema import ChatRequest
from main import chat_and_run
from pathlib import Path
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from backend.auth import router as auth_router
from backend.helper import retrieve_val_from_env

app = FastAPI()
session_secret = retrieve_val_from_env("SESSION_SECRET", "")
if not session_secret:
    raise RuntimeError("Set SESSION_SECRET in backend/.env")

app.add_middleware(SessionMiddleware, secret_key=session_secret)
app.include_router(auth_router)

project_root = Path(__file__).resolve().parents[1]

@app.post("/chat")
def receive(request: ChatRequest):
    return chat_and_run(request.query, request.session_id)

@app.get("/")
def chat_page():
    return FileResponse(project_root/"frontend"/"chat.html")

@app.get("/script.js")
def chat_script():
    return FileResponse(project_root/"frontend"/"script.js")