"""
Tool Executor node — runs web search + scraping for each query.
Caps total tool calls, deduplicates by URL, logs every call.
"""

import logging
import time

from agent.schemas import AgentState
from agent.tools.scraper import scrape_url
from agent.tools.web_search import web_search
from config.settings import get_settings

logger = logging.getLogger(__name__)


def tool_executor_node(state: AgentState) -> dict:
    cfg = get_settings()
    queries = state.get("search_queries", [])
    logger.info(f"ToolExecutor: {len(queries)} queries, limit={cfg.max_tool_calls}")

    all_sources: list[dict] = []
    tool_logs: list[dict] = []
    seen_urls: set[str] = set()
    total_calls = 0

    for query in queries:
        if total_calls >= cfg.max_tool_calls:
            logger.info("ToolExecutor: max tool calls reached")
            break

        # Web search
        t0 = time.time()
        try:
            results = web_search(query)
            latency = int((time.time() - t0) * 1000)
            tool_logs.append({"tool_name": "web_search", "input": query, "success": True, "latency_ms": latency, "error": None})
            total_calls += 1
        except Exception as exc:
            latency = int((time.time() - t0) * 1000)
            tool_logs.append({"tool_name": "web_search", "input": query, "success": False, "latency_ms": latency, "error": str(exc)})
            total_calls += 1
            logger.error(f"ToolExecutor: web_search failed for '{query}': {exc}")
            continue

        # Scrape top N results
        scraped = 0
        for result in results:
            if total_calls >= cfg.max_tool_calls or scraped >= cfg.top_n_to_scrape:
                break
            url = result.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            t0 = time.time()
            try:
                content = scrape_url(url)
                latency = int((time.time() - t0) * 1000)
                result["scraped_content"] = content
                tool_logs.append({
                    "tool_name": "scraper", "input": url,
                    "success": bool(content), "latency_ms": latency,
                    "error": None if content else "Empty content",
                })
            except Exception as exc:
                latency = int((time.time() - t0) * 1000)
                tool_logs.append({"tool_name": "scraper", "input": url, "success": False, "latency_ms": latency, "error": str(exc)})

            total_calls += 1
            scraped += 1
            all_sources.append(result)

        # Add remaining results (snippet-only, no scrape)
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_sources.append(result)

    logger.info(f"ToolExecutor: {len(all_sources)} sources, {total_calls} calls")
    return {"raw_sources": all_sources, "tools_called": tool_logs, "current_node": "tool_executor"}
