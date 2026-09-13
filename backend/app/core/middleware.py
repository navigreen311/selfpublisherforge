"""
API Gateway middleware stack.

Provides:
- RequestTimingMiddleware  -- X-Response-Time header
- CorrelationIDMiddleware  -- X-Request-ID generation / propagation
- RequestLoggingMiddleware -- structured request/response logging
- SecurityHeadersMiddleware -- HSTS, CSP, X-Frame-Options, X-Content-Type-Options
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("spf.middleware")


# ---------------------------------------------------------------------------
# Correlation ID
# ---------------------------------------------------------------------------


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Generate or propagate an ``X-Request-ID`` header.

    If the incoming request already carries the header, its value is reused;
    otherwise a new UUID-4 is created.  The value is stored on
    ``request.state.correlation_id`` so downstream code can access it.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response


# ---------------------------------------------------------------------------
# Request Timing
# ---------------------------------------------------------------------------


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Add an ``X-Response-Time`` header (in milliseconds)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
        return response


# ---------------------------------------------------------------------------
# Request Logging
# ---------------------------------------------------------------------------


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every request with method, path, status, duration and optional
    user context.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        correlation_id: str = getattr(request.state, "correlation_id", "-")
        user: dict[str, Any] | None = getattr(request.state, "user", None)
        user_id = str(user["user_id"]) if user and "user_id" in user else "anonymous"

        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
                "user_id": user_id,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response


# ---------------------------------------------------------------------------
# Security Headers
# ---------------------------------------------------------------------------

# Default values -- production-ready but overridable.
_DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inject security headers into every response.

    Custom headers can be passed at init time; defaults cover HSTS, CSP,
    X-Frame-Options, X-Content-Type-Options, Referrer-Policy and
    Permissions-Policy.
    """

    def __init__(self, app: Any, headers: dict[str, str] | None = None) -> None:
        super().__init__(app)
        self.headers = headers or _DEFAULT_SECURITY_HEADERS

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for name, value in self.headers.items():
            response.headers[name] = value
        return response
