from typing import TypedDict
from src.schemas.review import AgentOutput, ReviewResult
from src.schemas.chat import ChatMessage


class GraphState(TypedDict, total=False):
    code: str
    language: str
    file_name: str | None
    code_analysis: dict
    security_findings: AgentOutput | None
    architecture_findings: AgentOutput | None
    performance_findings: AgentOutput | None
    final_review: ReviewResult | None
    chat_history: list[ChatMessage]
    session_id: str
