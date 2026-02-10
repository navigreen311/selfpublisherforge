"""
Reusable pagination helpers for API endpoints.

Provides ``CursorParams`` for cursor-based pagination input and
``PaginatedResponse`` as a generic envelope for paginated results.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class CursorParams(BaseModel):
    """Cursor-based pagination parameters."""

    cursor: str | None = None
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


def get_pagination_params(
    cursor: str | None = Query(None, description="Pagination cursor for the next page"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
) -> CursorParams:
    """FastAPI dependency that extracts pagination parameters from query strings.

    Usage::

        @router.get("/items")
        async def list_items(params: CursorParams = Depends(get_pagination_params)):
            ...
    """
    return CursorParams(cursor=cursor, limit=limit)
