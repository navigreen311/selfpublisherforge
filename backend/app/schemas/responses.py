"""Common response schemas (envelope pattern) used across all API modules.

Every API response is wrapped in a consistent envelope so the frontend can
rely on a predictable shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """A single validation or business-rule error."""

    field: str | None = Field(
        default=None,
        description="The request field that caused the error (if applicable).",
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
    )
    code: str | None = Field(
        default=None,
        description="Machine-readable error code for this detail.",
    )


class ErrorResponse(BaseModel):
    """Standard error envelope returned for 4xx/5xx responses."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable summary.")
    details: list[ErrorDetail] = Field(
        default_factory=list,
        description="Granular validation / business-rule errors.",
    )
    request_id: str = Field(
        ...,
        description="Correlation ID for tracing in logs.",
    )


class ErrorEnvelope(BaseModel):
    """Top-level error wrapper matching the frontend ``ApiError`` type."""

    error: ErrorResponse


# ---------------------------------------------------------------------------
# Success envelope
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope wrapping a ``data`` payload."""

    data: T
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata (pagination cursors, counts, etc.).",
    )


# ---------------------------------------------------------------------------
# Bulk action response
# ---------------------------------------------------------------------------

class BulkItemResult(BaseModel):
    """Outcome of a single item within a bulk action."""

    id: UUID
    success: bool
    error: str | None = None


class BulkActionResponse(BaseModel):
    """Response for :class:`~app.schemas.requests.BulkActionRequest`."""

    total: int = Field(..., description="Number of items submitted.")
    succeeded: int = Field(..., description="Number that succeeded.")
    failed: int = Field(..., description="Number that failed.")
    results: list[BulkItemResult] = Field(
        default_factory=list,
        description="Per-item outcomes.",
    )


# ---------------------------------------------------------------------------
# Pagination wrapper (extends core pagination with envelope)
# ---------------------------------------------------------------------------

class PaginatedMeta(BaseModel):
    """Pagination metadata placed in ``meta`` of a success response."""

    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


class PaginatedSuccessResponse(BaseModel, Generic[T]):
    """Success response specifically for paginated list endpoints."""

    data: list[T]
    meta: PaginatedMeta
