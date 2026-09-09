"""
Unit tests for the enhanced rate limiter with per-endpoint configuration.

Tests cover:
- Sliding window algorithm
- Per-endpoint configuration with wildcards
- Tier-based multipliers
- Retry-After header calculation
- Pattern matching
- Edge cases and error handling
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from app.core.rate_limiter import (
    SlidingWindowRateLimiter,
    get_rate_limiter,
    reset_limiter,
)
from app.core.rate_limits_config import (
    TIER_MULTIPLIERS,
    find_rate_limit,
    match_pattern,
)
from app.schemas.common import PlanTier

# ---------------------------------------------------------------------------
# Fake Redis Implementation
# ---------------------------------------------------------------------------


class FakeRedis:
    """Minimal in-memory stand-in for redis.asyncio.Redis."""

    def __init__(self) -> None:
        self._store: dict[str, list[tuple[float, str]]] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    async def zrem(self, key: str, member: str) -> int:
        """Remove a member from a sorted set."""
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
        """Close connection (no-op for fake)."""
        pass


class FakePipeline:
    """Pipeline for batching Redis commands."""

    def __init__(self, redis: FakeRedis) -> None:
        self._redis = redis
        self._ops: list[tuple[str, Any]] = []

    def zremrangebyscore(
        self, key: str, min_score: str, max_score: float
    ) -> FakePipeline:
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
        """Execute all queued operations."""
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
    return SlidingWindowRateLimiter(redis_client=fake_redis)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests -- Pattern Matching
# ---------------------------------------------------------------------------


class TestPatternMatching:
    def test_exact_match(self) -> None:
        assert match_pattern("/api/v1/auth/login", "/api/v1/auth/login") is True

    def test_exact_mismatch(self) -> None:
        assert match_pattern("/api/v1/auth/login", "/api/v1/auth/register") is False

    def test_wildcard_at_end(self) -> None:
        assert match_pattern("/api/v1/ai/*", "/api/v1/ai/generate") is True
        assert match_pattern("/api/v1/ai/*", "/api/v1/ai/covers/create") is True

    def test_wildcard_mismatch(self) -> None:
        assert match_pattern("/api/v1/ai/*", "/api/v1/books/list") is False

    def test_longer_pattern_than_path(self) -> None:
        assert match_pattern("/api/v1/auth/login/extra", "/api/v1/auth/login") is False

    def test_pattern_with_multiple_segments_after_wildcard(self) -> None:
        # Wildcard should match everything after
        assert (
            match_pattern("/api/v1/ai/*", "/api/v1/ai/writing/generate/chapter")
            is True
        )

    def test_empty_segments(self) -> None:
        assert match_pattern("/api/v1/*", "/api/v1/") is True


# ---------------------------------------------------------------------------
# Tests -- Rate Limit Configuration
# ---------------------------------------------------------------------------


class TestRateLimitConfiguration:
    def test_find_exact_match(self) -> None:
        limit, window = find_rate_limit("POST", "/api/v1/auth/login", PlanTier.FREE)
        assert limit == 5
        assert window == 300

    def test_find_with_tier_multiplier(self) -> None:
        # FREE tier: 5 requests
        limit_free, window = find_rate_limit(
            "POST", "/api/v1/auth/login", PlanTier.FREE
        )
        assert limit_free == 5

        # STARTER tier: 5 * 2 = 10 requests
        limit_starter, _ = find_rate_limit(
            "POST", "/api/v1/auth/login", PlanTier.STARTER
        )
        assert limit_starter == 10

        # PRO tier: 5 * 5 = 25 requests
        limit_pro, _ = find_rate_limit("POST", "/api/v1/auth/login", PlanTier.PRO)
        assert limit_pro == 25

        # ENTERPRISE tier: 5 * 50 = 250 requests
        limit_ent, _ = find_rate_limit(
            "POST", "/api/v1/auth/login", PlanTier.ENTERPRISE
        )
        assert limit_ent == 250

    def test_find_wildcard_match(self) -> None:
        # Should match "POST /api/v1/ai/*"
        limit, window = find_rate_limit(
            "POST", "/api/v1/ai/generate-outline", PlanTier.FREE
        )
        assert limit == 15  # AI catch-all
        assert window == 3600

    def test_find_most_specific_match(self) -> None:
        # "POST /api/v1/ai/writing/*" is more specific than "POST /api/v1/ai/*"
        limit, window = find_rate_limit(
            "POST", "/api/v1/ai/writing/generate", PlanTier.FREE
        )
        assert limit == 20  # Writing specific
        assert window == 3600

    def test_find_general_api_fallback(self) -> None:
        # Should match "GET /api/v1/*"
        limit, window = find_rate_limit("GET", "/api/v1/books/list", PlanTier.FREE)
        assert limit == 100
        assert window == 60

    def test_find_default_when_no_match(self) -> None:
        # No configured pattern for this endpoint
        limit, window = find_rate_limit("GET", "/some/other/path", PlanTier.FREE)
        assert limit == 60  # Default
        assert window == 60

    def test_tier_multipliers_exist(self) -> None:
        assert TIER_MULTIPLIERS[PlanTier.FREE] == 1.0
        assert TIER_MULTIPLIERS[PlanTier.STARTER] == 2.0
        assert TIER_MULTIPLIERS[PlanTier.PRO] == 5.0
        assert TIER_MULTIPLIERS[PlanTier.BUSINESS] == 10.0
        assert TIER_MULTIPLIERS[PlanTier.ENTERPRISE] == 50.0

    def test_business_tier_multiplier(self) -> None:
        # BUSINESS tier: 5 * 10 = 50 requests
        limit, window = find_rate_limit(
            "POST", "/api/v1/auth/login", PlanTier.BUSINESS
        )
        assert limit == 50
        assert window == 300


# ---------------------------------------------------------------------------
# Tests -- Sliding Window Limiter
# ---------------------------------------------------------------------------


class TestSlidingWindowLimiter:
    @pytest.mark.asyncio
    async def test_first_request_allowed(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        result = await limiter.check("test:1", limit=10, window_seconds=60)
        assert result.allowed is True
        assert result.limit == 10
        assert result.remaining == 9
        assert result.retry_after is None

    @pytest.mark.asyncio
    async def test_requests_up_to_limit_allowed(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        for i in range(10):
            result = await limiter.check("test:2", limit=10, window_seconds=60)
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_exceeding_limit_denied(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill to limit
        for _ in range(10):
            await limiter.check("test:3", limit=10, window_seconds=60)

        # Next request should be denied
        result = await limiter.check("test:3", limit=10, window_seconds=60)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_retry_after_header(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill to limit
        for _ in range(5):
            await limiter.check("test:retry", limit=5, window_seconds=60)

        # Exceed limit
        result = await limiter.check("test:retry", limit=5, window_seconds=60)
        assert result.allowed is False
        assert result.retry_after is not None
        # Should be close to window_seconds (60) but may be slightly less
        assert 1 <= result.retry_after <= 60

    @pytest.mark.asyncio
    async def test_different_keys_independent(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill key A
        for _ in range(10):
            await limiter.check("test:A", limit=10, window_seconds=60)

        # Key A exhausted
        result_a = await limiter.check("test:A", limit=10, window_seconds=60)
        assert result_a.allowed is False

        # Key B still has capacity
        result_b = await limiter.check("test:B", limit=10, window_seconds=60)
        assert result_b.allowed is True

    @pytest.mark.asyncio
    async def test_denied_request_not_counted(
        self, fake_redis: FakeRedis, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill to limit
        for _ in range(10):
            await limiter.check("test:rollback", limit=10, window_seconds=60)

        # This should be denied and rolled back
        result = await limiter.check("test:rollback", limit=10, window_seconds=60)
        assert result.allowed is False

        # Should still have exactly 10 entries
        key = "rl:test:rollback"
        assert len(fake_redis._store.get(key, [])) == 10

    @pytest.mark.asyncio
    async def test_window_expiration(
        self, fake_redis: FakeRedis, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill to limit
        for _ in range(10):
            await limiter.check("test:expire", limit=10, window_seconds=60)

        # Manually age all entries beyond the window
        key = "rl:test:expire"
        old_time = time.time() - 70  # 10 seconds past window
        fake_redis._store[key] = [(old_time, f"old-{i}") for i in range(10)]

        # Next request should be allowed (old entries pruned)
        result = await limiter.check("test:expire", limit=10, window_seconds=60)
        assert result.allowed is True
        assert result.remaining == 9


# ---------------------------------------------------------------------------
# Tests -- Request-Based Rate Limiting
# ---------------------------------------------------------------------------


class TestRequestBasedRateLimiting:
    @pytest.mark.asyncio
    async def test_check_request_uses_endpoint_config(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Auth endpoint should have strict limits
        result = await limiter.check_request(
            identifier="user:123",
            method="POST",
            path="/api/v1/auth/login",
            tier=PlanTier.FREE,
        )
        assert result.allowed is True
        assert result.limit == 5  # Configured for auth login

    @pytest.mark.asyncio
    async def test_check_request_applies_tier_multiplier(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # PRO tier should get 5x multiplier
        result = await limiter.check_request(
            identifier="user:pro",
            method="POST",
            path="/api/v1/auth/login",
            tier=PlanTier.PRO,
        )
        assert result.limit == 25  # 5 * 5x

    @pytest.mark.asyncio
    async def test_check_request_different_endpoints_separate_limits(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Fill auth endpoint
        for _ in range(5):
            await limiter.check_request(
                identifier="user:456",
                method="POST",
                path="/api/v1/auth/login",
                tier=PlanTier.FREE,
            )

        # Auth endpoint exhausted
        result_auth = await limiter.check_request(
            identifier="user:456",
            method="POST",
            path="/api/v1/auth/login",
            tier=PlanTier.FREE,
        )
        assert result_auth.allowed is False

        # Different endpoint should still have capacity
        result_other = await limiter.check_request(
            identifier="user:456",
            method="GET",
            path="/api/v1/books/list",
            tier=PlanTier.FREE,
        )
        assert result_other.allowed is True

    @pytest.mark.asyncio
    async def test_check_request_wildcard_matching(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Should match "POST /api/v1/ai/writing/*" with limit 20
        result = await limiter.check_request(
            identifier="user:ai",
            method="POST",
            path="/api/v1/ai/writing/generate-chapter",
            tier=PlanTier.FREE,
        )
        assert result.limit == 20


# ---------------------------------------------------------------------------
# Tests -- Reset Timestamp
# ---------------------------------------------------------------------------


class TestResetTimestamp:
    @pytest.mark.asyncio
    async def test_reset_is_future_timestamp(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        result = await limiter.check("test:reset", limit=10, window_seconds=60)
        now = int(time.time())
        assert result.reset_at > now
        assert result.reset_at <= now + 60 + 2  # Allow 2s margin

    @pytest.mark.asyncio
    async def test_reset_matches_window(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        result = await limiter.check("test:window", limit=10, window_seconds=120)
        now = int(time.time())
        # Reset should be approximately now + window
        assert 118 <= result.reset_at - now <= 122


# ---------------------------------------------------------------------------
# Tests -- Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    @pytest.mark.asyncio
    async def test_get_rate_limiter_returns_singleton(self) -> None:
        await reset_limiter()
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_reset_limiter_clears_singleton(self) -> None:
        limiter1 = get_rate_limiter()
        await reset_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is not limiter2


# ---------------------------------------------------------------------------
# Tests -- Close Connection
# ---------------------------------------------------------------------------


class TestCloseConnection:
    @pytest.mark.asyncio
    async def test_close_clears_redis(
        self, fake_redis: FakeRedis, limiter: SlidingWindowRateLimiter
    ) -> None:
        assert limiter._redis is not None
        await limiter.close()
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_close_when_already_none(self) -> None:
        limiter = SlidingWindowRateLimiter(redis_client=None)
        await limiter.close()  # Should not raise


# ---------------------------------------------------------------------------
# Tests -- Concurrent Requests
# ---------------------------------------------------------------------------


class TestConcurrentRequests:
    @pytest.mark.asyncio
    async def test_concurrent_requests_counted_correctly(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        import asyncio

        tasks = [limiter.check("test:concurrent", 20, 60) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should be allowed
        for result in results:
            assert result.allowed is True

        # Final check should show 10 used
        final = await limiter.check("test:concurrent", 20, 60)
        assert final.remaining == 9  # 20 - 11

    @pytest.mark.asyncio
    async def test_concurrent_at_boundary(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        import asyncio

        # Fill to near limit
        for _ in range(8):
            await limiter.check("test:boundary", 10, 60)

        # Fire 5 concurrent (2 should be allowed, 3 denied)
        tasks = [limiter.check("test:boundary", 10, 60) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        allowed_count = sum(1 for r in results if r.allowed)
        denied_count = sum(1 for r in results if not r.allowed)

        assert allowed_count == 2
        assert denied_count == 3


# ---------------------------------------------------------------------------
# Tests -- Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_zero_limit(self, limiter: SlidingWindowRateLimiter) -> None:
        # Even with limit 0, first request counts
        result = await limiter.check("test:zero", limit=0, window_seconds=60)
        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_very_large_limit(self, limiter: SlidingWindowRateLimiter) -> None:
        result = await limiter.check("test:large", limit=1000000, window_seconds=60)
        assert result.allowed is True
        assert result.remaining == 999999

    @pytest.mark.asyncio
    async def test_short_window(self, limiter: SlidingWindowRateLimiter) -> None:
        # 1 second window
        result = await limiter.check("test:short", limit=5, window_seconds=1)
        assert result.allowed is True
        assert result.reset_at <= int(time.time()) + 2

    @pytest.mark.asyncio
    async def test_remaining_never_negative(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # Exceed limit significantly
        for _ in range(20):
            result = await limiter.check("test:negative", limit=5, window_seconds=60)

        # Remaining should be 0, not negative
        assert result.remaining == 0


# ---------------------------------------------------------------------------
# Tests -- Method-Path Combinations
# ---------------------------------------------------------------------------


class TestMethodPathCombinations:
    @pytest.mark.asyncio
    async def test_same_path_different_methods_separate_limits(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        # POST /api/v1/books
        for _ in range(30):
            await limiter.check_request(
                "user:method",
                method="POST",
                path="/api/v1/books",
                tier=PlanTier.FREE,
            )

        # POST exhausted
        result_post = await limiter.check_request(
            "user:method", method="POST", path="/api/v1/books", tier=PlanTier.FREE
        )
        assert result_post.allowed is False

        # GET should still work (different limit)
        result_get = await limiter.check_request(
            "user:method", method="GET", path="/api/v1/books", tier=PlanTier.FREE
        )
        assert result_get.allowed is True


# ---------------------------------------------------------------------------
# Tests -- All Tiers
# ---------------------------------------------------------------------------


class TestAllTiers:
    @pytest.mark.asyncio
    async def test_all_tier_multipliers(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        base_limit = 10

        tiers_and_expected = [
            (PlanTier.FREE, 10),  # 1x
            (PlanTier.STARTER, 20),  # 2x
            (PlanTier.PRO, 50),  # 5x
            (PlanTier.BUSINESS, 100),  # 10x
            (PlanTier.ENTERPRISE, 500),  # 50x
        ]

        for tier, expected_limit in tiers_and_expected:
            # Use find_rate_limit with a simple pattern
            limit, _ = find_rate_limit("POST", "/test/endpoint", tier)

            # Since no match, should use default (60) with multiplier
            if tier == PlanTier.FREE:
                assert limit == 60
            elif tier == PlanTier.STARTER:
                assert limit == 120
            elif tier == PlanTier.PRO:
                assert limit == 300
            elif tier == PlanTier.BUSINESS:
                assert limit == 600
            elif tier == PlanTier.ENTERPRISE:
                assert limit == 3000
