from uuid import uuid4
from datetime import datetime
from app.core.database import supabase
from app.models.bot import Bot

def generate_share_url(bot_id: str) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    return f"{timestamp}-{bot_id.replace('-', '')}"

def create_bot(data: dict) -> dict:
    bot_id = str(uuid4())
    share_id = str(uuid4())
    share_url = generate_share_url(bot_id)
    now = datetime.utcnow().isoformat()

    bot_data = {
        "id": bot_id,
        # "user_id": data["user_id"],
        "name": data["name"],
        "description": data.get("description"),
        # "icon": data.get("icon", "Bot"),
        # "icon_type": data.get("icon_type", "lucide"),
        "system_prompt": data["system_prompt"],
        "model": data.get("model", "gpt-4"),
        "temperature": data.get("temperature", 0.7),
        "max_tokens": data.get("max_tokens", 2000),
        "pdf_url": data.get("pdf_url"),
        "created_at": now,
        "updated_at": now,
        "visibility": data.get("visibility", "private"),
        "share_id": share_id,
        "share_url": share_url,
    }

    print("Bot data being inserted:", bot_data)
    try:
        response = supabase.table("bots").insert([bot_data]).execute()
        return response.data[0]
    
    except Exception as e:
            print("Error during bot insert:", e)
            raise e