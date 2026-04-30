"""Planner node — generates a research plan and search queries."""

import logging

from agent.llm import call_llm_json
from agent.prompts import PLANNER_PROMPT
from agent.schemas import AgentState

logger = logging.getLogger(__name__)


def _fallback_plan(question: str) -> dict:
    words = question.split()
    q = " ".join(words[:10])
    return {
        "plan_steps": [
            {"step_number": 1, "description": "Direct web search for the question", "status": "pending"},
            {"step_number": 2, "description": "Analyse and synthesise search results", "status": "pending"},
        ],
        "search_queries": [q, f"{q} latest research 2025"],
    }


def planner_node(state: AgentState) -> dict:
    question = state["question"]
    logger.info(f"Planner: {question[:100]}")

    try:
        parsed = call_llm_json(f"{PLANNER_PROMPT}\n\nResearch question: {question}", max_tokens=2048)
        plan_steps = parsed.get("plan_steps", [])
        search_queries = parsed.get("search_queries", [])
        if not plan_steps or not search_queries:
            raise ValueError("Empty plan_steps or search_queries")
        logger.info(f"Planner: {len(plan_steps)} steps, {len(search_queries)} queries")
        return {"plan_steps": plan_steps, "search_queries": search_queries, "current_node": "planner"}

    except Exception as exc:
        logger.warning(f"Planner failed ({exc}), using fallback")
        fb = _fallback_plan(question)
        return {"plan_steps": fb["plan_steps"], "search_queries": fb["search_queries"], "current_node": "planner"}
