"""Pydantic schemas for the Market Intelligence Engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ---------------------------------------------------------------------------
# Category schemas
# ---------------------------------------------------------------------------


class CategoryNode(BaseModel):
    id: str = Field(..., description="Amazon browse-node ID")
    name: str
    parent_id: str | None = None
    children: list[CategoryNode] = Field(default_factory=list)
    book_count: int | None = None

    model_config = {"from_attributes": True}


class CategoryAnalysis(BaseModel):
    category_id: str
    category_name: str
    book_count: int
    avg_bsr: float = Field(..., description="Average Best Sellers Rank")
    median_bsr: float
    avg_price: float
    avg_reviews: float
    avg_rating: float
    competition_score: float = Field(..., ge=0, le=100)
    bsr_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="BSR range buckets, e.g. {'1-1000': 45, '1001-5000': 120}",
    )
    top_books: list[CompetitorSummary] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Keyword schemas
# ---------------------------------------------------------------------------


class KeywordResearchRequest(BaseModel):
    keywords: list[str] = Field(..., min_length=1, max_length=20)
    marketplace: str = Field(default="US", description="Amazon marketplace code")


class KeywordData(BaseModel):
    keyword: str
    search_volume: int = Field(..., ge=0)
    competition: float = Field(..., ge=0, le=1, description="0=low, 1=high")
    cpc: float = Field(..., ge=0, description="Cost per click in USD")
    trend: TrendDirection = TrendDirection.STABLE
    trend_data: list[float] = Field(
        default_factory=list,
        description="Monthly search volume for the last 12 months",
    )
    relevance_score: float = Field(default=0, ge=0, le=100)


class KeywordResearchResponse(BaseModel):
    keywords: list[KeywordData]
    marketplace: str
    generated_at: datetime


class KeywordSuggestionsParams(BaseModel):
    genre: str
    niche: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Niche analysis schemas
# ---------------------------------------------------------------------------


class NicheAnalysisRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=200)
    category_id: str | None = None
    marketplace: str = Field(default="US")


class GapAnalysisItem(BaseModel):
    area: str
    description: str
    opportunity_level: str = Field(..., description="low / medium / high")


class NicheAnalysisResponse(BaseModel):
    niche: str
    demand_score: float = Field(..., ge=0, le=100)
    supply_score: float = Field(..., ge=0, le=100)
    opportunity_score: float = Field(..., ge=0, le=100)
    top_competitors: list[CompetitorSummary]
    gap_analysis: list[GapAnalysisItem]
    avg_monthly_revenue: float | None = None
    avg_bsr: float | None = None
    recommendation: str = ""
    analyzed_at: datetime


# ---------------------------------------------------------------------------
# Competitor schemas
# ---------------------------------------------------------------------------


class CompetitorSummary(BaseModel):
    asin: str
    title: str
    author: str = ""
    bsr: int | None = None
    price: float | None = None
    reviews_count: int = 0
    rating: float | None = None
    image_url: str | None = None


class CompetitorTrackRequest(BaseModel):
    asin: str = Field(..., min_length=10, max_length=10, pattern=r"^B[0-9A-Z]{9}$")
    marketplace: str = Field(default="US")


class BSRHistoryPoint(BaseModel):
    date: datetime
    bsr: int
    price: float | None = None


class CompetitorDetail(BaseModel):
    id: UUID
    asin: str
    title: str
    author: str
    bsr: int | None = None
    price: float | None = None
    reviews_count: int = 0
    rating: float | None = None
    image_url: str | None = None
    category: str | None = None
    marketplace: str = "US"
    bsr_history: list[BSRHistoryPoint] = Field(default_factory=list)
    tracked_since: datetime
    last_updated: datetime | None = None

    model_config = {"from_attributes": True}


class CompetitorListItem(BaseModel):
    id: UUID
    asin: str
    title: str
    author: str
    bsr: int | None = None
    price: float | None = None
    reviews_count: int = 0
    rating: float | None = None
    marketplace: str = "US"
    tracked_since: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Trends / Snapshots
# ---------------------------------------------------------------------------


class TrendDataPoint(BaseModel):
    date: datetime
    value: float


class MarketTrend(BaseModel):
    label: str
    category_id: str | None = None
    keyword: str | None = None
    direction: TrendDirection
    data_points: list[TrendDataPoint] = Field(default_factory=list)
    change_pct: float = Field(default=0, description="Percentage change over period")


class MarketTrendsResponse(BaseModel):
    trends: list[MarketTrend]
    period_start: datetime
    period_end: datetime


class MarketSnapshot(BaseModel):
    id: UUID
    category_id: str
    category_name: str
    snapshot_date: datetime
    avg_bsr: float
    avg_price: float
    book_count: int
    avg_reviews: float
    competition_score: float

    model_config = {"from_attributes": True}


# Resolve forward references
CategoryAnalysis.model_rebuild()
NicheAnalysisResponse.model_rebuild()
