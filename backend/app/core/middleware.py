"""Application middleware stack.

Provides:
* **CorrelationIdMiddleware** -- injects/propagates a unique request ID.
* **RequestLoggingMiddleware** -- logs every request with method, path,
  status code and duration in milliseconds.
* **TimingMiddleware** -- adds ``X-Process-Time-Ms`` response header.
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)

# Header used to propagate correlation IDs across services.
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request has a correlation ID.

    If the incoming request carries an ``X-Correlation-ID`` header it is
    reused; otherwise a new UUID-4 is generated.  The value is stored in
    the ``correlation_id_ctx`` context-var so that the structured logger
    can include it automatically.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        cid = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # Store in contextvars for logger access
        token = correlation_id_ctx.set(cid)
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = cid
            return response
        finally:
            correlation_id_ctx.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status and duration."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.perf_counter()

        # Let request proceed
        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_agent": request.headers.get("user-agent", ""),
            },
        )

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add ``X-Process-Time-Ms`` header with the server processing time."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
