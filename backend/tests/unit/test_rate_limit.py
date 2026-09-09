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
    WINDOW_SIZE,
    RateLimitMiddleware,
    RateLimitTier,
    SlidingWindowRateLimiter,
    _extract_identifier,
    _extract_tier,
    get_rate_limiter,
)

# ---------------------------------------------------------------------------
# Helpers -- in-memory fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    """Minimal in-memory stand-in for ``redis.asyncio.Redis``."""

    def __init__(self) -> None:
        self._store: dict[str, list[tuple[float, str]]] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    async def zrem(self, key: str, member: str) -> int:
        if key in self._store:
            before = len(self._store[key])
            self._store[key] = [(s, m) for s, m in self._store[key] if m != member]
            return before - len(self._store[key])
        return 0

    async def zrange(
        self, key: str, start: int, stop: int, withscores: bool = False
    ) -> list[tuple[str, float]] | list[str]:
        """Get range of members from sorted set."""
        if key not in self._store:
            return []

        entries = sorted(self._store[key], key=lambda x: x[0])
        result = entries[start : stop + 1 if stop >= 0 else None]

        if withscores:
            return [(m, s) for s, m in result]
        return [m for _, m in result]

    async def close(self) -> None:
        pass


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self._redis = redis
        self._ops: list[tuple[str, Any]] = []

    def zremrangebyscore(self, key: str, min_score: str, max_score: float) -> FakePipeline:
        self._ops.append(("zremrangebyscore", (key, min_score, max_score)))
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> FakePipeline:
        self._ops.append(("zadd", (key, mapping)))
        return self

    def zcard(self, key: str) -> FakePipeline:
        self._ops.append(("zcard", (key,)))
        return self

    def expire(self, key: str, ttl: int) -> FakePipeline:
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


class FakeRedisConnectionError(FakeRedis):
    """A FakeRedis that raises ConnectionError on pipeline execution."""

    def pipeline(self) -> FakeErrorPipeline:
        return FakeErrorPipeline()


class FakeErrorPipeline:
    """Pipeline that raises on execute to simulate Redis failure."""

    def zremrangebyscore(self, *a: Any, **kw: Any) -> FakeErrorPipeline:
        return self

    def zadd(self, *a: Any, **kw: Any) -> FakeErrorPipeline:
        return self

    def zcard(self, *a: Any, **kw: Any) -> FakeErrorPipeline:
        return self

    def expire(self, *a: Any, **kw: Any) -> FakeErrorPipeline:
        return self

    async def execute(self) -> list[Any]:
        from redis.exceptions import ConnectionError as RedisConnectionError

        raise RedisConnectionError("Simulated Redis connection failure")


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

    @pytest.mark.asyncio
    async def test_denied_request_is_removed_from_window(
        self, fake_redis: FakeRedis, limiter: SlidingWindowRateLimiter
    ) -> None:
        """When a request is denied, the entry added during the check is rolled back."""
        for _ in range(60):
            await limiter.check("user:rollback", RateLimitTier.FREE)

        # This should be denied and the entry removed
        allowed, _ = await limiter.check("user:rollback", RateLimitTier.FREE)
        assert allowed is False

        # The sorted set should still have exactly 60 entries (not 61)
        key = "rl:user:rollback"
        assert len(fake_redis._store.get(key, [])) == 60

    @pytest.mark.asyncio
    async def test_token_replenishment_over_time(
        self, fake_redis: FakeRedis, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Entries older than the window are pruned, effectively replenishing capacity."""
        # Fill to limit
        for _ in range(60):
            await limiter.check("user:replenish", RateLimitTier.FREE)

        # Manually age all entries beyond the window
        key = "rl:user:replenish"
        old_time = time.time() - WINDOW_SIZE - 10
        fake_redis._store[key] = [(old_time, f"old-{i}") for i in range(60)]

        # Next request should be allowed because old entries get pruned
        allowed, headers = await limiter.check("user:replenish", RateLimitTier.FREE)
        assert allowed is True
        assert int(headers["X-RateLimit-Remaining"]) == 59


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

    @pytest.mark.asyncio
    async def test_non_override_path_uses_default(self, limiter: SlidingWindowRateLimiter) -> None:
        """A path that does not match any override prefix uses the default tier limit."""
        _, headers = await limiter.check(
            "u:free", RateLimitTier.FREE, path="/api/v1/books/list"
        )
        assert int(headers["X-RateLimit-Limit"]) == DEFAULT_TIER_LIMITS[RateLimitTier.FREE]

    @pytest.mark.asyncio
    async def test_enterprise_ai_endpoint_override(self, limiter: SlidingWindowRateLimiter) -> None:
        """Enterprise tier on AI endpoint gets the AI-specific enterprise limit."""
        _, headers = await limiter.check(
            "u:ent", RateLimitTier.ENTERPRISE, path="/api/v1/ai/summarize"
        )
        expected = ENDPOINT_OVERRIDES["/api/v1/ai/"][RateLimitTier.ENTERPRISE]
        assert int(headers["X-RateLimit-Limit"]) == expected


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

    @pytest.mark.asyncio
    async def test_remaining_never_negative(self, limiter: SlidingWindowRateLimiter) -> None:
        """Even after exceeding the limit, remaining should be 0, not negative."""
        for _ in range(65):
            _, headers = await limiter.check("u:neg", RateLimitTier.FREE)
        assert int(headers["X-RateLimit-Remaining"]) == 0

    @pytest.mark.asyncio
    async def test_reset_is_approximately_window_size_in_future(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """The reset timestamp should be roughly now + WINDOW_SIZE."""
        now = int(time.time())
        _, headers = await limiter.check("u:reset-check", RateLimitTier.FREE)
        reset = int(headers["X-RateLimit-Reset"])
        # Allow 2 second margin for test execution time
        assert now + WINDOW_SIZE - 2 <= reset <= now + WINDOW_SIZE + 2


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

    def test_extract_tier_no_tier_key(self) -> None:
        """User dict present but without a 'tier' key falls back to FREE."""
        request = MagicMock()
        request.state.user = {"user_id": "abc"}
        assert _extract_tier(request) == RateLimitTier.FREE

    def test_extract_tier_enterprise(self) -> None:
        request = MagicMock()
        request.state.user = {"tier": "enterprise"}
        assert _extract_tier(request) == RateLimitTier.ENTERPRISE

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

    def test_extract_identifier_no_client(self) -> None:
        """When request.client is None, should fall back to 'unknown'."""
        request = MagicMock()
        request.state.user = None
        request.headers = {}
        request.client = None
        assert _extract_identifier(request) == "ip:unknown"


# ---------------------------------------------------------------------------
# Tests -- Redis Backend (mock Redis)
# ---------------------------------------------------------------------------


class TestRedisIntegration:
    @pytest.mark.asyncio
    async def test_lazy_redis_initialization(self) -> None:
        """When no redis_client is provided, _get_redis creates one from settings."""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        mock_redis = MagicMock()

        with patch("app.core.rate_limiter.get_settings") as mock_settings, \
             patch("app.core.rate_limiter.redis.from_url", return_value=mock_redis) as mock_from_url:
            mock_settings.return_value.REDIS_URL = "redis://localhost:6379/0"
            result = await limiter._get_redis()
            mock_from_url.assert_called_once_with(
                "redis://localhost:6379/0",
                decode_responses=True,
            )
            assert result is mock_redis

    @pytest.mark.asyncio
    async def test_redis_reused_on_subsequent_calls(self, fake_redis: FakeRedis) -> None:
        """The same Redis client is returned on every _get_redis call."""
        limiter = SlidingWindowRateLimiter(redis_client=fake_redis)  # type: ignore[arg-type]
        r1 = await limiter._get_redis()
        r2 = await limiter._get_redis()
        assert r1 is r2

    @pytest.mark.asyncio
    async def test_close_clears_redis_reference(self, fake_redis: FakeRedis) -> None:
        """After close(), the internal Redis reference should be None."""
        limiter = SlidingWindowRateLimiter(redis_client=fake_redis)  # type: ignore[arg-type]
        assert limiter._redis is not None
        await limiter.close()
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_close_on_already_none_redis(self) -> None:
        """Calling close() when Redis is already None should not raise."""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        await limiter.close()  # Should not raise


# ---------------------------------------------------------------------------
# Tests -- Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_rate_limiter_returns_same_instance(self) -> None:
        """get_rate_limiter should return the same singleton each time."""
        # Reset module-level singleton for test isolation
        import app.core.rate_limit as rl_module

        original = rl_module._limiter
        try:
            rl_module._limiter = None
            limiter1 = get_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is limiter2
        finally:
            rl_module._limiter = original


# ---------------------------------------------------------------------------
# Tests -- RateLimitTier enum
# ---------------------------------------------------------------------------


class TestRateLimitTierEnum:
    def test_tier_values(self) -> None:
        assert RateLimitTier.FREE.value == "free"
        assert RateLimitTier.PRO.value == "pro"
        assert RateLimitTier.ENTERPRISE.value == "enterprise"

    def test_tier_is_string(self) -> None:
        """RateLimitTier inherits from str, so members are strings."""
        assert isinstance(RateLimitTier.FREE, str)

    def test_default_tier_limits_cover_all_tiers(self) -> None:
        # Only check the tiers that have entries in DEFAULT_TIER_LIMITS
        for tier in [RateLimitTier.FREE, RateLimitTier.PRO, RateLimitTier.ENTERPRISE]:
            assert tier in DEFAULT_TIER_LIMITS


# ---------------------------------------------------------------------------
# Tests -- Middleware Dispatch
# ---------------------------------------------------------------------------


class TestRateLimitMiddlewareDispatch:
    @pytest.mark.asyncio
    async def test_middleware_passes_allowed_request(self) -> None:
        """When the limiter allows, the middleware should call_next and attach headers."""
        mock_limiter = AsyncMock(spec=SlidingWindowRateLimiter)
        mock_limiter.check = AsyncMock(
            return_value=(
                True,
                {
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "59",
                    "X-RateLimit-Reset": "9999999999",
                },
            )
        )

        response = MagicMock()
        response.headers = {}
        call_next = AsyncMock(return_value=response)

        request = MagicMock()
        request.url.path = "/api/v1/books"
        request.state.user = None
        request.headers = {}
        request.client.host = "127.0.0.1"

        middleware = RateLimitMiddleware(app=MagicMock(), limiter=mock_limiter)
        result = await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)
        assert result.headers["X-RateLimit-Limit"] == "60"

    @pytest.mark.asyncio
    async def test_middleware_returns_429_when_denied(self) -> None:
        """When the limiter denies, the middleware returns a 429 JSON response."""
        mock_limiter = AsyncMock(spec=SlidingWindowRateLimiter)
        mock_limiter.check = AsyncMock(
            return_value=(
                False,
                {
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "9999999999",
                },
            )
        )

        call_next = AsyncMock()
        request = MagicMock()
        request.url.path = "/api/v1/books"
        request.state.user = None
        request.headers = {}
        request.client.host = "127.0.0.1"

        middleware = RateLimitMiddleware(app=MagicMock(), limiter=mock_limiter)
        result = await middleware.dispatch(request, call_next)

        assert result.status_code == 429
        call_next.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_middleware_skips_health_endpoint(self) -> None:
        """Requests to /health should bypass rate limiting entirely."""
        mock_limiter = AsyncMock(spec=SlidingWindowRateLimiter)

        response = MagicMock()
        call_next = AsyncMock(return_value=response)

        request = MagicMock()
        request.url.path = "/health"

        middleware = RateLimitMiddleware(app=MagicMock(), limiter=mock_limiter)
        result = await middleware.dispatch(request, call_next)

        mock_limiter.check.assert_not_awaited()
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_allows_on_redis_failure(self) -> None:
        """If Redis is unreachable, the middleware should allow the request through."""
        from redis.exceptions import ConnectionError as RedisConnectionError

        mock_limiter = AsyncMock(spec=SlidingWindowRateLimiter)
        mock_limiter.check = AsyncMock(side_effect=RedisConnectionError("down"))

        response = MagicMock()
        response.headers = {}
        call_next = AsyncMock(return_value=response)

        request = MagicMock()
        request.url.path = "/api/v1/books"
        request.state.user = None
        request.headers = {}
        request.client.host = "127.0.0.1"

        middleware = RateLimitMiddleware(app=MagicMock(), limiter=mock_limiter)
        result = await middleware.dispatch(request, call_next)

        # Request should be allowed through despite Redis failure
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_allows_on_timeout_error(self) -> None:
        """If Redis times out, the middleware should allow the request through."""
        mock_limiter = AsyncMock(spec=SlidingWindowRateLimiter)
        mock_limiter.check = AsyncMock(side_effect=TimeoutError("timeout"))

        response = MagicMock()
        response.headers = {}
        call_next = AsyncMock(return_value=response)

        request = MagicMock()
        request.url.path = "/api/v1/books"
        request.state.user = None
        request.headers = {}
        request.client.host = "127.0.0.1"

        middleware = RateLimitMiddleware(app=MagicMock(), limiter=mock_limiter)
        result = await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)


# ---------------------------------------------------------------------------
# Tests -- Concurrent Request Handling
# ---------------------------------------------------------------------------


class TestConcurrentRequests:
    @pytest.mark.asyncio
    async def test_concurrent_requests_counted_correctly(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Multiple concurrent requests to the same identifier are all tracked."""
        import asyncio

        tasks = [
            limiter.check("user:concurrent", RateLimitTier.FREE)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # All 10 should be allowed (well within the 60 limit)
        for allowed, headers in results:
            assert allowed is True

        # After 10 concurrent requests, remaining should reflect them
        _, final_headers = await limiter.check("user:concurrent", RateLimitTier.FREE)
        assert int(final_headers["X-RateLimit-Remaining"]) == 49  # 60 - 11

    @pytest.mark.asyncio
    async def test_concurrent_requests_at_boundary(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Fill to near-limit, then fire concurrent requests that cross the boundary."""
        # Fill 58 of 60 slots
        for _ in range(58):
            await limiter.check("user:boundary", RateLimitTier.FREE)

        import asyncio

        # Fire 5 concurrent -- 2 should be allowed, 3 denied
        tasks = [
            limiter.check("user:boundary", RateLimitTier.FREE)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)

        allowed_count = sum(1 for allowed, _ in results if allowed)
        denied_count = sum(1 for allowed, _ in results if not allowed)
        assert allowed_count == 2
        assert denied_count == 3
