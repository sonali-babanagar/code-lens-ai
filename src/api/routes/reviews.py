from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.api.dependencies import get_store, get_graph
from src.utils.file_utils import read_uploaded_file, read_uploaded_zip
from src.utils.github import parse_github_url, fetch_file_content, fetch_pr_files
from src.graph.nodes import run_multi_file_review
import json
import asyncio

router = APIRouter(prefix="/sessions/{session_id}", tags=["Reviews"])


class CodeReviewRequest(BaseModel):
    code: str
    language: str | None = None


@router.post("/review")
async def submit_review(session_id: str, request: CodeReviewRequest):
    """Submit raw code for review."""
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(request.code) > 500_000:
        raise HTTPException(status_code=422, detail="Code too long (max 500KB)")

    graph = get_graph()
    result = await graph.ainvoke({
        "code": request.code,
        "language": request.language or "",
        "session_id": session_id,
    })

    review = result["final_review"]
    await store.save_review(session_id, review)
    await store.save_findings(session_id, review.findings)
    return review.model_dump()


@router.post("/review/upload")
async def upload_for_review(session_id: str, file: UploadFile = File(...)):
    """Upload a single code file or a zip for review."""
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = await file.read()
    filename = file.filename or "unknown"

    if filename.endswith(".zip"):
        files = read_uploaded_zip(content)
        if not files:
            raise HTTPException(status_code=422, detail="No code files found in zip")

        # Multi-level review: Level 1 (per-file) + Level 2 (cross-file)
        graph = get_graph()
        multi_result = await run_multi_file_review(files, session_id, graph)

        # Collect all findings for storage
        all_findings = []
        for r in multi_result.file_reviews.values():
            all_findings.extend(r.findings)
        all_findings.extend(multi_result.cross_file_findings)

        # Save as a flat ReviewResult for backward compatibility
        from src.schemas.review import ReviewResult
        flat_review = ReviewResult(
            session_id=session_id,
            code_snippet_preview=f"[{len(files)} files: {', '.join(multi_result.files_reviewed)}]",
            language=files[0][2],
            findings=all_findings,
            summary=multi_result.summary,
        )
        await store.save_review(session_id, flat_review)
        await store.save_findings(session_id, all_findings)

        return multi_result.model_dump()
    else:
        code, language = read_uploaded_file(content, filename)

        graph = get_graph()
        result = await graph.ainvoke({
            "code": code,
            "language": language,
            "session_id": session_id,
            "file_name": filename,
        })

        review = result["final_review"]
        await store.save_review(session_id, review)
        await store.save_findings(session_id, review.findings)
        return review.model_dump()


class GitHubReviewRequest(BaseModel):
    github_url: str


@router.post("/review/github")
async def github_review(session_id: str, request: GitHubReviewRequest):
    """Review code from a GitHub file URL or PR URL."""
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        parsed = parse_github_url(request.github_url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    graph = get_graph()

    if parsed["type"] == "pr":
        files = await fetch_pr_files(parsed["owner"], parsed["repo"], parsed["pr_number"])
        if not files:
            raise HTTPException(status_code=422, detail="No code files found in PR")

        multi_result = await run_multi_file_review(files, session_id, graph)

        all_findings = []
        for r in multi_result.file_reviews.values():
            all_findings.extend(r.findings)
        all_findings.extend(multi_result.cross_file_findings)

        from src.schemas.review import ReviewResult
        flat_review = ReviewResult(
            session_id=session_id,
            code_snippet_preview=f"PR #{parsed['pr_number']}: {', '.join(multi_result.files_reviewed)}",
            language=files[0][2],
            findings=all_findings,
            summary=multi_result.summary,
        )
        await store.save_review(session_id, flat_review)
        await store.save_findings(session_id, all_findings)
        return multi_result.model_dump()

    else:
        filename, code, language = await fetch_file_content(request.github_url)
        result = await graph.ainvoke({
            "code": code,
            "language": language,
            "session_id": session_id,
            "file_name": filename,
        })
        review = result["final_review"]
        await store.save_review(session_id, review)
        await store.save_findings(session_id, review.findings)
        return review.model_dump()


# Node names in the graph mapped to SSE event names
_NODE_EVENT_MAP = {
    "analyze_code": "code_analysis",
    "security_agent": "security_findings",
    "architecture_agent": "architecture_findings",
    "performance_agent": "performance_findings",
    "synthesizer": "review_complete",
}


@router.post("/review/stream")
async def stream_review(session_id: str, request: CodeReviewRequest):
    """Stream review results as SSE events as each agent completes."""
    store = get_store()
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(request.code) > 500_000:
        raise HTTPException(status_code=422, detail="Code too long (max 500KB)")

    async def event_generator():
        graph = get_graph()
        final_review = None

        async for event in graph.astream_events(
            {"code": request.code, "language": request.language or "", "session_id": session_id},
            version="v2",
        ):
            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_end" and name in _NODE_EVENT_MAP:
                event_name = _NODE_EVENT_MAP[name]
                output = event.get("data", {}).get("output", {})

                if event_name == "code_analysis":
                    payload = output.get("code_analysis", {})
                elif event_name == "review_complete":
                    review = output.get("final_review")
                    if review:
                        final_review = review
                        payload = review.model_dump()
                    else:
                        continue
                else:
                    agent_output = output.get(event_name)
                    if agent_output:
                        payload = agent_output.model_dump()
                    else:
                        continue

                line = json.dumps(payload, default=str)
                yield f"event: {event_name}\ndata: {line}\n\n"

        # Save after stream completes
        if final_review:
            await store.save_review(session_id, final_review)
            await store.save_findings(session_id, final_review.findings)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/review")
async def get_review(session_id: str):
    store = get_store()
    review = await store.get_review(session_id)
    if not review:
        raise HTTPException(status_code=404, detail="No review found for this session")
    return review.model_dump()


@router.get("/findings")
async def get_findings(
    session_id: str,
    severity: str | None = Query(None),
    category: str | None = Query(None),
    agent: str | None = Query(None),
    file_name: str | None = Query(None),
):
    store = get_store()
    findings = await store.get_findings(session_id)
    if not findings:
        raise HTTPException(status_code=404, detail="No findings found")

    if severity:
        findings = [f for f in findings if f.severity.value == severity]
    if category:
        findings = [f for f in findings if f.category.value == category]
    if agent:
        findings = [f for f in findings if f.agent_name == agent]
    if file_name:
        findings = [f for f in findings if f.file_name == file_name]

    return [f.model_dump() for f in findings]
