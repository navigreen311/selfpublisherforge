"""
Unit tests for the sliding-window rate limiter.

These tests use a **fake Redis** implementation so they can run without
a live Redis server.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.rate_limit import (
    DEFAULT_TIER_LIMITS,
    ENDPOINT_OVERRIDES,
    RateLimitMiddleware,
    RateLimitTier,
    SlidingWindowRateLimiter,
    _extract_identifier,
    _extract_tier,
)


# ---------------------------------------------------------------------------
# Helpers -- in-memory fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    """Minimal in-memory stand-in for ``redis.asyncio.Redis``."""

    def __init__(self) -> None:
        self._store: dict[str, list[tuple[float, str]]] = {}

    def pipeline(self) -> "FakePipeline":
        return FakePipeline(self)

    async def zrem(self, key: str, member: str) -> int:
        if key in self._store:
            before = len(self._store[key])
            self._store[key] = [(s, m) for s, m in self._store[key] if m != member]
            return before - len(self._store[key])
        return 0

    async def close(self) -> None:
        pass


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self._redis = redis
        self._ops: list[tuple[str, Any]] = []

    def zremrangebyscore(self, key: str, min_score: str, max_score: float) -> "FakePipeline":
        self._ops.append(("zremrangebyscore", (key, min_score, max_score)))
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> "FakePipeline":
        self._ops.append(("zadd", (key, mapping)))
        return self

    def zcard(self, key: str) -> "FakePipeline":
        self._ops.append(("zcard", (key,)))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self._ops.append(("expire", (key, ttl)))
        return self

    async def execute(self) -> list[Any]:
        results: list[Any] = []
        for op, args in self._ops:
            if op == "zremrangebyscore":
                key, _min, max_score = args
                if key in self._redis._store:
                    self._redis._store[key] = [
                        (s, m) for s, m in self._redis._store[key] if s > max_score
                    ]
                results.append(0)
            elif op == "zadd":
                key, mapping = args
                if key not in self._redis._store:
                    self._redis._store[key] = []
                for member, score in mapping.items():
                    self._redis._store[key].append((score, member))
                results.append(len(mapping))
            elif op == "zcard":
                (key,) = args
                results.append(len(self._redis._store.get(key, [])))
            elif op == "expire":
                results.append(True)
        return results


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def limiter(fake_redis: FakeRedis) -> SlidingWindowRateLimiter:
    rl = SlidingWindowRateLimiter(redis_client=fake_redis)  # type: ignore[arg-type]
    return rl


# ---------------------------------------------------------------------------
# Tests -- Sliding Window Algorithm
# ---------------------------------------------------------------------------


class TestSlidingWindow:
    @pytest.mark.asyncio
    async def test_first_request_allowed(self, limiter: SlidingWindowRateLimiter) -> None:
        allowed, headers = await limiter.check("user:1", RateLimitTier.FREE)
        assert allowed is True
        assert int(headers["X-RateLimit-Limit"]) == 60
        assert int(headers["X-RateLimit-Remaining"]) == 59

    @pytest.mark.asyncio
    async def test_requests_up_to_limit_allowed(self, limiter: SlidingWindowRateLimiter) -> None:
        for i in range(60):
            allowed, _ = await limiter.check("user:2", RateLimitTier.FREE)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_exceeding_limit_denied(self, limiter: SlidingWindowRateLimiter) -> None:
        for _ in range(60):
            await limiter.check("user:3", RateLimitTier.FREE)

        allowed, headers = await limiter.check("user:3", RateLimitTier.FREE)
        assert allowed is False
        assert int(headers["X-RateLimit-Remaining"]) == 0

    @pytest.mark.asyncio
    async def test_different_identifiers_independent(self, limiter: SlidingWindowRateLimiter) -> None:
        for _ in range(60):
            await limiter.check("user:A", RateLimitTier.FREE)

        # user:A is exhausted
        allowed_a, _ = await limiter.check("user:A", RateLimitTier.FREE)
        assert allowed_a is False

        # user:B should still be fine
        allowed_b, _ = await limiter.check("user:B", RateLimitTier.FREE)
        assert allowed_b is True


# ---------------------------------------------------------------------------
# Tests -- Tier Limits
# ---------------------------------------------------------------------------


class TestTierLimits:
    @pytest.mark.asyncio
    async def test_free_tier_limit(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check("u:free", RateLimitTier.FREE)
        assert int(headers["X-RateLimit-Limit"]) == DEFAULT_TIER_LIMITS[RateLimitTier.FREE]

    @pytest.mark.asyncio
    async def test_pro_tier_limit(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check("u:pro", RateLimitTier.PRO)
        assert int(headers["X-RateLimit-Limit"]) == DEFAULT_TIER_LIMITS[RateLimitTier.PRO]

    @pytest.mark.asyncio
    async def test_enterprise_tier_limit(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check("u:ent", RateLimitTier.ENTERPRISE)
        assert int(headers["X-RateLimit-Limit"]) == DEFAULT_TIER_LIMITS[RateLimitTier.ENTERPRISE]

    @pytest.mark.asyncio
    async def test_endpoint_override_ai(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check(
            "u:free", RateLimitTier.FREE, path="/api/v1/ai/generate"
        )
        assert int(headers["X-RateLimit-Limit"]) == ENDPOINT_OVERRIDES["/api/v1/ai/"][RateLimitTier.FREE]

    @pytest.mark.asyncio
    async def test_endpoint_override_generation(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check(
            "u:pro", RateLimitTier.PRO, path="/api/v1/generation/text"
        )
        assert int(headers["X-RateLimit-Limit"]) == ENDPOINT_OVERRIDES["/api/v1/generation/"][RateLimitTier.PRO]


# ---------------------------------------------------------------------------
# Tests -- Header Injection
# ---------------------------------------------------------------------------


class TestRateLimitHeaders:
    @pytest.mark.asyncio
    async def test_headers_present(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check("u:hdr", RateLimitTier.FREE)
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    @pytest.mark.asyncio
    async def test_reset_is_future_timestamp(self, limiter: SlidingWindowRateLimiter) -> None:
        _, headers = await limiter.check("u:ts", RateLimitTier.FREE)
        reset = int(headers["X-RateLimit-Reset"])
        assert reset > int(time.time())

    @pytest.mark.asyncio
    async def test_remaining_decrements(self, limiter: SlidingWindowRateLimiter) -> None:
        _, h1 = await limiter.check("u:dec", RateLimitTier.FREE)
        _, h2 = await limiter.check("u:dec", RateLimitTier.FREE)
        assert int(h2["X-RateLimit-Remaining"]) == int(h1["X-RateLimit-Remaining"]) - 1


# ---------------------------------------------------------------------------
# Tests -- Identifier / Tier Extraction Helpers
# ---------------------------------------------------------------------------


class TestExtraction:
    def test_extract_tier_from_user(self) -> None:
        request = MagicMock()
        request.state.user = {"tier": "pro"}
        assert _extract_tier(request) == RateLimitTier.PRO

    def test_extract_tier_fallback_free(self) -> None:
        request = MagicMock()
        request.state.user = None
        assert _extract_tier(request) == RateLimitTier.FREE

    def test_extract_tier_invalid_falls_back(self) -> None:
        request = MagicMock()
        request.state.user = {"tier": "ultra"}
        assert _extract_tier(request) == RateLimitTier.FREE

    def test_extract_identifier_authenticated(self) -> None:
        request = MagicMock()
        request.state.user = {"user_id": "abc-123"}
        assert _extract_identifier(request) == "user:abc-123"

    def test_extract_identifier_anonymous_ip(self) -> None:
        request = MagicMock()
        request.state.user = None
        request.headers = {}
        request.client.host = "1.2.3.4"
        assert _extract_identifier(request) == "ip:1.2.3.4"

    def test_extract_identifier_forwarded_for(self) -> None:
        request = MagicMock()
        request.state.user = None
        request.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}
        assert _extract_identifier(request) == "ip:10.0.0.1"
