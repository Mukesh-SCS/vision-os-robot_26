"""Simple project logger utilities."""

from __future__ import annotations

import logging
import multiprocessing as mp
import sys

from config import settings


def configure_logging(level: int = logging.INFO) -> None:
    """Configure process-safe basic logging output."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(processName)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with default setup if needed."""
    root = logging.getLogger()
    if not root.handlers:
        configure_logging(logging.DEBUG if settings.ENABLE_DEBUG_LOGS else logging.INFO)
    return logging.getLogger(name)


def process_started_message() -> str:
    """Provide a compact start message for worker processes."""
    proc = mp.current_process()
    return f"process started (name={proc.name}, pid={proc.pid})"
