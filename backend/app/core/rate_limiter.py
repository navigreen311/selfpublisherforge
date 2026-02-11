"""
Sliding window rate limiter with Redis backend.

Provides per-endpoint rate limiting with configurable limits and tier-based multipliers.
Uses Redis sorted sets for accurate sliding window algorithm.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from app.config import get_settings
from app.core.rate_limits_config import find_rate_limit
from app.schemas.common import PlanTier

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool  # Whether the request is allowed
    limit: int  # The limit that was applied
    remaining: int  # Remaining requests in the window
    reset_at: int  # Unix timestamp when the window resets
    retry_after: Optional[int] = None  # Seconds to wait before retrying (if denied)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter backed by Redis sorted sets.

    Each request is recorded as a member in a sorted set keyed by the
    rate limit identifier. The score is the request timestamp. On each
    check we:
    1. Remove entries outside the current window
    2. Count remaining members
    3. Add the current request if allowed
    4. Set expiration on the key to prevent memory leaks

    The sliding window ensures smooth rate limiting without the "burst at
    window boundary" problem of fixed windows.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        Initialize the rate limiter.

        Args:
            redis_client: Optional Redis client. If None, will be lazily
                         initialized from settings.
        """
        self._redis: Optional[redis.Redis] = redis_client

    async def _get_redis(self) -> redis.Redis:
        """Get or create the Redis client."""
        if self._redis is None:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """
        Check whether a request is allowed under the rate limit.

        Args:
            key: Unique identifier for this rate limit bucket
                (e.g., "user:123:POST:/api/v1/ai/generate")
            limit: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with allowed status and metadata

        Raises:
            RedisError: If Redis operations fail (caller should handle gracefully)
        """
        now = time.time()
        window_start = now - window_seconds

        r = await self._get_redis()
        redis_key = f"rl:{key}"

        # Use pipeline for atomic operations
        pipe = r.pipeline()

        # 1. Remove expired entries (outside the window)
        pipe.zremrangebyscore(redis_key, "-inf", window_start)

        # 2. Add current request with current timestamp as score
        pipe.zadd(redis_key, {f"{now}": now})

        # 3. Count entries in the window (including the one we just added)
        pipe.zcard(redis_key)

        # 4. Set expiry to prevent keys from lingering forever
        # Expire after window + buffer to ensure we don't lose data
        pipe.expire(redis_key, window_seconds + 10)

        # Execute all operations atomically
        results = await pipe.execute()

        # Result[2] is the count after adding the current request
        current_count: int = results[2]

        # Determine if request is allowed
        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        reset_at = int(now) + window_seconds

        if not allowed:
            # Remove the request we just added since it's denied
            await r.zrem(redis_key, f"{now}")

            # Calculate retry_after: time until oldest request expires
            # Get the oldest entry in the window
            oldest_entries = await r.zrange(redis_key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_timestamp = float(oldest_entries[0][1])
                retry_after = max(1, int(oldest_timestamp + window_seconds - now))
            else:
                retry_after = window_seconds
        else:
            retry_after = None

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def check_request(
        self,
        identifier: str,
        method: str,
        path: str,
        tier: PlanTier = PlanTier.FREE,
    ) -> RateLimitResult:
        """
        Check rate limit for a specific HTTP request.

        Convenience method that finds the appropriate limit for the endpoint
        and tier, then checks against it.

        Args:
            identifier: Unique identifier for the client (user ID or IP)
            method: HTTP method (GET, POST, etc.)
            path: Request path
            tier: User's subscription tier

        Returns:
            RateLimitResult with allowed status and metadata
        """
        # Find the applicable rate limit for this endpoint and tier
        limit, window_seconds = find_rate_limit(method, path, tier)

        # Build the rate limit key: identifier:method:path
        # This ensures different endpoints have separate rate limits
        key = f"{identifier}:{method}:{path}"

        # Check the rate limit
        return await self.check(key, limit, window_seconds)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """
    Get the module-level rate limiter singleton.

    Returns:
        Shared SlidingWindowRateLimiter instance
    """
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter()
    return _limiter


async def reset_limiter() -> None:
    """Reset the module-level limiter (useful for testing)."""
    global _limiter
    if _limiter is not None:
        await _limiter.close()
        _limiter = None
