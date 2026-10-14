from enum import Enum
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class Category(str, Enum):
    security = "security"
    architecture = "architecture"
    performance = "performance"
    style = "style"


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    agent_name: str
    severity: Severity
    category: Category
    title: str
    description: str
    line_number: int | None = None
    suggestion: str
    source_reference: str | None = None
    file_name: str | None = None


class AgentOutput(BaseModel):
    agent_name: str
    findings: list[Finding] = []
    raw_reasoning: str | None = None


class ReviewResult(BaseModel):
    session_id: str
    code_snippet_preview: str
    language: str
    findings: list[Finding] = []
    summary: str
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MultiFileReviewResult(BaseModel):
    session_id: str
    files_reviewed: list[str]
    file_reviews: dict[str, ReviewResult]
    cross_file_findings: list[Finding] = []
    summary: str
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
