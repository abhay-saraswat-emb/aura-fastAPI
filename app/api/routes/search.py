from fastapi import APIRouter, Query
from app.services.search_service import claude_perform_search, gemini_perform_search, gpt_perform_search
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, ClassVar


router = APIRouter()

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    model: str
    prompt: str
    system_prompt: Optional[str] = "You are a helpful assistant."
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    conversation_history: List[Message] = []


@router.post("/")
async def search_web(request: ChatRequest):
    """
    Endpoint for chatbot interaction that returns a streaming response
    when using Claude model, or a regular JSON response for other models.
    """

    conversation_history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]

    if request.model == "Claude":
        # Return a streaming response for Claude
        return StreamingResponse(
            claude_perform_search(
                request.prompt, 
                request.system_prompt, 
                request.max_tokens, 
                request.temperature,
                conversation_history
            ),
            media_type="text/plain"
        )
    elif request.model == "Gemini":
        # Return a streaming response for Gemini
        return StreamingResponse(
            gemini_perform_search(
                request.prompt, 
                request.system_prompt, 
                request.max_tokens, 
                request.temperature,
                conversation_history
            ),
            media_type="text/plain" 
        )
    elif request.model == "GPT":
        # Return a streaming response for GPT
        return StreamingResponse(
            gpt_perform_search(
                request.prompt, 
                request.system_prompt, 
                request.max_tokens, 
                request.temperature,
                conversation_history
            ),
            media_type="text/plain" 
        )
