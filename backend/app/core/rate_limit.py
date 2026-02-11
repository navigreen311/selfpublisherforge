"""
Redis-based rate limiter with sliding window algorithm.

Supports tier-based limits and endpoint-specific overrides.
Re-exports the new rate limiter implementation for backward compatibility.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, Response
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.rate_limiter import (
    SlidingWindowRateLimiter as _NewSlidingWindowRateLimiter,
)
from app.core.rate_limiter import (
    get_rate_limiter as _get_new_limiter,
)
from app.schemas.common import PlanTier

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
RateLimitTier = PlanTier

# Legacy constants for backward compatibility
DEFAULT_TIER_LIMITS: dict[PlanTier, int] = {
    PlanTier.FREE: 60,
    PlanTier.PRO: 300,
    PlanTier.ENTERPRISE: 1000,
}

ENDPOINT_OVERRIDES: dict[str, dict[PlanTier, int]] = {
    "/api/v1/ai/": {
        PlanTier.FREE: 10,
        PlanTier.PRO: 60,
        PlanTier.ENTERPRISE: 200,
    },
    "/api/v1/generation/": {
        PlanTier.FREE: 10,
        PlanTier.PRO: 60,
        PlanTier.ENTERPRISE: 200,
    },
}

WINDOW_SIZE = 60  # seconds (1 minute)


# ---------------------------------------------------------------------------
# Backward Compatibility Wrapper
# ---------------------------------------------------------------------------


class SlidingWindowRateLimiter:
    """
    Backward-compatible wrapper around the new rate limiter.

    This maintains the old API: check(identifier, tier, path) -> (bool, dict)
    while using the new implementation under the hood.
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        self._limiter = _NewSlidingWindowRateLimiter(redis_client=redis_client)

    async def _get_redis(self) -> Any:
        """Get the Redis client (for test compatibility)."""
        return await self._limiter._get_redis()

    def _resolve_limit(self, tier: PlanTier, path: str) -> int:
        """Return the applicable rate limit for a tier + path combination."""
        for prefix, overrides in ENDPOINT_OVERRIDES.items():
            if path.startswith(prefix):
                return overrides.get(tier, DEFAULT_TIER_LIMITS[tier])
        return DEFAULT_TIER_LIMITS[tier]

    async def check(
        self,
        identifier: str,
        tier: PlanTier = PlanTier.FREE,
        path: str = "/",
    ) -> tuple[bool, dict[str, str]]:
        """
        Check whether the request is allowed (legacy API).

        Returns:
            (allowed, headers) where *headers* is a dict of
            X-RateLimit-* response headers.
        """
        limit = self._resolve_limit(tier, path)
        key = identifier

        result = await self._limiter.check(key, limit, WINDOW_SIZE)

        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_at),
        }

        return result.allowed, headers

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        await self._limiter.close()

    @property
    def _redis(self) -> Any:
        """Access to internal Redis client (for test compatibility)."""
        return self._limiter._redis


# Module-level singleton -------------------------------------------------
_limiter: SlidingWindowRateLimiter | None = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Return (and lazily create) the module-level rate limiter."""
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter()
    return _limiter


def _extract_tier(request: Request) -> PlanTier:
    """
    Determine the caller's tier from the request state.

    Falls back to FREE if no tier information is available.
    """
    user: dict[str, Any] | None = getattr(request.state, "user", None)
    if user and "tier" in user:
        try:
            return PlanTier(user["tier"])
        except ValueError:
            pass
    return PlanTier.FREE


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

    Uses the new rate limiter with per-endpoint configuration and tier-based multipliers.
    """

    def __init__(self, app: Any, limiter: SlidingWindowRateLimiter | None = None) -> None:
        super().__init__(app)
        # Use the wrapped legacy limiter if provided, or create a new one
        if limiter is None:
            self.limiter = _get_new_limiter()
            self._legacy_limiter = None
        elif hasattr(limiter, 'check_request'):
            # Already a new limiter instance (has check_request method)
            self.limiter = limiter
            self._legacy_limiter = None
        elif isinstance(limiter, SlidingWindowRateLimiter):
            # Legacy wrapper - use its internal new limiter
            self.limiter = limiter._limiter
            self._legacy_limiter = None
        else:
            # Mock or other object - wrap it to use legacy API
            self._legacy_limiter = limiter
            self.limiter = None

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)

        identifier = _extract_identifier(request)
        tier = _extract_tier(request)
        method = request.method
        path = request.url.path

        try:
            # Use the new limiter if available, otherwise use legacy API
            if self.limiter is not None:
                # New rate limiter with check_request method
                result = await self.limiter.check_request(
                    identifier=identifier,
                    method=method,
                    path=path,
                    tier=tier,
                )
                headers = {
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_at),
                }
                allowed = result.allowed
                if not allowed and result.retry_after is not None:
                    headers["Retry-After"] = str(result.retry_after)
            else:
                # Legacy limiter with check method
                allowed, headers = await self._legacy_limiter.check(
                    identifier=identifier,
                    tier=tier,
                    path=path,
                )
        except (RedisConnectionError, RedisError, ConnectionError, TimeoutError, OSError):
            # If Redis is unavailable, allow the request through
            logger.warning("Rate limiter unavailable, allowing request through", exc_info=True)
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

        # Request allowed, proceed and add rate limit headers
        response = await call_next(request)
        for name, value in headers.items():
            response.headers[name] = value
        return response
