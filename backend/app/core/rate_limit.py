"""Rate limiting middleware using Redis sliding window counters.

Tier limits (requests per minute):
  - free:       60
  - starter:    120
  - pro:        300
  - business:   600
  - enterprise: 1000
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from redis.asyncio import Redis

from app.config import get_settings

# ---------------------------------------------------------------------------
# Tier -> requests per minute mapping
# ---------------------------------------------------------------------------
TIER_RATE_LIMITS: dict[str, int] = {
    "free": 60,
    "starter": 120,
    "pro": 300,
    "business": 600,
    "enterprise": 1000,
}

DEFAULT_RATE_LIMIT = TIER_RATE_LIMITS["free"]
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis.

    Behaviour:
    * Identifies callers by ``X-User-ID`` header (set by the auth layer) or
      falls back to the client IP.
    * Reads the caller's plan tier from ``X-Plan-Tier`` header (injected by the
      auth dependency) to pick the correct limit.
    * Uses a Redis sorted-set per caller to implement an accurate sliding
      window.
    * Injects standard ``X-RateLimit-*`` / ``Retry-After`` headers.
    """

    def __init__(self, app: Any, redis: Redis | None = None) -> None:
        super().__init__(app)
        self._redis = redis
        self._settings = get_settings()

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    async def _get_redis(self) -> Redis | None:
        """Lazily connect to Redis if not already provided."""
        if self._redis is not None:
            return self._redis
        try:
            self._redis = Redis.from_url(
                self._settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            return self._redis
        except Exception:  # noqa: BLE001
            # If Redis is unavailable, let requests through (fail-open).
            return None

    # ------------------------------------------------------------------
    # Core sliding-window logic
    # ------------------------------------------------------------------

    async def _check_rate_limit(
        self,
        redis: Redis,
        key: str,
        limit: int,
    ) -> tuple[bool, int, int, float]:
        """Check and update the sliding-window counter.

        Returns (allowed, remaining, limit, reset_at_epoch).
        """
        now = time.time()
        window_start = now - WINDOW_SECONDS
        pipe = redis.pipeline()

        # Remove entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipe.zadd(key, {f"{now}": now})
        # Count entries in window
        pipe.zcard(key)
        # Set key expiry to auto-cleanup
        pipe.expire(key, WINDOW_SECONDS + 1)

        results = await pipe.execute()
        request_count: int = results[2]

        remaining = max(0, limit - request_count)
        reset_at = now + WINDOW_SECONDS
        allowed = request_count <= limit

        return allowed, remaining, limit, reset_at

    # ------------------------------------------------------------------
    # Middleware dispatch
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip rate limiting for health-check and docs endpoints
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        redis = await self._get_redis()
        if redis is None:
            # Fail-open: if Redis is down, do not block requests.
            return await call_next(request)

        # Identify caller
        user_id = request.headers.get("X-User-ID")
        if user_id:
            identifier = f"user:{user_id}"
        else:
            client = request.client
            identifier = f"ip:{client.host}" if client else "ip:unknown"

        # Determine tier limit
        tier = request.headers.get("X-Plan-Tier", "free").lower()
        limit = TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMIT)

        rate_key = f"rate_limit:{identifier}"

        allowed, remaining, limit_val, reset_at = await self._check_rate_limit(
            redis, rate_key, limit
        )

        if not allowed:
            retry_after = max(1, int(reset_at - time.time()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={
                    "X-RateLimit-Limit": str(limit_val),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)

        # Attach rate-limit info headers
        response.headers["X-RateLimit-Limit"] = str(limit_val)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))

        return response
