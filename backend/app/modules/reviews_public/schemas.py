"""Pydantic schemas for the public reviews + widget endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PublicReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: float
    title: str | None = None
    body_excerpt: str | None = None
    reviewer_name: str | None = None
    date: datetime | None = None


class PublicReviewsResponse(BaseModel):
    book_id: str
    book_title: str | None = None
    rating: float = 0.0
    review_count: int = 0
    reviews: list[PublicReviewItem] = Field(default_factory=list)


class WidgetConfigRequest(BaseModel):
    book_id: str
    style: str = "compact"  # compact | full | badge
    theme: str = "light"  # light | dark | auto
    max_reviews: int = 3
    show_stars: bool = True
    show_count: bool = True
    show_reviews: bool = True


class WidgetConfigResponse(BaseModel):
    embed_code: str
    api_url: str
