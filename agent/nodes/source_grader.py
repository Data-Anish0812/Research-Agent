"""Source Grader node — scores each source on relevance, authority, recency, depth."""

import logging

from agent.llm import call_llm_json
from agent.prompts import SOURCE_GRADER_PROMPT
from agent.schemas import AgentState

logger = logging.getLogger(__name__)

_SCORE_THRESHOLD = 3.0
_FALLBACK_KEEP = 3


def _build_prompt_input(question: str, raw_sources: list[dict]) -> str:
    lines = [f"Research Question: {question}\n\nSources to grade:\n"]
    for i, src in enumerate(raw_sources, 1):
        preview = (src.get("scraped_content", "") or src.get("snippet", ""))[:2000]
        lines.append(
            f"--- Source {i} ---\n"
            f"Title: {src.get('title', 'N/A')}\n"
            f"URL: {src.get('url', 'N/A')}\n"
            f"Date: {src.get('date', 'N/A')}\n"
            f"Content: {preview}\n"
        )
    return "\n".join(lines)


def source_grader_node(state: AgentState) -> dict:
    raw_sources = state.get("raw_sources", [])
    question = state["question"]

    if not raw_sources:
        logger.warning("SourceGrader: no sources to grade")
        return {"graded_sources": [], "current_node": "source_grader"}

    logger.info(f"SourceGrader: grading {len(raw_sources)} sources")

    try:
        prompt_input = _build_prompt_input(question, raw_sources)
        parsed = call_llm_json(f"{SOURCE_GRADER_PROMPT}\n\n{prompt_input}", max_tokens=4096)
        graded = parsed.get("graded_sources", [])

        # Restore scraped_content that the LLM may have dropped
        content_map = {s["url"]: s.get("scraped_content", "") for s in raw_sources}
        for g in graded:
            if not g.get("scraped_content"):
                g["scraped_content"] = content_map.get(g.get("url", ""), "")

        above = [g for g in graded if g.get("overall_score", 0) >= _SCORE_THRESHOLD]
        if above:
            result = above
        elif graded:
            result = sorted(graded, key=lambda x: x.get("overall_score", 0), reverse=True)[:_FALLBACK_KEEP]
            logger.warning("SourceGrader: all below threshold, keeping top 3 as fallback")
        else:
            result = []

        logger.info(f"SourceGrader: {len(result)} sources passed")
        return {"graded_sources": result, "current_node": "source_grader"}

    except Exception as exc:
        logger.error(f"SourceGrader failed: {exc}")
        fallback = [
            {**s, "scores": {"relevance": 3, "authority": 3, "recency": 3, "depth": 3}, "overall_score": 3.0}
            for s in raw_sources[:5]
        ]
        return {"graded_sources": fallback, "current_node": "source_grader"}
