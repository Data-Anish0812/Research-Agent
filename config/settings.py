"""
Centralised configuration using pydantic-settings.
All environment variables are read here — no os.getenv() scattered across files.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── LLM ───────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"

    # ── Search / Scraper ──────────────────────────────────────────────
    tavily_api_key: str = ""
    max_search_results: int = 5
    max_scrape_chars: int = 8000
    scrape_timeout_seconds: float = 8.0

    # ── Agent ─────────────────────────────────────────────────────────
    max_tool_calls: int = 5
    top_n_to_scrape: int = 2
    pipeline_timeout_seconds: int = 120
    llm_max_retries: int = 3

    # ── App ───────────────────────────────────────────────────────────
    app_title: str = "AI Research Agent"
    log_level: str = "INFO"

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key)

    def validate_keys(self) -> list[str]:
        """Return list of missing required API keys."""
        missing = []
        if not self.has_gemini and not self.has_groq:
            missing.append("GEMINI_API_KEY or GROQ_API_KEY (at least one required)")
        if not self.has_tavily:
            missing.append("TAVILY_API_KEY")
        return missing


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
