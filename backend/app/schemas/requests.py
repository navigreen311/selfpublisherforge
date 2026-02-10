"""Common request schemas reused across modules.

These schemas standardise sorting, filtering, date-range queries
and bulk-action payloads so every API endpoint behaves consistently.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class SortDirection(str, Enum):
    """Sort direction for ordered queries."""

    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Generic sort parameters accepted by list endpoints."""

    sort_by: str = Field(
        default="created_at",
        description="Field name to sort by.",
    )
    sort_dir: SortDirection = Field(
        default=SortDirection.DESC,
        description="Sort direction: 'asc' or 'desc'.",
    )


class FilterOperator(str, Enum):
    """Supported filter comparison operators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"


class FilterParams(BaseModel):
    """A single field-level filter clause.

    Example JSON payload::

        {"field": "status", "operator": "eq", "value": "active"}
    """

    field: str = Field(..., description="Model field to filter on.")
    operator: FilterOperator = Field(
        default=FilterOperator.EQ,
        description="Comparison operator.",
    )
    value: str | int | float | bool | list[str] = Field(
        ...,
        description="Value(s) to compare against. Use a list for 'in' operator.",
    )


class DateRangeFilter(BaseModel):
    """Restrict results to a date/datetime window.

    At least one of ``start`` or ``end`` should be provided.
    """

    field: str = Field(
        default="created_at",
        description="The datetime field to filter.",
    )
    start: datetime | date | None = Field(
        default=None,
        description="Inclusive start of the range.",
    )
    end: datetime | date | None = Field(
        default=None,
        description="Inclusive end of the range.",
    )

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: datetime | date | None, info: object) -> datetime | date | None:
        data = info.data if hasattr(info, "data") else {}  # type: ignore[union-attr]
        start = data.get("start")
        if v is not None and start is not None and v < start:
            msg = "'end' must be equal to or after 'start'"
            raise ValueError(msg)
        return v


class BulkActionRequest(BaseModel):
    """Request to perform a single action on multiple resources at once."""

    ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of resource UUIDs to act on (1-100).",
    )
    action: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Action to perform, e.g. 'archive', 'delete', 'activate'.",
    )
    params: dict[str, str | int | float | bool] | None = Field(
        default=None,
        description="Optional action-specific parameters.",
    )
