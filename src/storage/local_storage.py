import json
import os
import shutil
from src.config import settings
from src.storage.base import BaseSessionStore
from src.schemas.session import Session
from src.schemas.review import ReviewResult, Finding
from src.schemas.chat import ChatMessage

SESSIONS_DIR = os.path.join(settings.MEDIA_DIR, "sessions")


class LocalSessionStore(BaseSessionStore):
    def _session_dir(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, session_id)

    def _ensure_dir(self, session_id: str) -> str:
        path = self._session_dir(session_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _write_json(self, filepath: str, data: dict | list) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_json(self, filepath: str) -> dict | list | None:
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    async def create_session(self, session_id: str) -> Session:
        session = Session(session_id=session_id)
        path = self._ensure_dir(session_id)
        self._write_json(os.path.join(path, "session.json"), session.model_dump())
        return session

    async def get_session(self, session_id: str) -> Session | None:
        data = self._read_json(os.path.join(self._session_dir(session_id), "session.json"))
        if data is None:
            return None
        return Session(**data)

    async def save_review(self, session_id: str, review: ReviewResult) -> None:
        path = self._ensure_dir(session_id)
        self._write_json(os.path.join(path, "review.json"), review.model_dump())
        # also update session status
        session = await self.get_session(session_id)
        if session:
            session.status = "reviewed"
            session.language = review.language
            session.code_snippet_preview = review.code_snippet_preview
            self._write_json(os.path.join(path, "session.json"), session.model_dump())

    async def get_review(self, session_id: str) -> ReviewResult | None:
        data = self._read_json(os.path.join(self._session_dir(session_id), "review.json"))
        if data is None:
            return None
        return ReviewResult(**data)

    async def save_findings(self, session_id: str, findings: list[Finding]) -> None:
        path = self._ensure_dir(session_id)
        self._write_json(os.path.join(path, "findings.json"), [f.model_dump() for f in findings])

    async def get_findings(self, session_id: str) -> list[Finding]:
        data = self._read_json(os.path.join(self._session_dir(session_id), "findings.json"))
        if data is None:
            return []
        return [Finding(**f) for f in data]

    async def add_chat_message(self, session_id: str, message: ChatMessage) -> None:
        path = self._ensure_dir(session_id)
        filepath = os.path.join(path, "chat_history.json")
        history = self._read_json(filepath) or []
        history.append(message.model_dump())
        self._write_json(filepath, history)

    async def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        data = self._read_json(os.path.join(self._session_dir(session_id), "chat_history.json"))
        if data is None:
            return []
        return [ChatMessage(**m) for m in data]

    async def list_sessions(self) -> list[Session]:
        if not os.path.exists(SESSIONS_DIR):
            return []
        sessions = []
        for name in os.listdir(SESSIONS_DIR):
            session = await self.get_session(name)
            if session:
                sessions.append(session)
        return sessions

    async def delete_session(self, session_id: str) -> None:
        path = self._session_dir(session_id)
        if os.path.exists(path):
            shutil.rmtree(path)
