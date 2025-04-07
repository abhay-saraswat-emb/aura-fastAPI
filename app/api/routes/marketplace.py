from fastapi import APIRouter, HTTPException, Query
from app.schemas.bot import CreateBotRequest
from app.services import bot_services
from app.core.database import supabase

router = APIRouter()

@router.post("/bots")
def create_bot(req: CreateBotRequest):
    return bot_services.create_bot(req.dict())

@router.get("/bots")
def get_user_bots(user_id: str = Query(...)):
    res = supabase.table("bots").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data

@router.get("/bots/public")
def get_public_bots():
    res = supabase.table("bots").select("*").eq("visibility", "public").order("created_at", desc=True).execute()
    return res.data

@router.get("/bots/share/{share_url}")
def get_shared_bot(share_url: str):
    res = supabase.table("bots").select("*").eq("share_url", share_url).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Bot not found")
    return res.data[0]
