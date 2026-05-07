from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.utils.security import get_current_user

from app.services.agent_service import run_agent

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None

from app.db.chat_db import save_chat, get_all_chats, get_chat_by_id
import uuid

@router.post("/chat")
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    
    try:
        # Run the Agent with the user's question and history
        result = await run_agent(request.question, request.history)
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        return {
            "answer": "I encountered an error while processing your request. Please try again or rephrase your question.",
            "error": str(e),
            "session_id": request.session_id
        }

    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        # Generate a short title from the first question
        title = request.question[:30] + "..." if len(request.question) > 30 else request.question
    else:
        # We need to preserve or fetch the title. For simplicity, if session_id is provided, 
        # we try to fetch existing chat to keep its title.
        existing_chat = get_chat_by_id(session_id, user_email=current_user)
        title = existing_chat["title"] if existing_chat else "Chat Session"
        
    save_chat(session_id, title, result["history"], user_email=current_user)

    return {
        "question": request.question,
        "answer": result["answer"],
        "tool_used": result["tool_used"],
        "history": result["history"],
        "session_id": session_id
    }

@router.get("/history")
async def get_history(current_user: str = Depends(get_current_user)):
    chats = get_all_chats(user_email=current_user)
    return {"chats": chats}

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, current_user: str = Depends(get_current_user)):
    chat = get_chat_by_id(session_id, user_email=current_user)
    if not chat:
        return {"error": "Chat not found"}
    return {"chat": chat}

@router.delete("/history/{session_id}")
async def delete_chat_session(session_id: str, current_user: str = Depends(get_current_user)):
    from app.db.chat_db import delete_chat
    success = delete_chat(session_id, user_email=current_user)
    if not success:
        return {"error": "Failed to delete chat or chat not found"}, 404
    return {"message": "Chat deleted successfully", "session_id": session_id}