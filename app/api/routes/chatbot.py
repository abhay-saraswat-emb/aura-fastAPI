from fastapi import APIRouter, Depends, Request, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Union, AsyncGenerator
from app.services.ai_service import claude_client
import os
import anthropic
from typing import List, Dict, Optional, ClassVar
from app.services.ai_service import claude_stream_response, genai_stream_response, openai_stream_response
from app.services.pdf_service import pdf_claude_stream_response, pdf_genai_stream_response, pdf_openai_stream_response
from app.services.image_service import image_claude_stream_response, image_genai_stream_response, image_openai_stream_response

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
    pdf_url: Optional[str] = None

@router.post("/")
async def chatbot_interaction(request: ChatRequest):
    """
    Endpoint for chatbot interaction that returns a streaming response
    when using Claude model, or a regular JSON response for other models.
    """

    conversation_history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]

    if request.model == "Claude":
        # Return a streaming response for Claude
        return StreamingResponse(
            claude_stream_response(
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
            genai_stream_response(
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
            openai_stream_response(
                request.prompt, 
                request.system_prompt, 
                request.max_tokens, 
                request.temperature,
                conversation_history
            ),
            media_type="text/plain" 
        )

@router.post("/file-chat/")
async def query_pdf(request: ChatRequest):
    """
    Endpoint for chatbot interaction that returns a streaming response.
    Supports both PDF and image-based input based on URL extension.
    """
    conversation_history = [
        {"role": msg.role, "content": msg.content} for msg in request.conversation_history
    ]

    # Determine file type from URL extension
    file_ext = os.path.splitext(request.pdf_url or "")[1].lower()

    is_image = file_ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
    is_pdf = file_ext == ".pdf"

    if not request.pdf_url or (not is_image and not is_pdf):
        return StreamingResponse(
            iter(["data: Error: Unsupported or missing file type.\n\n"]),
            media_type="text/plain"
        )

    if is_image:
        if request.model == "Claude":
            return StreamingResponse(
                image_claude_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    image_url=request.pdf_url
                ),
                media_type="text/plain"
            )
        elif request.model == "Gemini":
            return StreamingResponse(
                image_genai_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    image_url=request.pdf_url
                ),
                media_type="text/plain"
            )
        elif request.model == "GPT":
            return StreamingResponse(
                image_openai_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    image_url=request.pdf_url
                ),
                media_type="text/plain"
            )

    if is_pdf:
        if request.model == "Claude":
            return StreamingResponse(
                pdf_claude_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    pdf_url=request.pdf_url
                ),
                media_type="text/plain"
            )
        elif request.model == "Gemini":
            return StreamingResponse(
                pdf_genai_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    pdf_url=request.pdf_url
                ),
                media_type="text/plain"
            )
        elif request.model == "GPT":
            return StreamingResponse(
                pdf_openai_stream_response(
                    request.prompt,
                    request.system_prompt,
                    request.max_tokens,
                    request.temperature,
                    conversation_history,
                    pdf_url=request.pdf_url
                ),
                media_type="text/plain"
            )
