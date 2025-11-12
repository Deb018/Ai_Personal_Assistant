from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

# import the ask_ai function from the services module
from services.askai import ask_ai


app = FastAPI(title="Chat UI API")

router = APIRouter(
    prefix="",
    tags=["Chat"]
)


class ChatMessage(BaseModel):
    prompt: str
    reply: str


class ChatHistory(BaseModel):
    messages: List[ChatMessage]


class AskRequest(BaseModel):
    prompt: str


# File to store chat history
CHAT_FILE = Path("chat_history.json")


def load_chat_history() -> ChatHistory:
    """Load chat history from file"""
    if CHAT_FILE.exists():
        try:
            data = json.loads(CHAT_FILE.read_text())
            return ChatHistory(messages=[ChatMessage(**msg) for msg in data])
        except Exception:
            return ChatHistory(messages=[])
    return ChatHistory(messages=[])


def save_chat_history(history: ChatHistory):
    """Save chat history to file"""
    CHAT_FILE.write_text(json.dumps([msg.dict() for msg in history.messages], indent=2))


@router.get("/chat")
async def get_chat_history():
    """Get all chat messages"""
    history = load_chat_history()
    return history


@router.post("/ask")
async def ask_endpoint(req: AskRequest):
    """Return a short assistant reply and save to chat history"""
    try:
        reply = await ask_ai(req.prompt)
        
        # Load existing history
        history = load_chat_history()
        
        # Add new message
        history.messages.append(ChatMessage(prompt=req.prompt, reply=reply))
        
        # Save updated history
        save_chat_history(history)
        
        return {"reply": reply}
    except Exception as e:
        return {"error": str(e)}


app.include_router(router)