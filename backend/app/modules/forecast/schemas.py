"""Pydantic schemas for revenue forecasting."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    """A single point on the forecast chart."""

    date: date
    actual: float | None = None
    projected: float | None = None
    conf_low: float | None = None
    conf_high: float | None = None


class ForecastSummary(BaseModel):
    """Headline numbers for the forecast horizon."""

    horizon_days: int
    expected_revenue: float = Field(..., description="Likely projected revenue over horizon")
    best_case: float = Field(..., description="Optimistic (upper confidence) revenue")
    worst_case: float = Field(..., description="Pessimistic (lower confidence) revenue")
    trend_pct: float = Field(..., description="Slope as % change vs current daily avg")
    confidence: float = Field(..., description="0..1 confidence score")
    past_actual_total: float = Field(..., description="Total actual revenue in lookback window")


class ForecastResponse(BaseModel):
    """Response for GET /api/v1/forecast/revenue."""

    horizon_days: int
    summary: ForecastSummary
    chart_data: list[ForecastPoint]
    seasonality_insights: list[str] = []
    currency: str = "USD"
