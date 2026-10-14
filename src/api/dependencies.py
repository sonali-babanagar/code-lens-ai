from src.storage.local_storage import LocalSessionStore
from src.storage.base import BaseSessionStore
from src.graph.builder import build_review_graph
from src.agents.chat_agent import ChatAgent

_store: BaseSessionStore | None = None
_graph = None
_chat_agent: ChatAgent | None = None


def get_store() -> BaseSessionStore:
    global _store
    if _store is None:
        _store = LocalSessionStore()
    return _store


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_review_graph()
    return _graph


def get_chat_agent() -> ChatAgent:
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent
