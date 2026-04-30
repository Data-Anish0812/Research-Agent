"""
Web scraper using Jina Reader (r.jina.ai) — synchronous.
Sanitises content for prompt injection. Config from Settings.
"""

import logging
import re
import time

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(all\s+)?above\s+instructions",
    r"(?i)disregard\s+(all\s+)?previous",
    r"(?i)system\s*prompt",
    r"(?i)you\s+are\s+(now\s+)?an?\s+AI",
    r"(?i)you\s+are\s+(now\s+)?a\s+language\s+model",
    r"(?i)act\s+as\s+(if\s+you\s+are\s+)?",
    r"(?i)pretend\s+you\s+are",
    r"(?i)<\s*script[^>]*>.*?<\s*/\s*script\s*>",
    r"(?i)<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>",
    r"(?i)<\s*style[^>]*>.*?<\s*/\s*style\s*>",
    r"(?i)\{\{.*?\}\}",
    r"(?i)<%.*?%>",
]

_TRANSIENT_HTTP_CODES = frozenset([429, 502, 503, 504])


def _sanitize(content: str) -> str:
    """Strip prompt-injection patterns from scraped text."""
    for pattern in _INJECTION_PATTERNS:
        content = re.sub(pattern, "[REDACTED]", content, flags=re.DOTALL)
    return content


def scrape_url(url: str) -> str:
    """
    Scrape a URL via Jina Reader.

    Returns cleaned, truncated content or empty string on failure.
    """
    cfg = get_settings()
    jina_url = f"https://r.jina.ai/{url}"
    timeout = httpx.Timeout(cfg.scrape_timeout_seconds, connect=3.0)

    for attempt in range(2):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(
                    jina_url,
                    headers={"Accept": "text/plain", "User-Agent": "ResearchAgent/1.0"},
                    follow_redirects=True,
                )
                resp.raise_for_status()
                content = resp.text
                if len(content) > cfg.max_scrape_chars:
                    content = content[: cfg.max_scrape_chars] + "\n\n[CONTENT TRUNCATED]"
                return _sanitize(content)

        except httpx.TimeoutException:
            logger.warning(f"scrape_url timeout attempt {attempt + 1}: {url}")
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code in _TRANSIENT_HTTP_CODES:
                logger.warning(f"scrape_url HTTP {code} attempt {attempt + 1}: {url}")
            else:
                logger.error(f"scrape_url HTTP {code} (permanent): {url}")
                return ""
        except Exception as exc:
            logger.error(f"scrape_url error (permanent) attempt {attempt + 1}: {exc}")
            return ""

        if attempt == 0:
            time.sleep(0.5)

    logger.error(f"scrape_url failed after retries: {url}")
    return ""
