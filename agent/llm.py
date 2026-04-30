"""
LLM client with dual-provider support.

Primary:  Gemini 2.5 Flash
Fallback: Groq Llama 3.3 70B

Auto-retries transient errors, falls back across providers.
All config comes from Settings — no raw os.getenv() calls.
"""

import json
import logging
import time
from typing import Callable

from config.settings import get_settings

logger = logging.getLogger(__name__)

RETRY_DELAYS = [2, 4, 8]


# ── Provider callers ──────────────────────────────────────────────────────────

def _call_gemini(prompt: str, max_tokens: int) -> str:
    from google import genai
    from google.genai import types

    cfg = get_settings()
    client = genai.Client(api_key=cfg.gemini_api_key)
    response = client.models.generate_content(
        model=cfg.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _call_groq(prompt: str, max_tokens: int) -> str:
    from groq import Groq

    cfg = get_settings()
    client = Groq(api_key=cfg.groq_api_key)
    response = client.chat.completions.create(
        model=cfg.groq_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """Parse JSON, stripping markdown fences if present."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        end = -1 if lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[1:end])
    return json.loads(cleaned)


# ── Transient error detection ─────────────────────────────────────────────────

_TRANSIENT_CODES = frozenset([
    "503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
    "rate_limit", "overloaded", "502", "504",
])


def _is_transient(error: Exception) -> bool:
    return any(code in str(error) for code in _TRANSIENT_CODES)


# ── Public API ────────────────────────────────────────────────────────────────

def call_llm_json(prompt: str, max_tokens: int = 4096) -> dict:
    """
    Call an LLM and return a parsed JSON dict.

    Provider order: Gemini first (if key set), Groq as fallback.
    Retries transient errors up to llm_max_retries times per provider.
    """
    cfg = get_settings()

    providers: list[tuple[str, Callable]] = []
    if cfg.has_gemini:
        providers.append(("gemini", _call_gemini))
    if cfg.has_groq:
        providers.append(("groq", _call_groq))

    if not providers:
        raise RuntimeError(
            "No LLM API key configured. Set GEMINI_API_KEY and/or GROQ_API_KEY in .env"
        )

    last_error: Exception | None = None

    for provider_name, call_fn in providers:
        for attempt in range(cfg.llm_max_retries):
            try:
                raw = call_fn(prompt, max_tokens)
                result = _parse_json(raw)
                if attempt > 0:
                    logger.info(f"LLM succeeded via {provider_name} on attempt {attempt + 1}")
                return result

            except json.JSONDecodeError as exc:
                logger.warning(f"[{provider_name}] JSON parse error attempt {attempt + 1}: {exc}")
                last_error = exc
                if attempt < cfg.llm_max_retries - 1:
                    time.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])

            except Exception as exc:
                last_error = exc
                if _is_transient(exc):
                    logger.warning(
                        f"[{provider_name}] Transient error attempt {attempt + 1}: {str(exc)[:120]}"
                    )
                    if attempt < cfg.llm_max_retries - 1:
                        time.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])
                        continue
                    logger.warning(f"[{provider_name}] Retries exhausted, trying next provider")
                    break
                else:
                    logger.error(f"[{provider_name}] Permanent error: {str(exc)[:150]}")
                    break  # skip remaining retries, try next provider

    raise last_error or RuntimeError("All LLM providers failed")
