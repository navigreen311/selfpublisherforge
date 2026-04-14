"""Schemas for bulk operations on books."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BulkActionRequest(BaseModel):
    """Request body for POST /api/v1/books/bulk.

    action:
      - archive: set book.status = "archived"
      - delete: soft-delete (sets deleted_at)
      - change_price: set metadata.price = params.price
      - add_tags: merge params.tags into metadata.tags (dedup)
      - export_metadata_csv: return CSV of metadata for selected books
    """

    action: str = Field(
        ...,
        pattern="^(archive|delete|change_price|add_tags|export_metadata_csv)$",
    )
    book_ids: list[UUID] = Field(..., min_length=1, max_length=500)
    params: dict = Field(default_factory=dict)


class BulkActionResponse(BaseModel):
    """Response for non-export bulk actions."""

    action: str
    requested: int
    affected: int
    skipped_ids: list[UUID] = []
    message: str | None = None
