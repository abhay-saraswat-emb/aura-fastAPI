from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class Bot(BaseModel):
    id: UUID
    # user_id: UUID
    name: str
    description: Optional[str]
    # icon: str
    # icon_type: str
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    pdf_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    visibility: str
    share_id: UUID
    share_url: str
