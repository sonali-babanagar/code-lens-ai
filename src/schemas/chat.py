from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
