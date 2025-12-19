# backend.py
from typing import Optional, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import build_llm, build_embedding_model
from chatbot import attach_vector_store, run_conversation_turn, ConversationState

app = FastAPI()

# Dev: allow Vite dev server to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_embedding_model = build_embedding_model()
_vector_store = attach_vector_store()
_llm = build_llm()
_conversations: Dict[str, ConversationState] = {}


class ChatRequest(BaseModel):
    message: str
    client_type: str = "cardholder"
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    state: Optional[ConversationState] = _conversations.get(req.session_id)

    state = run_conversation_turn(
        user_input=req.message,
        llm=_llm,
        vector_store=_vector_store,
        metadata={"client_type": req.client_type},
        prev_state=state,
    )

    _conversations[req.session_id] = state
    return ChatResponse(reply=state["messages"][-1]["content"])
