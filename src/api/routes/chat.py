from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.dependencies import get_store, get_chat_agent
from src.schemas.chat import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(prefix="/sessions/{session_id}/chat", tags=["Chat"])


@router.post("")
async def send_message(session_id: str, request: ChatRequest) -> ChatResponse:
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    review = await store.get_review(session_id)
    if not review:
        raise HTTPException(status_code=400, detail="No review found. Submit code for review first.")

    # save user message
    user_msg = ChatMessage(role="user", content=request.message)
    await store.add_chat_message(session_id, user_msg)

    # get history and generate response
    chat_history = await store.get_chat_history(session_id)
    chat_agent = get_chat_agent()
    reply = await chat_agent.respond(request.message, review, chat_history)

    # save assistant reply
    assistant_msg = ChatMessage(role="assistant", content=reply)
    await store.add_chat_message(session_id, assistant_msg)

    return ChatResponse(reply=reply, session_id=session_id)


@router.post("/stream")
async def stream_message(session_id: str, request: ChatRequest):
    """Stream chat response token-by-token via SSE."""
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    review = await store.get_review(session_id)
    if not review:
        raise HTTPException(status_code=400, detail="No review found. Submit code for review first.")

    user_msg = ChatMessage(role="user", content=request.message)
    await store.add_chat_message(session_id, user_msg)

    chat_history = await store.get_chat_history(session_id)
    chat_agent = get_chat_agent()

    async def event_generator():
        full_reply = []
        async for token in chat_agent.respond_stream(request.message, review, chat_history):
            full_reply.append(token)
            yield f"data: {token}\n\n"

        # Save complete reply after streaming finishes
        complete = "".join(full_reply)
        assistant_msg = ChatMessage(role="assistant", content=complete)
        await store.add_chat_message(session_id, assistant_msg)
        yield "event: done\ndata: \n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history")
async def get_chat_history(session_id: str):
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = await store.get_chat_history(session_id)
    return [m.model_dump() for m in history]
