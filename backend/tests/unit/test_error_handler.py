"""
Unit tests for the global error handlers.

Tests exercise each handler function directly with mock requests,
as well as the ``register_error_handlers`` integration.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_handler import (
    _error_envelope,
    _get_request_id,
    app_exception_handler,
    internal_error_handler,
    not_found_handler,
    register_error_handlers,
    validation_exception_handler,
)
from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(correlation_id: str = "test-req-id-001") -> MagicMock:
    """Build a mock ``Request`` with a correlation_id on state."""
    request = MagicMock()
    request.state.correlation_id = correlation_id
    return request


def _make_request_without_correlation() -> MagicMock:
    """Build a mock ``Request`` where correlation_id is absent from state."""
    request = MagicMock(spec=[])
    request.state = MagicMock(spec=[])  # no correlation_id attribute
    return request


# ---------------------------------------------------------------------------
# Tests -- _get_request_id helper
# ---------------------------------------------------------------------------


class TestGetRequestId:
    def test_returns_correlation_id_when_present(self) -> None:
        request = _make_request("abc-123")
        assert _get_request_id(request) == "abc-123"

    def test_returns_unknown_when_absent(self) -> None:
        request = _make_request_without_correlation()
        result = _get_request_id(request)
        assert result == "unknown"


# ---------------------------------------------------------------------------
# Tests -- _error_envelope builder
# ---------------------------------------------------------------------------


class TestErrorEnvelope:
    def test_basic_envelope_structure(self) -> None:
        envelope = _error_envelope(
            code="TEST_ERROR",
            message="Something went wrong",
            request_id="req-001",
        )
        assert "error" in envelope
        assert envelope["error"]["code"] == "TEST_ERROR"
        assert envelope["error"]["message"] == "Something went wrong"
        assert envelope["error"]["request_id"] == "req-001"

    def test_envelope_without_details(self) -> None:
        """When details is None, the 'details' key should be absent."""
        envelope = _error_envelope(
            code="NO_DETAILS",
            message="No details here",
            request_id="req-002",
        )
        assert "details" not in envelope["error"]

    def test_envelope_with_empty_details(self) -> None:
        """When details is an empty list, the 'details' key should be absent (falsy)."""
        envelope = _error_envelope(
            code="EMPTY_DETAILS",
            message="Empty details",
            request_id="req-003",
            details=[],
        )
        assert "details" not in envelope["error"]

    def test_envelope_with_details(self) -> None:
        details = [{"field": "name", "message": "required"}]
        envelope = _error_envelope(
            code="VALIDATION_ERROR",
            message="Validation failed",
            request_id="req-004",
            details=details,
        )
        assert envelope["error"]["details"] == details

    def test_envelope_follows_error_envelope_schema(self) -> None:
        """The envelope must have exactly the expected structure."""
        envelope = _error_envelope(
            code="SCHEMA_CHECK",
            message="Checking schema",
            request_id="req-005",
            details=[{"info": "test"}],
        )
        # Top-level must have only "error" key
        assert set(envelope.keys()) == {"error"}
        # Error must have code, message, request_id, and details
        error_keys = set(envelope["error"].keys())
        assert error_keys == {"code", "message", "request_id", "details"}


# ---------------------------------------------------------------------------
# Tests -- AppException handler
# ---------------------------------------------------------------------------


class TestAppExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_correct_status_code(self) -> None:
        request = _make_request()
        exc = AppException(status_code=400, code="BAD_REQUEST", message="Bad input")
        response = await app_exception_handler(request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_correct_body(self) -> None:
        request = _make_request("req-body-test")
        exc = AppException(status_code=400, code="BAD_REQUEST", message="Bad input")
        response = await app_exception_handler(request, exc)
        body = response.body.decode()
        import json

        data = json.loads(body)
        assert data["error"]["code"] == "BAD_REQUEST"
        assert data["error"]["message"] == "Bad input"
        assert data["error"]["request_id"] == "req-body-test"

    @pytest.mark.asyncio
    async def test_includes_details_when_present(self) -> None:
        request = _make_request()
        details = [{"field": "email", "issue": "invalid format"}]
        exc = AppException(
            status_code=422, code="VALIDATION_ERROR", message="Invalid", details=details
        )
        response = await app_exception_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["details"] == details

    @pytest.mark.asyncio
    async def test_response_is_json(self) -> None:
        """Error responses must be JSON, never HTML."""
        request = _make_request()
        exc = AppException(status_code=400, code="BAD_REQUEST", message="Oops")
        response = await app_exception_handler(request, exc)
        content_type = dict(response.headers).get("content-type", "")
        assert "application/json" in content_type

    @pytest.mark.asyncio
    async def test_includes_request_id(self) -> None:
        request = _make_request("correlation-xyz")
        exc = AppException(status_code=500, code="ERR", message="fail")
        response = await app_exception_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["request_id"] == "correlation-xyz"


# ---------------------------------------------------------------------------
# Tests -- ValidationError handler (RequestValidationError)
# ---------------------------------------------------------------------------


class TestValidationExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_422(self) -> None:
        request = _make_request()
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "title"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )
        response = await validation_exception_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_formats_field_errors_properly(self) -> None:
        request = _make_request("req-val-001")
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "title"),
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ("body", "pages"),
                    "msg": "value is not a valid integer",
                    "type": "type_error.integer",
                },
            ]
        )
        response = await validation_exception_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Request validation failed."
        assert data["error"]["request_id"] == "req-val-001"

        details = data["error"]["details"]
        assert len(details) == 2
        assert details[0]["field"] == "body -> title"
        assert details[0]["message"] == "field required"
        assert details[0]["type"] == "value_error.missing"
        assert details[1]["field"] == "body -> pages"

    @pytest.mark.asyncio
    async def test_handles_empty_loc(self) -> None:
        """When loc is empty, field should be an empty string."""
        request = _make_request()
        exc = RequestValidationError(
            errors=[{"loc": (), "msg": "general error", "type": "value_error"}]
        )
        response = await validation_exception_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["details"][0]["field"] == ""

    @pytest.mark.asyncio
    async def test_response_is_json_not_html(self) -> None:
        """Validation errors must return JSON, not HTML (especially for API routes)."""
        request = _make_request()
        exc = RequestValidationError(
            errors=[{"loc": ("query", "page"), "msg": "not int", "type": "type_error"}]
        )
        response = await validation_exception_handler(request, exc)
        content_type = dict(response.headers).get("content-type", "")
        assert "application/json" in content_type
        # Ensure no HTML
        body = response.body.decode()
        assert "<html" not in body.lower()


# ---------------------------------------------------------------------------
# Tests -- NotFoundError (custom exception) returns 404
# ---------------------------------------------------------------------------


class TestNotFoundError:
    def test_not_found_error_has_404_status(self) -> None:
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.code == "NOT_FOUND"

    def test_not_found_error_custom_resource(self) -> None:
        exc = NotFoundError(resource="Book")
        assert exc.message == "Book not found."

    def test_not_found_error_custom_detail(self) -> None:
        exc = NotFoundError(detail="Book with ID 123 was not found")
        assert exc.message == "Book with ID 123 was not found"

    @pytest.mark.asyncio
    async def test_not_found_handler_returns_404_json(self) -> None:
        """The not_found_handler returns a 404 JSON response for StarletteHTTPException."""
        request = _make_request("req-nf-001")
        exc = StarletteHTTPException(status_code=404, detail="Page not found")
        response = await not_found_handler(request, exc)
        assert response.status_code == 404
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Page not found"
        assert data["error"]["request_id"] == "req-nf-001"

    @pytest.mark.asyncio
    async def test_not_found_handler_default_message(self) -> None:
        """When the exception detail is falsy, the fallback default message is used."""
        request = _make_request()
        # Starlette auto-fills detail to "Not Found" when None/omitted,
        # so pass empty string to trigger the fallback branch.
        exc = StarletteHTTPException(status_code=404, detail="")
        response = await not_found_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["message"] == "The requested resource was not found."


# ---------------------------------------------------------------------------
# Tests -- UnauthorizedError returns 401
# ---------------------------------------------------------------------------


class TestUnauthorizedError:
    def test_unauthorized_error_has_401_status(self) -> None:
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.code == "UNAUTHORIZED"

    def test_unauthorized_error_default_message(self) -> None:
        exc = UnauthorizedError()
        assert exc.message == "Authentication required."

    def test_unauthorized_error_custom_message(self) -> None:
        exc = UnauthorizedError(message="Token expired")
        assert exc.message == "Token expired"

    @pytest.mark.asyncio
    async def test_unauthorized_via_app_exception_handler(self) -> None:
        """UnauthorizedError is an AppException, so the app_exception_handler processes it."""
        request = _make_request("req-auth-001")
        exc = UnauthorizedError(message="Invalid token")
        response = await app_exception_handler(request, exc)
        assert response.status_code == 401
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert data["error"]["request_id"] == "req-auth-001"


# ---------------------------------------------------------------------------
# Tests -- ForbiddenError returns 403
# ---------------------------------------------------------------------------


class TestForbiddenError:
    def test_forbidden_error_has_403_status(self) -> None:
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.code == "FORBIDDEN"

    def test_forbidden_error_default_message(self) -> None:
        exc = ForbiddenError()
        assert exc.message == "Insufficient permissions."

    def test_forbidden_error_custom_message(self) -> None:
        exc = ForbiddenError(message="Admin only")
        assert exc.message == "Admin only"

    @pytest.mark.asyncio
    async def test_forbidden_via_app_exception_handler(self) -> None:
        request = _make_request("req-403")
        exc = ForbiddenError(message="Not allowed")
        response = await app_exception_handler(request, exc)
        assert response.status_code == 403
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# Tests -- Internal Server Error handler
# ---------------------------------------------------------------------------


class TestInternalErrorHandler:
    @pytest.mark.asyncio
    async def test_returns_500(self) -> None:
        request = _make_request("req-500")
        exc = RuntimeError("Unexpected failure")
        response = await internal_error_handler(request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_sanitized_message_no_leak(self) -> None:
        """The 500 response should NOT leak the original exception message."""
        request = _make_request()
        exc = RuntimeError("database password is hunter2")
        response = await internal_error_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert "hunter2" not in data["error"]["message"]
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    @pytest.mark.asyncio
    async def test_includes_request_id_for_support(self) -> None:
        request = _make_request("support-ref-xyz")
        exc = Exception("boom")
        response = await internal_error_handler(request, exc)
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["request_id"] == "support-ref-xyz"

    @pytest.mark.asyncio
    async def test_response_is_json(self) -> None:
        request = _make_request()
        exc = Exception("boom")
        response = await internal_error_handler(request, exc)
        content_type = dict(response.headers).get("content-type", "")
        assert "application/json" in content_type

    @pytest.mark.asyncio
    async def test_logs_exception(self) -> None:
        """The handler should log the exception with logger.exception."""
        request = _make_request("log-test")
        exc = ValueError("something broke")
        with patch("app.core.error_handler.logger") as mock_logger:
            await internal_error_handler(request, exc)
            mock_logger.exception.assert_called_once()


# ---------------------------------------------------------------------------
# Tests -- ConflictError returns 409
# ---------------------------------------------------------------------------


class TestConflictError:
    def test_conflict_error_has_409_status(self) -> None:
        exc = ConflictError()
        assert exc.status_code == 409
        assert exc.code == "CONFLICT"

    def test_conflict_error_default_message(self) -> None:
        exc = ConflictError()
        assert exc.message == "Resource conflict."

    @pytest.mark.asyncio
    async def test_conflict_via_app_exception_handler(self) -> None:
        request = _make_request("req-409")
        exc = ConflictError(message="Duplicate entry")
        response = await app_exception_handler(request, exc)
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Tests -- Custom ValidationError (business logic, not Pydantic)
# ---------------------------------------------------------------------------


class TestCustomValidationError:
    def test_validation_error_has_422_status(self) -> None:
        exc = ValidationError()
        assert exc.status_code == 422
        assert exc.code == "VALIDATION_ERROR"

    def test_validation_error_with_details(self) -> None:
        details = [{"field": "isbn", "message": "Invalid ISBN format"}]
        exc = ValidationError(message="Invalid book data", details=details)
        assert exc.details == details
        assert exc.message == "Invalid book data"

    @pytest.mark.asyncio
    async def test_validation_error_via_app_exception_handler(self) -> None:
        request = _make_request("req-422-custom")
        details = [{"field": "price", "message": "must be positive"}]
        exc = ValidationError(message="Invalid input", details=details)
        response = await app_exception_handler(request, exc)
        assert response.status_code == 422
        import json

        data = json.loads(response.body.decode())
        assert data["error"]["details"] == details


# ---------------------------------------------------------------------------
# Tests -- register_error_handlers
# ---------------------------------------------------------------------------


class TestRegisterErrorHandlers:
    def test_registers_all_handlers(self) -> None:
        """register_error_handlers should call add_exception_handler for each type."""
        app = MagicMock(spec=FastAPI)
        register_error_handlers(app)
        assert app.add_exception_handler.call_count == 4

    def test_registers_app_exception(self) -> None:
        app = MagicMock(spec=FastAPI)
        register_error_handlers(app)
        call_args_list = app.add_exception_handler.call_args_list
        registered_types = [call.args[0] for call in call_args_list]
        assert AppException in registered_types

    def test_registers_validation_error(self) -> None:
        app = MagicMock(spec=FastAPI)
        register_error_handlers(app)
        call_args_list = app.add_exception_handler.call_args_list
        registered_types = [call.args[0] for call in call_args_list]
        assert RequestValidationError in registered_types

    def test_registers_404_and_500(self) -> None:
        app = MagicMock(spec=FastAPI)
        register_error_handlers(app)
        call_args_list = app.add_exception_handler.call_args_list
        registered_types = [call.args[0] for call in call_args_list]
        assert 404 in registered_types
        assert 500 in registered_types


# ---------------------------------------------------------------------------
# Tests -- AppException base class
# ---------------------------------------------------------------------------


class TestAppExceptionBase:
    def test_inherits_from_exception(self) -> None:
        exc = AppException(status_code=400, code="TEST", message="test")
        assert isinstance(exc, Exception)

    def test_str_is_message(self) -> None:
        exc = AppException(status_code=400, code="TEST", message="human readable")
        assert str(exc) == "human readable"

    def test_details_default_to_empty_list(self) -> None:
        exc = AppException(status_code=400, code="TEST", message="test")
        assert exc.details == []

    def test_details_preserved(self) -> None:
        details = [{"key": "value"}]
        exc = AppException(status_code=400, code="TEST", message="test", details=details)
        assert exc.details is details
