"""Unit tests for core middleware: correlation IDs, request logging, timing,
and rate limiting.

These tests exercise the middleware in isolation using a minimal FastAPI app
and the HTTPX async test client.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.core.logging import correlation_id_ctx
from app.core.middleware import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    TimingMiddleware,
)
from app.core.rate_limit import (
    DEFAULT_RATE_LIMIT,
    TIER_RATE_LIMITS,
    RateLimitMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers -- tiny test app factory
# ---------------------------------------------------------------------------

def _build_app(
    *,
    correlation: bool = True,
    logging: bool = False,
    timing: bool = False,
    rate_limit: bool = False,
    redis: object | None = None,
) -> FastAPI:
    """Build a minimal FastAPI app with selected middleware."""
    app = FastAPI()

    if rate_limit:
        app.add_middleware(RateLimitMiddleware, redis=redis)
    if timing:
        app.add_middleware(TimingMiddleware)
    if logging:
        app.add_middleware(RequestLoggingMiddleware)
    if correlation:
        app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    @app.get("/cid")
    async def cid():
        """Return the current correlation ID from the context var."""
        return {"correlation_id": correlation_id_ctx.get()}

    @app.get("/slow")
    async def slow():
        await asyncio.sleep(0.05)
        return {"ok": True}

    return app


async def _make_client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ===================================================================
# Correlation ID Middleware
# ===================================================================

class TestCorrelationIdMiddleware:

    @pytest.mark.asyncio
    async def test_generates_correlation_id_when_absent(self):
        app = _build_app(correlation=True)
        async with await _make_client(app) as client:
            resp = await client.get("/ping")
            assert resp.status_code == 200
            cid = resp.headers.get(CORRELATION_ID_HEADER)
            assert cid is not None
            # UUID-4 has 36 chars with dashes
            assert len(cid) == 36

    @pytest.mark.asyncio
    async def test_propagates_existing_correlation_id(self):
        app = _build_app(correlation=True)
        my_cid = "my-custom-correlation-id-12345"
        async with await _make_client(app) as client:
            resp = await client.get("/ping", headers={CORRELATION_ID_HEADER: my_cid})
            assert resp.headers.get(CORRELATION_ID_HEADER) == my_cid

    @pytest.mark.asyncio
    async def test_correlation_id_available_in_context(self):
        app = _build_app(correlation=True)
        my_cid = "context-test-cid"
        async with await _make_client(app) as client:
            resp = await client.get("/cid", headers={CORRELATION_ID_HEADER: my_cid})
            assert resp.json()["correlation_id"] == my_cid

    @pytest.mark.asyncio
    async def test_different_requests_get_different_ids(self):
        app = _build_app(correlation=True)
        async with await _make_client(app) as client:
            r1 = await client.get("/ping")
            r2 = await client.get("/ping")
            cid1 = r1.headers.get(CORRELATION_ID_HEADER)
            cid2 = r2.headers.get(CORRELATION_ID_HEADER)
            assert cid1 != cid2


# ===================================================================
# Timing Middleware
# ===================================================================

class TestTimingMiddleware:

    @pytest.mark.asyncio
    async def test_adds_process_time_header(self):
        app = _build_app(timing=True, correlation=False)
        async with await _make_client(app) as client:
            resp = await client.get("/ping")
            assert resp.status_code == 200
            header_val = resp.headers.get("X-Process-Time-Ms")
            assert header_val is not None
            assert float(header_val) >= 0

    @pytest.mark.asyncio
    async def test_timing_reflects_actual_duration(self):
        app = _build_app(timing=True, correlation=False)
        async with await _make_client(app) as client:
            resp = await client.get("/slow")
            duration = float(resp.headers["X-Process-Time-Ms"])
            # /slow sleeps 50ms, allow margin
            assert duration >= 40


# ===================================================================
# Request Logging Middleware
# ===================================================================

class TestRequestLoggingMiddleware:

    @pytest.mark.asyncio
    async def test_logging_middleware_logs_request(self):
        app = _build_app(logging=True, correlation=False)
        with patch("app.core.middleware.logger") as mock_logger:
            async with await _make_client(app) as client:
                resp = await client.get("/ping")
                assert resp.status_code == 200
            # The logger should have been called at least once
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args
            # The format string includes method and path
            assert "GET" in str(call_args)
            assert "/ping" in str(call_args)


# ===================================================================
# Rate Limit Middleware
# ===================================================================

class TestRateLimitMiddleware:

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, mock_redis):
        """Rate-limit headers should appear on every response."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)
        async with await _make_client(app) as client:
            resp = await client.get("/ping")
            assert resp.status_code == 200
            assert "X-RateLimit-Limit" in resp.headers
            assert "X-RateLimit-Remaining" in resp.headers
            assert "X-RateLimit-Reset" in resp.headers

    @pytest.mark.asyncio
    async def test_default_limit_is_free_tier(self, mock_redis):
        """Without X-Plan-Tier, limit should be the free tier limit."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)
        async with await _make_client(app) as client:
            resp = await client.get("/ping")
            assert int(resp.headers["X-RateLimit-Limit"]) == TIER_RATE_LIMITS["free"]

    @pytest.mark.asyncio
    async def test_pro_tier_gets_higher_limit(self, mock_redis):
        """Pro tier should report a 300/min limit."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)
        async with await _make_client(app) as client:
            resp = await client.get("/ping", headers={"X-Plan-Tier": "pro"})
            assert int(resp.headers["X-RateLimit-Limit"]) == TIER_RATE_LIMITS["pro"]

    @pytest.mark.asyncio
    async def test_enterprise_tier_gets_highest_limit(self, mock_redis):
        """Enterprise tier should report a 1000/min limit."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)
        async with await _make_client(app) as client:
            resp = await client.get("/ping", headers={"X-Plan-Tier": "enterprise"})
            assert int(resp.headers["X-RateLimit-Limit"]) == TIER_RATE_LIMITS["enterprise"]

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_rate_limit(self, mock_redis):
        """The /health endpoint should not be rate-limited."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        async with await _make_client(app) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            # No rate-limit headers on /health
            assert "X-RateLimit-Limit" not in resp.headers

    @pytest.mark.asyncio
    async def test_fails_open_when_redis_unavailable(self):
        """If Redis is unreachable, requests should still go through."""
        # Pass a Redis that will fail to connect
        broken_redis = AsyncMock()
        broken_redis.ping = AsyncMock(side_effect=ConnectionError("nope"))

        app = _build_app(rate_limit=True, correlation=False, redis=None)

        # Patch _get_redis to return None (simulating Redis down)
        with patch.object(RateLimitMiddleware, "_get_redis", return_value=None):
            async with await _make_client(app) as client:
                resp = await client.get("/ping")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_identifies_by_user_id_header(self, mock_redis):
        """When X-User-ID is present, the key should be user-based."""
        app = _build_app(rate_limit=True, correlation=False, redis=mock_redis)
        async with await _make_client(app) as client:
            resp = await client.get(
                "/ping",
                headers={"X-User-ID": "user-123", "X-Plan-Tier": "free"},
            )
            assert resp.status_code == 200
            assert int(resp.headers["X-RateLimit-Limit"]) == TIER_RATE_LIMITS["free"]

    @pytest.mark.asyncio
    async def test_tier_limit_values(self):
        """Verify the tier constants match the spec."""
        assert TIER_RATE_LIMITS["free"] == 60
        assert TIER_RATE_LIMITS["starter"] == 120
        assert TIER_RATE_LIMITS["pro"] == 300
        assert TIER_RATE_LIMITS["business"] == 600
        assert TIER_RATE_LIMITS["enterprise"] == 1000


# ===================================================================
# Logging module -- correlation ID context
# ===================================================================

class TestCorrelationIdContext:

    def test_default_value_is_none(self):
        assert correlation_id_ctx.get() is None

    def test_set_and_get(self):
        token = correlation_id_ctx.set("test-cid-123")
        try:
            assert correlation_id_ctx.get() == "test-cid-123"
        finally:
            correlation_id_ctx.reset(token)

    def test_reset_restores_default(self):
        token = correlation_id_ctx.set("temp-cid")
        correlation_id_ctx.reset(token)
        assert correlation_id_ctx.get() is None
