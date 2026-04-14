"""Pydantic schemas for Pen Name Management."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PenNameBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    amazon_author_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=2000)
    photo_url: Optional[str] = None
    genres: list[str] = Field(default_factory=list)
    is_default: bool = False


class PenNameCreate(PenNameBase):
    pass


class PenNameUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    amazon_author_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=2000)
    photo_url: Optional[str] = None
    genres: Optional[list[str]] = None
    is_default: Optional[bool] = None


class PenNameResponse(PenNameBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    user_id: Optional[UUID] = None
    book_count: int = 0
    created_at: datetime
    updated_at: datetime


class PenNameBook(BaseModel):
    id: UUID
    title: str
    type: Optional[str] = None
    status: Optional[str] = None


class PenNameBooksResponse(BaseModel):
    books: list[PenNameBook]


class PenNameAnalyticsResponse(BaseModel):
    revenue: float = 0.0
    sales: int = 0
    books_count: int = 0
    avg_rating: Optional[float] = None
    period: str = "30d"
