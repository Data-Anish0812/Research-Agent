"""
Citation Validator node — strips hallucinated URLs from findings.

Validates every URL against the graded_sources list.
Recalculates verified status (needs 2+ real source URLs).
Attaches evidence snippets from matched sources.
"""

import logging
from urllib.parse import urlparse

from agent.schemas import AgentState

logger = logging.getLogger(__name__)


def _normalise(url: str) -> str:
    p = urlparse(url.strip())
    return f"{p.scheme}://{(p.hostname or '').lower()}{p.path.rstrip('/')}"


def _get_snippet(url: str, sources: list[dict], max_len: int = 200) -> str:
    norm = _normalise(url)
    for src in sources:
        if _normalise(src.get("url", "")) == norm:
            content = src.get("scraped_content", "") or src.get("snippet", "")
            return content[:max_len].strip()
    return ""


def _validate(findings: list[dict], sources: list[dict]) -> list[dict]:
    known: dict[str, str] = {}  # normalised → original URL
    for src in sources:
        raw = src.get("url", "")
        if raw:
            known[_normalise(raw)] = raw

    kept = stripped = 0

    for finding in findings:
        valid_urls: list[str] = []
        evidence: list[str] = []

        for url in finding.get("source_urls", []):
            if not url:
                continue
            norm = _normalise(url)
            if norm in known:
                valid_urls.append(known[norm])
                snippet = _get_snippet(url, sources)
                if snippet:
                    evidence.append(snippet)
                kept += 1
            else:
                stripped += 1
                logger.warning(
                    f"CitationValidator: stripped invented URL from "
                    f"'{finding.get('claim', '')[:60]}': {url}"
                )

        finding["source_urls"] = valid_urls
        finding["verified"] = len(valid_urls) >= 2
        if evidence:
            finding["evidence_snippets"] = evidence

    logger.info(f"CitationValidator: kept {kept}, stripped {stripped} URLs")
    return findings


def citation_validator_node(state: AgentState) -> dict:
    findings = state.get("findings", [])
    sources = state.get("graded_sources", [])
    logger.info(f"CitationValidator: {len(findings)} findings vs {len(sources)} sources")

    if not findings:
        return {"findings": [], "current_node": "citation_validator"}

    validated = _validate(findings, sources)
    verified = sum(1 for f in validated if f.get("verified"))
    logger.info(f"CitationValidator: {verified}/{len(validated)} verified after validation")
    return {"findings": validated, "current_node": "citation_validator"}
