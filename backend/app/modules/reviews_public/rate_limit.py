"""Lightweight per-IP rate limiter for the public review endpoints.

Prefers the Redis-backed sliding-window limiter used elsewhere in the app,
but degrades gracefully to an in-memory fixed-window counter when Redis is
not configured (local dev, tests). The in-memory fallback is single-process
only; production deploys should always have Redis available.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

PUBLIC_API_LIMIT = 60  # requests
PUBLIC_API_WINDOW = 60  # seconds (per IP)

_in_memory_buckets: dict[str, Deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


async def enforce_public_rate_limit(
    request: Request,
    limit: int | None = None,
    window: int | None = None,
) -> None:
    """Raise 429 if the requesting IP has exceeded the public API rate limit."""
    # Read module-level values lazily so tests can monkey-patch them at runtime.
    effective_limit = limit if limit is not None else PUBLIC_API_LIMIT
    effective_window = window if window is not None else PUBLIC_API_WINDOW
    limit = effective_limit
    window = effective_window
    ip = _client_ip(request)
    key = f"public_reviews:{ip}"

    # Try Redis-backed sliding window first; fall back silently.
    try:
        from app.core.rate_limiter import get_rate_limiter  # type: ignore

        limiter = get_rate_limiter()
        result = await limiter.check(key, limit=limit, window_seconds=window)
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(result.retry_after or window)},
            )
        return
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - Redis not available / misconfigured
        logger.debug("Falling back to in-memory public rate limit: %s", exc)

    now = time.monotonic()
    bucket = _in_memory_buckets[key]
    cutoff = now - window
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(window)},
        )
    bucket.append(now)
