"""
Structured JSON logging configuration.

Provides a ``setup_logging`` function that configures the root logger
(and the ``spf.*`` hierarchy) with a JSON formatter.  Every log record
automatically includes ``correlation_id``, ``user_id``, and ``org_id``
when those values are available on the current request state.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config import get_settings

# Keys whose values must be redacted when logging request/response bodies.
_SENSITIVE_KEYS = re.compile(
    r"(password|passwd|secret|token|api_key|apikey|authorization|credit_card|ssn)",
    re.IGNORECASE,
)

# Sentinel replacement
_REDACTED = "***REDACTED***"


def sanitize(data: Any, _depth: int = 0) -> Any:
    """
    Recursively strip sensitive fields from *data*.

    Works on dicts, lists and leaves other types untouched.  A depth
    guard prevents unbounded recursion on pathological inputs.
    """
    if _depth > 20:
        return data

    if isinstance(data, dict):
        return {
            k: (_REDACTED if _SENSITIVE_KEYS.search(k) else sanitize(v, _depth + 1))
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [sanitize(item, _depth + 1) for item in data]
    return data


class SPFJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that injects ``correlation_id``, ``user_id``
    and ``org_id`` into every log record if those fields are present in
    the record's extra data.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)

        # Propagate context fields from the ``extra`` dict.
        for field in ("correlation_id", "user_id", "org_id"):
            value = getattr(record, field, None)
            if value is not None:
                log_record[field] = value


def setup_logging() -> None:
    """
    Configure the Python logging subsystem with structured JSON output.

    - ``DEBUG`` / ``INFO`` in development (``settings.DEBUG == True``).
    - ``WARNING`` and above in production.
    """
    settings = get_settings()
    level = logging.DEBUG if settings.DEBUG else logging.WARNING

    formatter = SPFJsonFormatter(
        fmt="%(asctime)s %(level)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp"},
    )

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Application loggers -- always at least INFO in dev
    app_logger = logging.getLogger("spf")
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Quieten noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "elasticsearch"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
