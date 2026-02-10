"""Structured JSON logging with correlation-ID propagation.

Usage::

    from app.core.logging import get_logger, correlation_id_ctx

    logger = get_logger(__name__)
    logger.info("processing request", extra={"user_id": "abc"})

The ``correlation_id_ctx`` context-var is set by the
``CorrelationIdMiddleware`` in ``middleware.py`` and automatically
injected into every log record by ``JsonFormatter``.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Correlation ID context variable (set per-request by middleware)
# ---------------------------------------------------------------------------
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Fields emitted:
      timestamp, level, logger, message, correlation_id, module, function,
      line, plus any keys from ``record.extra``.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Merge extra fields passed via ``extra={...}``
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry.update(record.extra)

        # Also pull out any ad-hoc attributes set by the caller
        for key in ("user_id", "org_id", "request_id", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Attach exception info when present
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# ---------------------------------------------------------------------------
# Filter that injects contextvar values into every record
# ---------------------------------------------------------------------------
class CorrelationIdFilter(logging.Filter):
    """Adds ``correlation_id`` attribute to every record from the context var."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get()  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
def setup_logging(
    level: str = "INFO",
    json_output: bool = True,
) -> None:
    """Configure the root logger for the application.

    Call once at startup (e.g. in the FastAPI lifespan).

    Parameters
    ----------
    level:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    json_output:
        If True, use ``JsonFormatter``; otherwise use a human-readable
        format (useful for local development).
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove existing handlers to avoid duplicates on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s [cid=%(correlation_id)s]"
            )
        )

    handler.addFilter(CorrelationIdFilter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    If ``setup_logging`` has not been called yet the logger will still
    work with Python's default config.
    """
    return logging.getLogger(name)
