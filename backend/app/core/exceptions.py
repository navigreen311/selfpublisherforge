"""
Custom exception classes for the SelfPublisherForge application.

These exceptions are caught by the global error handlers registered
in ``error_handler.py`` and converted into structured JSON responses.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception with structured error information.

    Parameters
    ----------
    status_code:
        HTTP status code for the response.
    code:
        Machine-readable error code (e.g. ``"NOT_FOUND"``).
    message:
        Human-readable error message.
    details:
        Optional list of additional error details.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details if details is not None else []


class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(self, resource: str = "Resource", detail: str | None = None) -> None:
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=detail or f"{resource} not found.",
        )


class UnauthorizedError(AppException):
    """Authentication required or invalid credentials (401)."""

    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            status_code=401,
            code="UNAUTHORIZED",
            message=message,
        )


class ForbiddenError(AppException):
    """Insufficient permissions (403)."""

    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(
            status_code=403,
            code="FORBIDDEN",
            message=message,
        )


class ConflictError(AppException):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource conflict.") -> None:
        super().__init__(
            status_code=409,
            code="CONFLICT",
            message=message,
        )


class ValidationError(AppException):
    """Business-logic validation failure (422)."""

    def __init__(self, message: str = "Validation failed.", details: list[Any] | None = None) -> None:
        super().__init__(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
