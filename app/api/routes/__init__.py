from fastapi import APIRouter
from . import chatbot, marketplace

router = APIRouter()
router.include_router(chatbot.router)
router.include_router(marketplace.router) 
