"""
Unit tests for the API gateway middleware stack.

Tests cover CorrelationIDMiddleware, RequestTimingMiddleware,
SecurityHeadersMiddleware, and RequestLoggingMiddleware.
"""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.responses import JSONResponse

from app.core.middleware import (
    CorrelationIDMiddleware,
    RequestLoggingMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)

# ---------------------------------------------------------------------------
# Helper -- minimal FastAPI app with the middleware under test
# ---------------------------------------------------------------------------


def _make_app(*middleware_classes, custom_headers=None) -> FastAPI:
    """Create a tiny FastAPI app with the listed middleware classes."""
    test_app = FastAPI()

    @test_app.get("/ping")
    async def ping(request: Request):
        # Expose correlation_id if present so tests can verify it.
        cid = getattr(request.state, "correlation_id", None)
        return JSONResponse({"correlation_id": cid})

    for cls in middleware_classes:
        if cls is SecurityHeadersMiddleware and custom_headers is not None:
            test_app.add_middleware(cls, headers=custom_headers)
        else:
            test_app.add_middleware(cls)

    return test_app


# ---------------------------------------------------------------------------
# CorrelationIDMiddleware
# ---------------------------------------------------------------------------


class TestCorrelationIDMiddleware:
    @pytest.mark.asyncio
    async def test_generates_id_when_absent(self) -> None:
        app = _make_app(CorrelationIDMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) == 36  # UUID-4

    @pytest.mark.asyncio
    async def test_propagates_existing_id(self) -> None:
        app = _make_app(CorrelationIDMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping", headers={"X-Request-ID": "my-custom-id"})
        assert resp.headers["X-Request-ID"] == "my-custom-id"

    @pytest.mark.asyncio
    async def test_stores_on_request_state(self) -> None:
        app = _make_app(CorrelationIDMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping", headers={"X-Request-ID": "state-check"})
        body = resp.json()
        assert body["correlation_id"] == "state-check"


# ---------------------------------------------------------------------------
# RequestTimingMiddleware
# ---------------------------------------------------------------------------


class TestRequestTimingMiddleware:
    @pytest.mark.asyncio
    async def test_adds_response_time_header(self) -> None:
        app = _make_app(RequestTimingMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")
        assert "X-Response-Time" in resp.headers
        assert resp.headers["X-Response-Time"].endswith("ms")

    @pytest.mark.asyncio
    async def test_response_time_is_numeric(self) -> None:
        app = _make_app(RequestTimingMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")
        raw = resp.headers["X-Response-Time"].replace("ms", "")
        assert float(raw) >= 0


# ---------------------------------------------------------------------------
# SecurityHeadersMiddleware
# ---------------------------------------------------------------------------


class TestSecurityHeadersMiddleware:
    @pytest.mark.asyncio
    async def test_default_security_headers(self) -> None:
        app = _make_app(SecurityHeadersMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert "Strict-Transport-Security" in resp.headers
        assert "X-Frame-Options" in resp.headers
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "X-Content-Type-Options" in resp.headers
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in resp.headers
        assert "Referrer-Policy" in resp.headers
        assert "Permissions-Policy" in resp.headers

    @pytest.mark.asyncio
    async def test_custom_security_headers(self) -> None:
        custom = {"X-Custom-Header": "hello"}
        app = _make_app(SecurityHeadersMiddleware, custom_headers=custom)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.headers.get("X-Custom-Header") == "hello"
        # Default headers should not be present
        assert "X-Frame-Options" not in resp.headers


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware
# ---------------------------------------------------------------------------


class TestRequestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_logs_request(self, caplog: pytest.LogCaptureFixture) -> None:
        app = _make_app(RequestLoggingMiddleware)
        transport = ASGITransport(app=app)

        with caplog.at_level(logging.INFO, logger="spf.middleware"):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/ping")

        assert resp.status_code == 200
        assert any("request_completed" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_log_record_has_extra_fields(self, caplog: pytest.LogCaptureFixture) -> None:
        app = _make_app(RequestLoggingMiddleware)
        transport = ASGITransport(app=app)

        with caplog.at_level(logging.INFO, logger="spf.middleware"):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/ping")

        records = [r for r in caplog.records if r.message == "request_completed"]
        assert len(records) >= 1
        rec = records[0]
        assert hasattr(rec, "method")
        assert rec.method == "GET"  # type: ignore[attr-defined]
        assert hasattr(rec, "path")
        assert hasattr(rec, "status_code")
        assert hasattr(rec, "duration_ms")
