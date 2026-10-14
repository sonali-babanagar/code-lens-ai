from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str | None = None
    code_snippet_preview: str | None = None
    status: str = "created"  # created, reviewed, chatting
