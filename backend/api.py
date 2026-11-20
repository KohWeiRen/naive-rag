from fastapi import FastAPI
from backend.schema import ChatRequest
from main import chat_and_run

app = FastAPI()

@app.post("/chat")
def receive(request: ChatRequest):
    return chat_and_run(request.query, request.session_id)