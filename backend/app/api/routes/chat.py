"""Chat HTTP routes."""
from fastapi import APIRouter
from backend.app.api.schemas import ChatRequest
from backend.app.services.offers import chat_response

router = APIRouter(tags=["chat"])


@router.post("/api/ai/chat")
def api_ai_chat(req: ChatRequest):
    """Chatbot inteligente Boti House."""
    return chat_response(req.message, req.context)
