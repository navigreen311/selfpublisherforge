"""Pydantic v2 schemas for the Chrome Extension API."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AmazonMarketplace(str, Enum):
    US = "amazon.com"
    UK = "amazon.co.uk"
    DE = "amazon.de"
    FR = "amazon.fr"
    CA = "amazon.ca"
    AU = "amazon.com.au"
    JP = "amazon.co.jp"
    IT = "amazon.it"
    ES = "amazon.es"
    IN = "amazon.in"


class ClipType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    LINK = "link"
    PRODUCT = "product"
    NOTE = "note"


# ---------------------------------------------------------------------------
# Extracted Amazon data
# ---------------------------------------------------------------------------


class ReviewSummary(BaseModel):
    total_reviews: int = 0
    average_rating: float | None = None
    rating_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Star rating counts, e.g. {'5': 120, '4': 30, ...}",
    )


class ExtractedAmazonData(BaseModel):
    """Data extracted from an Amazon product page by the content script."""

    asin: str = Field(..., min_length=10, max_length=10)
    title: str
    subtitle: str | None = None
    author: str | None = None
    price: float | None = None
    currency: str = "USD"
    bsr: int | None = Field(None, description="Best Sellers Rank (overall)")
    bsr_categories: dict[str, int] = Field(
        default_factory=dict,
        description="BSR by category name, e.g. {'Kindle eBooks > Romance': 342}",
    )
    categories: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    reviews: ReviewSummary = Field(default_factory=ReviewSummary)
    page_url: str | None = None
    image_url: str | None = None
    marketplace: AmazonMarketplace = AmazonMarketplace.US
    publication_date: str | None = None
    page_count: int | None = None
    language: str | None = None
    dimensions: str | None = None
    isbn: str | None = None
    raw_html_snippet: str | None = Field(
        None, max_length=50_000, description="Optional raw HTML for server-side re-parse"
    )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExtractDataRequest(BaseModel):
    """Payload sent from the Chrome Extension to save extracted data."""

    data: ExtractedAmazonData
    notes: str | None = Field(None, max_length=5000)
    tags: list[str] = Field(default_factory=list)


class QuickResearchQuery(BaseModel):
    """Query parameters for the quick research sidebar."""

    asin: str | None = Field(None, min_length=10, max_length=10)
    keywords: list[str] = Field(default_factory=list, max_length=10)
    category: str | None = None
    marketplace: AmazonMarketplace = AmazonMarketplace.US


class ClipSaveRequest(BaseModel):
    """Save a clip from the browser to the Knowledge Vault."""

    clip_type: ClipType = ClipType.TEXT
    content: str = Field(..., min_length=1, max_length=100_000)
    source_url: str | None = None
    title: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=30)
    notes: str | None = Field(None, max_length=5000)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ExtractedDataResponse(BaseModel):
    """Confirmation after saving extracted Amazon data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    asin: str
    title: str
    bsr: int | None = None
    saved_at: datetime


class RelatedKeyword(BaseModel):
    """A related keyword suggestion with estimated search volume."""

    keyword: str
    volume: str = Field(
        "medium",
        description="Estimated search volume indicator: 'high', 'medium', or 'low'.",
        pattern="^(high|medium|low)$",
    )
    relevance: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Relevance score 0-1 indicating closeness to the original keywords.",
    )
    source: str = Field(
        "analysis",
        description="How the keyword was derived: 'llm', 'title', 'frequency', 'synonym'.",
    )


class QuickResearchResponse(BaseModel):
    """Quick research data returned to the sidebar."""

    model_config = ConfigDict(from_attributes=True)

    asin: str | None = None
    title: str | None = None
    current_bsr: int | None = None
    bsr_history: list[dict[str, Any]] = Field(default_factory=list)
    estimated_daily_sales: int | None = None
    competitor_count: int | None = None
    avg_price: float | None = None
    avg_reviews: float | None = None
    niche_score: float | None = Field(None, ge=0, le=100)
    related_keywords: list[RelatedKeyword] = Field(default_factory=list)
    trends: dict[str, Any] = Field(default_factory=dict)


class ClipSaveResponse(BaseModel):
    """Confirmation after saving a clip to the Knowledge Vault."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    clip_type: ClipType
    title: str | None = None
    saved_at: datetime


class ExtensionVersionResponse(BaseModel):
    """Current published extension version info."""

    version: str
    min_version: str
    update_url: str
    changelog: str
