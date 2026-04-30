"""
LangGraph StateGraph — wires all 7 nodes in the research pipeline.

Planner → ToolExecutor → SourceGrader → ConflictDetector
       → Synthesizer → CitationValidator → Confidence
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    citation_validator_node,
    confidence_node,
    conflict_detector_node,
    planner_node,
    source_grader_node,
    synthesizer_node,
    tool_executor_node,
)
from agent.schemas import AgentState

_NODE_SEQUENCE = [
    ("planner", planner_node),
    ("tool_executor", tool_executor_node),
    ("source_grader", source_grader_node),
    ("conflict_detector", conflict_detector_node),
    ("synthesizer", synthesizer_node),
    ("citation_validator", citation_validator_node),
    ("confidence", confidence_node),
]


def build_graph():
    """Build and compile the research agent graph."""
    workflow = StateGraph(AgentState)

    for name, fn in _NODE_SEQUENCE:
        workflow.add_node(name, fn)

    # Wire sequentially
    workflow.add_edge(START, _NODE_SEQUENCE[0][0])
    for i in range(len(_NODE_SEQUENCE) - 1):
        workflow.add_edge(_NODE_SEQUENCE[i][0], _NODE_SEQUENCE[i + 1][0])
    workflow.add_edge(_NODE_SEQUENCE[-1][0], END)

    return workflow.compile()


@lru_cache(maxsize=1)
def get_graph():
    """Return the compiled graph (cached — built once per process)."""
    return build_graph()
