"""
Pipeline runner — drives the LangGraph agent and returns a result dict.
Separated from UI so it can be called from tests, CLI, or other frontends.
"""

import logging
import time
from uuid import uuid4

from agent.graph import get_graph

logger = logging.getLogger(__name__)

# Node display labels (order matters — matches graph sequence)
NODE_LABELS: dict[str, str] = {
    "planner": "Planning research approach",
    "tool_executor": "Searching the web",
    "source_grader": "Grading source quality",
    "conflict_detector": "Detecting conflicts",
    "synthesizer": "Synthesising findings",
    "citation_validator": "Validating citations",
    "confidence": "Scoring confidence",
}


def _build_initial_state(question: str, request_id: str) -> dict:
    return {
        "request_id": request_id,
        "question": question,
        "plan_steps": [],
        "search_queries": [],
        "raw_sources": [],
        "graded_sources": [],
        "conflict_report": None,
        "findings": [],
        "short_answer": "",
        "confidence_level": "low",
        "confidence_reasoning": "",
        "limitations": [],
        "assumptions": [],
        "suggested_next_steps": [],
        "tools_called": [],
        "current_node": "",
        "error": None,
    }


def _build_result(state: dict, question: str, request_id: str, latency_ms: int) -> dict:
    sources_used = [
        {
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "quality_score": s.get("overall_score", 0),
        }
        for s in state.get("graded_sources", [])
    ]
    return {
        "request_id": request_id,
        "question": question,
        "short_answer": state.get("short_answer", ""),
        "key_findings": state.get("findings", []),
        "conflict_report": state.get("conflict_report") or {"agreed": [], "disputed": [], "unclear": []},
        "sources_used": sources_used,
        "confidence_level": state.get("confidence_level", "low"),
        "confidence_reasoning": state.get("confidence_reasoning", ""),
        "limitations": state.get("limitations", []),
        "assumptions": state.get("assumptions", []),
        "suggested_next_steps": state.get("suggested_next_steps", []),
        "plan_used": state.get("plan_steps", []),
        "tools_called": state.get("tools_called", []),
        "total_latency_ms": latency_ms,
    }


def run_pipeline(
    question: str,
    on_node_start=None,
    on_node_done=None,
) -> tuple[dict | None, str | None]:
    """
    Run the research pipeline for a given question.

    Args:
        question:      The research question.
        on_node_start: Optional callback(node_name: str) called when a node begins.
        on_node_done:  Optional callback(node_name: str) called when a node completes.

    Returns:
        (result_dict, error_string) — one of these will be None.
    """
    graph = get_graph()
    request_id = str(uuid4())
    initial_state = _build_initial_state(question, request_id)
    accumulated = dict(initial_state)
    start = time.time()

    try:
        for output in graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in output.items():
                if on_node_start:
                    on_node_start(node_name)

                if isinstance(node_output, dict):
                    for key, value in node_output.items():
                        if key in ("raw_sources", "tools_called") and isinstance(value, list):
                            accumulated[key] = accumulated.get(key, []) + value
                        else:
                            accumulated[key] = value

                if on_node_done:
                    on_node_done(node_name)

    except Exception as exc:
        logger.error(f"Pipeline error (request={request_id}): {exc}")
        return None, str(exc)

    latency_ms = int((time.time() - start) * 1000)
    result = _build_result(accumulated, question, request_id, latency_ms)
    logger.info(f"Pipeline complete (request={request_id}, latency={latency_ms}ms)")
    return result, None
