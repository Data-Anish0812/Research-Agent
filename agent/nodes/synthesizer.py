"""Synthesizer node — writes the final research answer with citations."""

import json
import logging

from agent.llm import call_llm_json
from agent.prompts import SYNTHESIZER_PROMPT
from agent.schemas import AgentState

logger = logging.getLogger(__name__)


def _build_prompt_input(question: str, sources: list[dict], conflict_report: dict) -> str:
    lines = [f"Research Question: {question}\n\n=== GRADED SOURCES ===\n"]
    for i, src in enumerate(sources, 1):
        content = (src.get("scraped_content", "") or src.get("snippet", ""))[:3000]
        lines.append(
            f"--- Source {i} (Score: {src.get('overall_score', 'N/A')}) ---\n"
            f"Title: {src.get('title', 'N/A')}\n"
            f"URL: {src.get('url', 'N/A')}\n"
            f"Content: {content}\n"
        )
    lines.append("\n=== CONFLICT REPORT ===")
    lines.append(f"Agreed: {json.dumps(conflict_report.get('agreed', []))}")
    lines.append(f"Disputed: {json.dumps(conflict_report.get('disputed', []))}")
    lines.append(f"Unclear: {json.dumps(conflict_report.get('unclear', []))}")
    return "\n".join(lines)


def synthesizer_node(state: AgentState) -> dict:
    sources = state.get("graded_sources", [])
    conflict_report = state.get("conflict_report") or {"agreed": [], "disputed": [], "unclear": []}
    question = state["question"]
    logger.info("Synthesizer: generating answer")

    try:
        prompt_input = _build_prompt_input(question, sources, conflict_report)
        parsed = call_llm_json(f"{SYNTHESIZER_PROMPT}\n\n{prompt_input}", max_tokens=4096)

        findings = parsed.get("key_findings", [])
        for f in findings:
            f["verified"] = len(f.get("source_urls", [])) >= 2

        logger.info(f"Synthesizer: {len(findings)} findings, {sum(1 for f in findings if f.get('verified'))} verified")
        return {
            "short_answer": parsed.get("short_answer", "Unable to generate a summary."),
            "findings": findings,
            "limitations": parsed.get("limitations", []),
            "assumptions": parsed.get("assumptions", []),
            "suggested_next_steps": parsed.get("suggested_next_steps", []),
            "current_node": "synthesizer",
        }

    except Exception as exc:
        logger.error(f"Synthesizer failed: {exc}")
        return {
            "short_answer": "Research synthesis failed. Please try again.",
            "findings": [],
            "limitations": [f"Synthesis error: {exc}"],
            "assumptions": [],
            "suggested_next_steps": ["Retry the research query"],
            "current_node": "synthesizer",
        }
