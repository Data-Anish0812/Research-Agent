"""Conflict Detector node — finds agreed / disputed / unclear claims across sources."""

import logging

from agent.llm import call_llm_json
from agent.prompts import CONFLICT_DETECTOR_PROMPT
from agent.schemas import AgentState

logger = logging.getLogger(__name__)

_EMPTY_REPORT = {"agreed": [], "disputed": [], "unclear": []}


def _build_prompt_input(question: str, sources: list[dict]) -> str:
    lines = [f"Research Question: {question}\n\nGraded Sources:\n"]
    for i, src in enumerate(sources, 1):
        content = (src.get("scraped_content", "") or src.get("snippet", ""))[:3000]
        lines.append(
            f"--- Source {i} (Score: {src.get('overall_score', 'N/A')}) ---\n"
            f"Title: {src.get('title', 'N/A')}\n"
            f"URL: {src.get('url', 'N/A')}\n"
            f"Date: {src.get('date', 'N/A')}\n"
            f"Content: {content}\n"
        )
    return "\n".join(lines)


def conflict_detector_node(state: AgentState) -> dict:
    sources = state.get("graded_sources", [])
    question = state["question"]

    if len(sources) < 2:
        logger.info("ConflictDetector: <2 sources, skipping")
        return {
            "conflict_report": {**_EMPTY_REPORT, "unclear": ["Insufficient sources for conflict analysis"]},
            "current_node": "conflict_detector",
        }

    logger.info(f"ConflictDetector: analysing {len(sources)} sources")

    try:
        prompt_input = _build_prompt_input(question, sources)
        report = call_llm_json(f"{CONFLICT_DETECTOR_PROMPT}\n\n{prompt_input}", max_tokens=4096)
        report.setdefault("agreed", [])
        report.setdefault("disputed", [])
        report.setdefault("unclear", [])
        logger.info(
            f"ConflictDetector: {len(report['agreed'])} agreed, "
            f"{len(report['disputed'])} disputed, {len(report['unclear'])} unclear"
        )
        return {"conflict_report": report, "current_node": "conflict_detector"}

    except Exception as exc:
        logger.error(f"ConflictDetector failed: {exc}")
        return {
            "conflict_report": {**_EMPTY_REPORT, "unclear": [f"Conflict detection error: {exc}"]},
            "current_node": "conflict_detector",
        }
