from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID

class CreateBotRequest(BaseModel):
    # user_id: UUID
    name: str
    description: Optional[str]
    # icon: Optional[str] = "Bot"
    # icon_type: Optional[str] = "lucide"
    system_prompt: str
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    pdf_url: Optional[str]
    visibility: Literal["private", "public", "link"] = "private"
