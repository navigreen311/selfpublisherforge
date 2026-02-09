"""
Redis-based rate limiter with sliding window algorithm.

Supports tier-based limits and endpoint-specific overrides.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings


class RateLimitTier(str, Enum):
    """Rate limit tiers mapped to subscription plans."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Default requests-per-minute by tier
DEFAULT_TIER_LIMITS: dict[RateLimitTier, int] = {
    RateLimitTier.FREE: 60,
    RateLimitTier.PRO: 300,
    RateLimitTier.ENTERPRISE: 1000,
}

# Endpoint-specific overrides (path prefix -> requests per minute).
# AI generation endpoints get lower limits.
ENDPOINT_OVERRIDES: dict[str, dict[RateLimitTier, int]] = {
    "/api/v1/ai/": {
        RateLimitTier.FREE: 10,
        RateLimitTier.PRO: 60,
        RateLimitTier.ENTERPRISE: 200,
    },
    "/api/v1/generation/": {
        RateLimitTier.FREE: 10,
        RateLimitTier.PRO: 60,
        RateLimitTier.ENTERPRISE: 200,
    },
}

WINDOW_SIZE = 60  # seconds (1 minute)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter backed by Redis sorted sets.

    Each request is recorded as a member in a sorted set keyed by the
    client identifier. The score is the request timestamp. On each
    check we remove entries outside the window and count remaining
    members.
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis: redis.Redis | None = redis_client

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    def _resolve_limit(self, tier: RateLimitTier, path: str) -> int:
        """Return the applicable rate limit for a tier + path combination."""
        for prefix, overrides in ENDPOINT_OVERRIDES.items():
            if path.startswith(prefix):
                return overrides.get(tier, DEFAULT_TIER_LIMITS[tier])
        return DEFAULT_TIER_LIMITS[tier]

    async def check(
        self,
        identifier: str,
        tier: RateLimitTier = RateLimitTier.FREE,
        path: str = "/",
    ) -> tuple[bool, dict[str, str]]:
        """
        Check whether the request is allowed.

        Returns:
            (allowed, headers) where *headers* is a dict of
            X-RateLimit-* response headers.
        """
        limit = self._resolve_limit(tier, path)
        now = time.time()
        window_start = now - WINDOW_SIZE

        r = await self._get_redis()
        key = f"rl:{identifier}"

        pipe = r.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Add current request
        pipe.zadd(key, {f"{now}": now})
        # Count entries in window
        pipe.zcard(key)
        # Set expiry so keys don't linger
        pipe.expire(key, WINDOW_SIZE + 1)
        results = await pipe.execute()

        current_count: int = results[2]
        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        reset_at = int(now) + WINDOW_SIZE

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        if not allowed:
            # Remove the request we just added since it's denied
            await r.zrem(key, f"{now}")

        return allowed, headers

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# Module-level singleton -------------------------------------------------
_limiter: SlidingWindowRateLimiter | None = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Return (and lazily create) the module-level rate limiter."""
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter()
    return _limiter


def _extract_tier(request: Request) -> RateLimitTier:
    """
    Determine the caller's tier from the request state.

    Falls back to FREE if no tier information is available.
    """
    user: dict[str, Any] | None = getattr(request.state, "user", None)
    if user and "tier" in user:
        try:
            return RateLimitTier(user["tier"])
        except ValueError:
            pass
    return RateLimitTier.FREE


def _extract_identifier(request: Request) -> str:
    """
    Build a unique identifier for rate limiting.

    Authenticated users are keyed by user_id; anonymous callers by IP.
    """
    user: dict[str, Any] | None = getattr(request.state, "user", None)
    if user and "user_id" in user:
        return f"user:{user['user_id']}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces per-request rate limiting.
    """

    def __init__(self, app: Any, limiter: SlidingWindowRateLimiter | None = None) -> None:
        super().__init__(app)
        self.limiter = limiter or get_rate_limiter()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)

        identifier = _extract_identifier(request)
        tier = _extract_tier(request)

        try:
            allowed, headers = await self.limiter.check(
                identifier=identifier,
                tier=tier,
                path=request.url.path,
            )
        except Exception:
            # If Redis is unavailable, allow the request through
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                    }
                },
                headers=headers,
            )

        response = await call_next(request)
        for name, value in headers.items():
            response.headers[name] = value
        return response
