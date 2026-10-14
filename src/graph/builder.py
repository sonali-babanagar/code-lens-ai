from langgraph.graph import StateGraph, START, END
from src.graph.state import GraphState
from src.graph.nodes import (
    analyze_code,
    run_security_agent,
    run_architecture_agent,
    run_performance_agent,
    synthesize_results,
)


def build_review_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("analyze_code", analyze_code)
    graph.add_node("security_agent", run_security_agent)
    graph.add_node("architecture_agent", run_architecture_agent)
    graph.add_node("performance_agent", run_performance_agent)
    graph.add_node("synthesizer", synthesize_results)

    # code_analyzer runs first
    graph.add_edge(START, "analyze_code")

    # fan-out: all 3 agents run in parallel after code analysis
    graph.add_edge("analyze_code", "security_agent")
    graph.add_edge("analyze_code", "architecture_agent")
    graph.add_edge("analyze_code", "performance_agent")

    # fan-in: synthesizer waits for all 3 agents
    graph.add_edge("security_agent", "synthesizer")
    graph.add_edge("architecture_agent", "synthesizer")
    graph.add_edge("performance_agent", "synthesizer")

    graph.add_edge("synthesizer", END)

    return graph.compile()
