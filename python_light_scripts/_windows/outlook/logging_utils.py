"""Structured (JSON-lines) logging for the Outlook processor.

Each log record is emitted as one JSON object per line, with a stable
``event`` name plus arbitrary structured context. This is easy to grep,
ingest, and assert on in tests. Pure and import-safe on every platform.
"""

from __future__ import annotations

import json
import logging
from typing import Any


class JsonLineFormatter(logging.Formatter):
    """Format each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(context)
        return json.dumps(payload, default=str, sort_keys=True)


def get_structured_logger(
    name: str = "outlook.processor",
    log_file: str | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Return a logger that emits JSON-line records.

    Args:
        name: logger name.
        log_file: if given, records are written here; otherwise to stderr.
        level: logging level.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler: logging.Handler = (
            logging.FileHandler(log_file) if log_file else logging.StreamHandler()
        )
        handler.setFormatter(JsonLineFormatter())
        logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, level: int, event: str, **context: Any) -> None:
    """Log a structured ``event`` with arbitrary keyword ``context`` fields."""
    logger.log(level, event, extra={"context": context})
