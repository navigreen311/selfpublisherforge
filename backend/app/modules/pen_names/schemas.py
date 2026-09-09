"""Pydantic schemas for the Pen Names module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PenNameCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    amazon_url: str | None = Field(None, max_length=2000)
    bio: str | None = Field(None, max_length=2000)
    photo_url: str | None = Field(None, max_length=2000)
    genres: list[str] = Field(default_factory=list, max_length=20)
    is_default: bool = False


class PenNameUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    amazon_url: str | None = Field(None, max_length=2000)
    bio: str | None = Field(None, max_length=2000)
    photo_url: str | None = Field(None, max_length=2000)
    genres: list[str] | None = Field(None, max_length=20)
    is_default: bool | None = None


class PenNameResponse(BaseModel):
    id: UUID
    display_name: str
    amazon_url: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    is_default: bool = False
    book_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PenNameBook(BaseModel):
    id: UUID
    title: str
    type: str | None = None
    status: str | None = None


class PenNameBooksResponse(BaseModel):
    books: list[PenNameBook]


class PenNameAnalyticsResponse(BaseModel):
    revenue: float = 0.0
    sales: int = 0
    books_count: int = 0
    avg_rating: float = 0.0
    period: str = "30d"
