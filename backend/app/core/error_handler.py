"""
Global error handlers for the FastAPI application.

Provides handlers for:
- AppException       -> structured JSON error envelope
- RequestValidationError -> 422 with per-field details
- 404 Not Found
- 500 Internal Server Error (includes request_id for debugging)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import AppException

logger = logging.getLogger("spf.error_handler")


def _get_request_id(request: Request) -> str:
    """Retrieve correlation / request ID from the request state."""
    return getattr(request.state, "correlation_id", "unknown")


def _error_envelope(
    code: str,
    message: str,
    request_id: str,
    details: list[Any] | None = None,
) -> dict[str, Any]:
    """Build the standard JSON error envelope."""
    envelope: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    if details:
        envelope["error"]["details"] = details
    return envelope


# -----------------------------------------------------------------------
# Individual handlers
# -----------------------------------------------------------------------


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-level exceptions defined via ``AppException``."""
    request_id = _get_request_id(request)
    logger.warning(
        "app_exception | code=%s detail=%s request_id=%s",
        exc.code,
        exc.message,
        request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_envelope(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic / FastAPI request validation errors."""
    request_id = _get_request_id(request)
    field_errors = []
    for err in exc.errors():
        field_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=422,
        content=_error_envelope(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            request_id=request_id,
            details=field_errors,
        ),
    )


async def not_found_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle 404 Not Found."""
    request_id = _get_request_id(request)
    return JSONResponse(
        status_code=404,
        content=_error_envelope(
            code="NOT_FOUND",
            message=str(exc.detail) if exc.detail else "The requested resource was not found.",
            request_id=request_id,
        ),
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    Logs the full traceback and returns a sanitized 500 response that
    includes the ``request_id`` so support can correlate the error in
    logs.
    """
    request_id = _get_request_id(request)
    logger.exception(
        "unhandled_exception",
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content=_error_envelope(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Reference this request_id when contacting support.",
            request_id=request_id,
        ),
    )


# -----------------------------------------------------------------------
# Registration helper
# -----------------------------------------------------------------------


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on *app*.

    Call this during application startup (e.g. in ``create_app``).
    """
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(404, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(500, internal_error_handler)  # type: ignore[arg-type]
