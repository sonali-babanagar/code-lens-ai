from abc import ABC, abstractmethod
from src.schemas.session import Session
from src.schemas.review import ReviewResult, Finding
from src.schemas.chat import ChatMessage


class BaseSessionStore(ABC):
    @abstractmethod
    async def create_session(self, session_id: str) -> Session: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def save_review(self, session_id: str, review: ReviewResult) -> None: ...

    @abstractmethod
    async def get_review(self, session_id: str) -> ReviewResult | None: ...

    @abstractmethod
    async def save_findings(self, session_id: str, findings: list[Finding]) -> None: ...

    @abstractmethod
    async def get_findings(self, session_id: str) -> list[Finding]: ...

    @abstractmethod
    async def add_chat_message(self, session_id: str, message: ChatMessage) -> None: ...

    @abstractmethod
    async def get_chat_history(self, session_id: str) -> list[ChatMessage]: ...

    @abstractmethod
    async def list_sessions(self) -> list[Session]: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...
