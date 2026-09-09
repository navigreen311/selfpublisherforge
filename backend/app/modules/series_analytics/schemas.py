"""Schemas for Series Analytics (read-through rate tracking)."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class FunnelStep(BaseModel):
    """A single step in the series read-through funnel."""

    book_id: UUID
    title: str
    series_order: int
    unique_buyers: int
    units_sold: int
    revenue: float


class ReadThroughRate(BaseModel):
    """Read-through rate between two consecutive volumes."""

    from_order: int
    to_order: int
    from_title: str
    to_title: str
    rate: float = Field(..., description="Fraction (0-1) of V(n) buyers who also bought V(n+1)")
    healthy: bool = Field(..., description="True if rate >= 0.5")


class PerVolumeStat(BaseModel):
    """Per-volume performance row."""

    book_id: UUID
    title: str
    series_order: int
    units_sold: int
    revenue: float
    bsr_avg: int | None = None
    review_count: int | None = None
    rating_avg: float | None = None
    status: str | None = None


class RevenuePerBook(BaseModel):
    """Revenue per book (for bar chart)."""

    book_id: UUID
    title: str
    series_order: int
    revenue: float


class SeriesAnalyticsResponse(BaseModel):
    """Full response for GET /api/v1/series/{id}/analytics."""

    series_id: UUID
    series_name: str
    period: str
    funnel: list[FunnelStep]
    read_through_rates: list[ReadThroughRate]
    overall_read_through: float = Field(..., description="V1 -> last volume overall rate (0-1)")
    avg_revenue_per_vol1_buyer: float
    revenue_per_book: list[RevenuePerBook]
    per_volume_stats: list[PerVolumeStat]
    total_units: int
    total_revenue: float
