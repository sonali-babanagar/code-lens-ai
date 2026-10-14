from src.graph.state import GraphState
from src.agents.code_analyzer import CodeAnalyzer
from src.agents.security_agent import SecurityAgent
from src.agents.architecture_agent import ArchitectureAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.synthesizer import Synthesizer
from src.agents.cross_reference_agent import CrossReferenceAgent
from src.schemas.review import MultiFileReviewResult, ReviewResult
from src.rag.retriever import KnowledgeRetriever

_retriever = None


def _get_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


async def analyze_code(state: GraphState) -> dict:
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze(state["code"], state.get("language"))
    return {"code_analysis": analysis, "language": analysis["language"]}


async def run_security_agent(state: GraphState) -> dict:
    agent = SecurityAgent(_get_retriever())
    output = await agent.analyze(state["code"], state["language"], state.get("file_name"))
    return {"security_findings": output}


async def run_architecture_agent(state: GraphState) -> dict:
    agent = ArchitectureAgent(_get_retriever())
    output = await agent.analyze(state["code"], state["language"], state.get("file_name"))
    return {"architecture_findings": output}


async def run_performance_agent(state: GraphState) -> dict:
    agent = PerformanceAgent(_get_retriever())
    output = await agent.analyze(state["code"], state["language"], state.get("file_name"))
    return {"performance_findings": output}


async def synthesize_results(state: GraphState) -> dict:
    synthesizer = Synthesizer()
    agent_outputs = [
        out for out in [
            state.get("security_findings"),
            state.get("architecture_findings"),
            state.get("performance_findings"),
        ] if out is not None
    ]
    review = synthesizer.synthesize(
        session_id=state["session_id"],
        code=state["code"],
        language=state["language"],
        agent_outputs=agent_outputs,
    )
    return {"final_review": review}


async def run_multi_file_review(
    files: list[tuple[str, str, str]],
    session_id: str,
    graph,
) -> MultiFileReviewResult:
    """Level 1: review each file independently, Level 2: cross-file analysis."""
    file_reviews: dict[str, ReviewResult] = {}
    files_map: dict[str, str] = {}

    # Level 1 — per-file review
    for filename, code, language in files:
        files_map[filename] = code
        result = await graph.ainvoke({
            "code": code,
            "language": language,
            "session_id": session_id,
            "file_name": filename,
        })
        file_reviews[filename] = result["final_review"]

    # Level 2 — cross-file analysis (only if multiple files)
    cross_findings = []
    if len(files) > 1:
        cross_agent = CrossReferenceAgent()
        cross_output = await cross_agent.analyze(files_map, file_reviews)
        cross_findings = cross_output.findings

    # Build combined summary
    total_findings = sum(len(r.findings) for r in file_reviews.values()) + len(cross_findings)
    all_findings = []
    for r in file_reviews.values():
        all_findings.extend(r.findings)
    all_findings.extend(cross_findings)

    from src.agents.synthesizer import Synthesizer
    synthesizer = Synthesizer()
    summary = synthesizer._build_summary(all_findings)

    return MultiFileReviewResult(
        session_id=session_id,
        files_reviewed=list(files_map.keys()),
        file_reviews=file_reviews,
        cross_file_findings=cross_findings,
        summary=summary,
    )
