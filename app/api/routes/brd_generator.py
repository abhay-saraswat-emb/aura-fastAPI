from app.schemas.bot import CreateBotRequest
from app.services import bot_services
from app.core.database import supabase
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, Request, APIRouter
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, Field
import httpx
import base64
import os
import anthropic
from typing import Dict, Any, Optional, List
import uuid
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from app.services.brd_service import brd_generator

router = APIRouter()


load_dotenv()

# Claude client
claude_client = anthropic.Anthropic()

# Environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-3-7-sonnet-20250219"
MAX_TOKENS = 128000


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    conversation_history: List[Message] = []


@router.post("/brd")
async def brd(request: ChatRequest):
    """Generate BRD with Claude"""

    conversation_history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]

    return StreamingResponse(
            brd_generator(
                request.max_tokens, 
                request.temperature,
                conversation_history
            ),
            media_type="text/plain"
        )
