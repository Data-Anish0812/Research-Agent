"""
Centralised logging configuration.
Call setup_logging() once at app startup.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a consistent format."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(name)-35s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "google", "groq", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
