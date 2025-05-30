import uvicorn
from fastapi import FastAPI, APIRouter, Request, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from app.api.routes import chatbot, pdf, image, tts, search, marketplace, brd_generator
import os  
from fastapi.templating import Jinja2Templates



app = FastAPI(title="Aura Chatbot API", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(pdf.router, prefix="/pdf", tags=["PDF"])
app.include_router(search.router, prefix="/search", tags=["Internet Search"])
app.include_router(marketplace.router, prefix="/market-place", tags=["Market Place"])
app.include_router(brd_generator.router, prefix="/brd-generator", tags=["BRD Generator"])


# app.include_router(tts.router, prefix="/tts", tags=["TTS"])

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/marketplace", response_class=HTMLResponse)
async def get_marketplace(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("marketplace.html", {"request": request})

@app.get("/brd-generator", response_class=HTMLResponse)
async def get_marketplace(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("brd-generator.html", {"request": request})

# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload