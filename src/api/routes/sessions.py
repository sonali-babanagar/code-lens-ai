from fastapi import APIRouter, HTTPException
from src.api.dependencies import get_store

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("")
async def create_session():
    store = get_store()
    from uuid import uuid4
    session_id = uuid4().hex
    session = await store.create_session(session_id)
    return {"session_id": session.session_id, "status": session.status}


@router.get("")
async def list_sessions():
    store = get_store()
    sessions = await store.list_sessions()
    return [s.model_dump() for s in sessions]


@router.get("/{session_id}")
async def get_session(session_id: str):
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await store.delete_session(session_id)
    return {"detail": "Session deleted"}
