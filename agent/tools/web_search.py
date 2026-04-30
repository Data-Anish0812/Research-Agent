"""
Web search via Tavily API (synchronous).
Config is sourced from Settings — no raw os.getenv() calls.
"""

import logging
import time

from tavily import TavilyClient

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> TavilyClient:
    cfg = get_settings()
    if not cfg.has_tavily:
        raise RuntimeError("TAVILY_API_KEY is not configured in .env")
    return TavilyClient(api_key=cfg.tavily_api_key)


def web_search(query: str, max_results: int | None = None) -> list[dict]:
    """
    Search the web using Tavily.

    Returns a list of dicts with keys: title, url, snippet, date, scraped_content.
    Returns an empty list on failure — callers must handle this gracefully.
    """
    cfg = get_settings()
    n = max_results or cfg.max_search_results

    for attempt in range(2):
        try:
            result = _get_client().search(
                query=query,
                max_results=n,
                search_depth="advanced",
            )
            sources = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "date": r.get("published_date", ""),
                    "scraped_content": "",
                }
                for r in result.get("results", [])
            ]
            logger.debug(f"web_search: '{query[:60]}' → {len(sources)} results")
            return sources

        except Exception as exc:
            logger.warning(f"web_search error attempt {attempt + 1}: {exc}")
            if attempt == 0:
                time.sleep(0.5)

    logger.error(f"web_search failed after retries for query: {query}")
    return []
