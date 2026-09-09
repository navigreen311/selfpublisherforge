"""
Tests for core infrastructure modules.

Covers: security (JWT + password hashing), exceptions, pagination,
error_handler, middleware, logging sanitization, and versioning.
"""
from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.responses import JSONResponse

from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.logging import sanitize
from app.core.pagination import CursorParams, PaginatedResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.versioning import APIVersion, extract_version

# ---------------------------------------------------------------------------
# 1. Security — JWT token creation and validation
# ---------------------------------------------------------------------------


class TestJWTTokens:
    """Test JWT access/refresh token creation and decoding."""

    def test_create_and_decode_access_token(self):
        """An access token round-trips through create -> decode."""
        user_id = str(uuid4())
        token = create_access_token({"sub": user_id, "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_and_decode_refresh_token(self):
        """A refresh token round-trips and has type=refresh."""
        user_id = str(uuid4())
        token = create_refresh_token({"sub": user_id})
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_access_token_custom_expiry(self):
        """Custom expiration delta is respected."""
        token = create_access_token(
            {"sub": "user1"}, expires_delta=timedelta(minutes=5)
        )
        payload = decode_token(token)
        assert payload["sub"] == "user1"

    def test_decode_invalid_token_raises(self):
        """Decoding a garbage token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        """A token with a modified payload fails validation."""
        token = create_access_token({"sub": "user1"})
        # Tamper with the payload section
        parts = token.split(".")
        parts[1] = parts[1][::-1]  # reverse the payload
        tampered = ".".join(parts)
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(tampered)


# ---------------------------------------------------------------------------
# 2. Security — password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    def test_hash_and_verify(self):
        """A hashed password verifies against the original."""
        raw = "SuperSecret123!"
        hashed = hash_password(raw)
        assert hashed != raw
        assert verify_password(raw, hashed)

    def test_wrong_password_fails(self):
        """A wrong password does not verify."""
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_hash_is_unique(self):
        """Two calls to hash produce different outputs (salt)."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ---------------------------------------------------------------------------
# 3. Custom exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    """Test the custom AppException hierarchy."""

    def test_app_exception_fields(self):
        exc = AppException(status_code=400, code="BAD", message="bad request")
        assert exc.status_code == 400
        assert exc.code == "BAD"
        assert exc.message == "bad request"
        assert exc.details == []

    def test_app_exception_with_details(self):
        details = [{"field": "name", "error": "required"}]
        exc = AppException(status_code=422, code="VAL", message="fail", details=details)
        assert exc.details == details

    def test_not_found_error(self):
        exc = NotFoundError("Book")
        assert exc.status_code == 404
        assert exc.code == "NOT_FOUND"
        assert "Book" in exc.message

    def test_unauthorized_error(self):
        exc = UnauthorizedError()
        assert exc.status_code == 401

    def test_forbidden_error(self):
        exc = ForbiddenError()
        assert exc.status_code == 403

    def test_conflict_error(self):
        exc = ConflictError("Duplicate entry")
        assert exc.status_code == 409
        assert exc.message == "Duplicate entry"

    def test_validation_error(self):
        exc = ValidationError("bad input", details=[{"field": "email"}])
        assert exc.status_code == 422
        assert len(exc.details) == 1


# ---------------------------------------------------------------------------
# 4. Pagination helpers
# ---------------------------------------------------------------------------


class TestPagination:
    """Test pagination models and the FastAPI dependency."""

    def test_cursor_params_defaults(self):
        params = CursorParams()
        assert params.cursor is None
        assert params.limit == 20

    def test_cursor_params_custom(self):
        params = CursorParams(cursor="abc123", limit=50)
        assert params.cursor == "abc123"
        assert params.limit == 50

    def test_paginated_response(self):
        resp = PaginatedResponse[str](
            items=["a", "b"],
            next_cursor="next",
            has_more=True,
            total_count=10,
        )
        assert resp.items == ["a", "b"]
        assert resp.has_more is True
        assert resp.total_count == 10

    def test_paginated_response_empty(self):
        resp = PaginatedResponse[int](items=[])
        assert resp.items == []
        assert resp.has_more is False
        assert resp.next_cursor is None


# ---------------------------------------------------------------------------
# 5. Error handler — structured error responses
# ---------------------------------------------------------------------------


class TestErrorHandler:
    """Test the global error handlers produce correct JSON envelopes."""

    @pytest.fixture
    def app_with_handlers(self):
        """Build a minimal app with error handlers registered."""
        from app.core.error_handler import register_error_handlers

        test_app = FastAPI()
        register_error_handlers(test_app)

        @test_app.get("/raise-app-exc")
        async def _raise_app():
            raise AppException(status_code=400, code="TEST_ERROR", message="test message")

        @test_app.get("/raise-500")
        async def _raise_500():
            raise RuntimeError("boom")

        return test_app

    @pytest.mark.asyncio
    async def test_app_exception_returns_structured_json(self, app_with_handlers):
        transport = ASGITransport(app=app_with_handlers, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/raise-app-exc")
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"]["code"] == "TEST_ERROR"
        assert body["error"]["message"] == "test message"
        assert "request_id" in body["error"]

    @pytest.mark.asyncio
    async def test_internal_error_returns_500(self, app_with_handlers):
        transport = ASGITransport(app=app_with_handlers, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/raise-500")
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"

    @pytest.mark.asyncio
    async def test_404_returns_not_found(self, app_with_handlers):
        transport = ASGITransport(app=app_with_handlers, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/nonexistent-path")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 6. Middleware — correlation ID and timing
# ---------------------------------------------------------------------------


class TestMiddleware:
    """Test core middleware components."""

    @pytest.fixture
    def app_with_middleware(self):
        from app.core.middleware import (
            CorrelationIDMiddleware,
            RequestTimingMiddleware,
            SecurityHeadersMiddleware,
        )

        test_app = FastAPI()

        @test_app.get("/ping")
        async def ping(request: Request):
            cid = getattr(request.state, "correlation_id", None)
            return JSONResponse({"correlation_id": cid})

        # Order matters: outer middleware listed first
        test_app.add_middleware(SecurityHeadersMiddleware)
        test_app.add_middleware(RequestTimingMiddleware)
        test_app.add_middleware(CorrelationIDMiddleware)

        return test_app

    @pytest.mark.asyncio
    async def test_correlation_id_generated(self, app_with_middleware):
        transport = ASGITransport(app=app_with_middleware)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/ping")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        body = resp.json()
        assert body["correlation_id"] == resp.headers["X-Request-ID"]

    @pytest.mark.asyncio
    async def test_correlation_id_propagated(self, app_with_middleware):
        transport = ASGITransport(app=app_with_middleware)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/ping", headers={"X-Request-ID": "my-custom-id"})
        assert resp.headers["X-Request-ID"] == "my-custom-id"
        body = resp.json()
        assert body["correlation_id"] == "my-custom-id"

    @pytest.mark.asyncio
    async def test_timing_header_present(self, app_with_middleware):
        transport = ASGITransport(app=app_with_middleware)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/ping")
        assert "X-Response-Time" in resp.headers
        assert resp.headers["X-Response-Time"].endswith("ms")

    @pytest.mark.asyncio
    async def test_security_headers_present(self, app_with_middleware):
        transport = ASGITransport(app=app_with_middleware)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/ping")
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert "Strict-Transport-Security" in resp.headers


# ---------------------------------------------------------------------------
# 7. Logging — sanitization of sensitive data
# ---------------------------------------------------------------------------


class TestLoggingSanitize:
    """Test the sanitize function strips sensitive keys."""

    def test_sanitize_removes_password(self):
        data = {"username": "alice", "password": "secret123"}
        result = sanitize(data)
        assert result["username"] == "alice"
        assert result["password"] == "***REDACTED***"

    def test_sanitize_removes_nested_api_key(self):
        data = {"config": {"api_key": "sk-xxx", "name": "test"}}
        result = sanitize(data)
        assert result["config"]["api_key"] == "***REDACTED***"
        assert result["config"]["name"] == "test"

    def test_sanitize_handles_lists(self):
        data = [{"token": "abc"}, {"safe": "value"}]
        result = sanitize(data)
        assert result[0]["token"] == "***REDACTED***"
        assert result[1]["safe"] == "value"

    def test_sanitize_leaves_scalars_untouched(self):
        assert sanitize(42) == 42
        assert sanitize("hello") == "hello"
        assert sanitize(None) is None

    def test_sanitize_depth_guard(self):
        """Deeply nested structures don't cause infinite recursion."""
        deep = {"a": "b"}
        for _ in range(30):
            deep = {"nested": deep}
        result = sanitize(deep)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 8. Versioning — URL extraction
# ---------------------------------------------------------------------------


class TestVersioning:
    """Test API version extraction from URL paths."""

    def test_extract_v1(self):
        assert extract_version("/api/v1/books") == APIVersion.V1

    def test_extract_v2(self):
        assert extract_version("/api/v2/books") == APIVersion.V2

    def test_extract_no_version(self):
        assert extract_version("/health") is None

    def test_extract_invalid_version(self):
        assert extract_version("/api/v99/books") is None
