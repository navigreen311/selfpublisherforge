"""Pydantic schemas for global search."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: UUID | str
    title: str
    snippet: str | None = None
    resource_type: str


class SearchResponse(BaseModel):
    query: str
    results_by_type: dict[str, list[SearchResultItem]]
    total_count: int
