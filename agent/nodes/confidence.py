"""Confidence node — rates overall research quality as high / medium / low."""

import logging

from agent.llm import call_llm_json
from agent.prompts import CONFIDENCE_PROMPT
from agent.schemas import AgentState

logger = logging.getLogger(__name__)


def _build_prompt_input(state: AgentState) -> str:
    sources = state.get("graded_sources", [])
    report = state.get("conflict_report") or {}
    findings = state.get("findings", [])

    verified = sum(1 for f in findings if f.get("verified"))
    avg_score = (
        sum(s.get("overall_score", 0) for s in sources) / len(sources)
        if sources else 0.0
    )

    return "\n".join([
        f"Research Question: {state['question']}",
        f"Sources used: {len(sources)}",
        f"Average source quality: {avg_score:.1f}",
        f"Total findings: {len(findings)}",
        f"Verified findings (2+ sources): {verified}",
        f"Unverified findings: {len(findings) - verified}",
        "",
        "Conflict Report:",
        f"  Agreed: {len(report.get('agreed', []))}",
        f"  Disputed: {len(report.get('disputed', []))}",
        f"  Unclear: {len(report.get('unclear', []))}",
        "",
        f"Short Answer: {state.get('short_answer', 'N/A')}",
    ])


def confidence_node(state: AgentState) -> dict:
    logger.info("Confidence: scoring research output")
    sources = state.get("graded_sources", [])
    disputes = (state.get("conflict_report") or {}).get("disputed", [])

    try:
        parsed = call_llm_json(
            f"{CONFIDENCE_PROMPT}\n\n{_build_prompt_input(state)}",
            max_tokens=1024,
        )
        level = parsed.get("confidence_level", "medium").lower()
        reasoning = parsed.get("confidence_reasoning", "No reasoning provided.")
    except Exception as exc:
        logger.error(f"Confidence scoring failed: {exc}")
        level = "low"
        reasoning = f"Confidence scoring failed: {exc}. Defaulting to low."

    # Apply automatic downgrades
    notes: list[str] = []

    if disputes and level == "high":
        level = "medium"
        notes.append(f"{len(disputes)} dispute(s) detected")

    if len(sources) < 3 and level == "high":
        level = "medium"
        notes.append(f"only {len(sources)} source(s) used")

    if len(sources) < 2:
        level = "low"
        notes.append(f"forced low: only {len(sources)} source(s)")

    if sources:
        avg = sum(s.get("overall_score", 0) for s in sources) / len(sources)
        if avg < 3.0:
            if level == "high":
                level = "medium"
                notes.append(f"avg quality {avg:.1f} < 3.0")
            elif level == "medium":
                level = "low"
                notes.append(f"avg quality {avg:.1f} < 3.0")

    if notes:
        reasoning += " | Auto-adjustments: " + "; ".join(notes)

    logger.info(f"Confidence: {level}")
    return {"confidence_level": level, "confidence_reasoning": reasoning, "current_node": "confidence"}
