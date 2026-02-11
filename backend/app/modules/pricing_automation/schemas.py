"""Pydantic v2 schemas for the Pricing Automation module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ──────────────────── Enums ────────────────────


class PricingStrategyType(str, Enum):
    COMPETITIVE_MATCH = "competitive_match"
    VALUE_BASED = "value_based"
    PENETRATION = "penetration"
    DYNAMIC = "dynamic"
    PROMOTIONAL = "promotional"


class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class PromotionStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookFormat(str, Enum):
    EBOOK = "ebook"
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    AUDIOBOOK = "audiobook"


# ──────────────────── Pricing Rule Schemas ────────────────────


class PricingRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    book_id: UUID | None = None
    strategy: PricingStrategyType
    book_format: BookFormat = BookFormat.EBOOK
    min_price: float = Field(default=0.99, ge=0.0, le=9999.99)
    max_price: float = Field(default=9.99, ge=0.0, le=9999.99)
    target_price: float | None = Field(default=None, ge=0.0, le=9999.99)
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_auto_apply: bool = False

    @field_validator("max_price")
    @classmethod
    def max_price_gte_min(cls, v: float, info: Any) -> float:
        min_price = info.data.get("min_price")
        if min_price is not None and v < min_price:
            raise ValueError("max_price must be >= min_price")
        return v


class PricingRuleCreate(PricingRuleBase):
    """Request body for creating a new pricing rule. Inherits all fields from PricingRuleBase."""


class PricingRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    strategy: PricingStrategyType | None = None
    status: RuleStatus | None = None
    book_format: BookFormat | None = None
    min_price: float | None = Field(default=None, ge=0.0, le=9999.99)
    max_price: float | None = Field(default=None, ge=0.0, le=9999.99)
    target_price: float | None = Field(default=None, ge=0.0, le=9999.99)
    parameters: dict[str, Any] | None = None
    is_auto_apply: bool | None = None


class PricingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    description: str | None
    book_id: UUID | None
    strategy: PricingStrategyType
    status: RuleStatus
    book_format: BookFormat
    min_price: float
    max_price: float
    target_price: float | None
    parameters: dict[str, Any]
    is_auto_apply: bool
    last_applied_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ──────────────────── Price Simulation Schemas ────────────────────


class PricePoint(BaseModel):
    price: float = Field(..., ge=0.0)
    estimated_daily_sales: float
    estimated_daily_revenue: float
    estimated_monthly_revenue: float
    royalty_rate: float
    estimated_daily_royalties: float
    estimated_monthly_royalties: float


class PriceSimulationRequest(BaseModel):
    book_id: UUID | None = None
    current_price: float = Field(..., ge=0.0)
    proposed_price: float = Field(..., ge=0.0)
    book_format: BookFormat = BookFormat.EBOOK
    current_daily_sales: float = Field(..., ge=0.0)
    elasticity: float = Field(
        default=-1.5,
        description="Price elasticity of demand (negative value).",
    )
    royalty_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Override royalty rate. If None, auto-calculated based on price range.",
    )


class PriceSimulationResponse(BaseModel):
    book_id: UUID | None
    current_price: float
    proposed_price: float
    price_change_pct: float
    book_format: BookFormat
    elasticity: float
    current_metrics: PricePoint
    proposed_metrics: PricePoint
    revenue_change_pct: float
    royalty_change_pct: float
    breakeven_sales: float
    recommended_price_points: list[PricePoint]


# ──────────────────── Competitor Price Schemas ────────────────────


class CompetitorPriceEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    competitor_asin: str | None
    competitor_title: str
    competitor_author: str | None
    book_format: BookFormat
    price: float
    currency: str
    bsr_rank: int | None
    review_count: int | None
    review_rating: float | None
    category: str | None
    snapshot_date: datetime
    source: str


class CompetitorPriceSummary(BaseModel):
    book_id: UUID
    book_format: BookFormat
    total_competitors: int
    avg_price: float
    median_price: float
    min_price: float
    max_price: float
    price_percentile_25: float
    price_percentile_75: float
    avg_bsr: float | None
    avg_review_rating: float | None
    competitors: list[CompetitorPriceEntry]


# ──────────────────── A/B Test Schemas ────────────────────


class ABTestCreate(BaseModel):
    book_id: UUID
    pricing_rule_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price_a: float = Field(..., ge=0.0)
    price_b: float = Field(..., ge=0.0)
    book_format: BookFormat = BookFormat.EBOOK
    duration_days: int = Field(default=14, ge=1, le=90)


class ABTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    pricing_rule_id: UUID | None
    book_id: UUID
    name: str
    description: str | None
    price_a: float
    price_b: float
    book_format: BookFormat
    status: ABTestStatus
    start_date: datetime | None
    end_date: datetime | None
    duration_days: int
    results: dict[str, Any] | None
    winner: str | None
    confidence_level: float | None
    created_at: datetime
    updated_at: datetime


# ──────────────────── Promotion Schemas ────────────────────


class PromotionCreate(BaseModel):
    book_id: UUID
    pricing_rule_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    original_price: float = Field(..., ge=0.0)
    promo_price: float = Field(..., ge=0.0)
    book_format: BookFormat = BookFormat.EBOOK
    start_date: datetime
    end_date: datetime
    platform: str = "amazon"
    notes: str | None = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: datetime, info: Any) -> datetime:
        start = info.data.get("start_date")
        if start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("promo_price")
    @classmethod
    def promo_less_than_original(cls, v: float, info: Any) -> float:
        original = info.data.get("original_price")
        if original is not None and v >= original:
            raise ValueError("promo_price must be less than original_price")
        return v


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    pricing_rule_id: UUID | None
    book_id: UUID
    name: str
    description: str | None
    original_price: float
    promo_price: float
    book_format: BookFormat
    start_date: datetime
    end_date: datetime
    status: PromotionStatus
    platform: str
    notes: str | None
    performance_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


# ──────────────────── KU Calculator Schemas ────────────────────


class KUCalculatorRequest(BaseModel):
    """Input for KU (Kindle Unlimited) vs. Wide distribution revenue calculator."""

    book_page_count: int = Field(..., ge=1, le=10000, description="KENPC page count")
    estimated_ku_reads_per_month: int = Field(
        ..., ge=0, description="Estimated full KU reads per month"
    )
    ku_page_rate: float = Field(
        default=0.0045,
        ge=0.0,
        description="KU per-page-read rate (KENP rate). Defaults to ~$0.0045.",
    )
    wide_price: float = Field(
        ..., ge=0.0, description="Price for wide distribution sales"
    )
    wide_monthly_sales: int = Field(
        ..., ge=0, description="Estimated monthly unit sales in wide distribution"
    )
    wide_royalty_rate: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Royalty rate for wide distribution. Defaults to 70%.",
    )
    amazon_price: float = Field(
        ..., ge=0.0, description="Price on Amazon (when in KU)"
    )
    amazon_monthly_sales: int = Field(
        ..., ge=0, description="Estimated monthly unit sales on Amazon (paid, outside KU)"
    )
    amazon_royalty_rate: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Amazon royalty rate. Defaults to 70%.",
    )


class RevenueBreakdown(BaseModel):
    source: str
    monthly_revenue: float
    monthly_royalties: float
    annual_revenue: float
    annual_royalties: float


class KUCalculatorResponse(BaseModel):
    ku_exclusive: RevenueBreakdown
    wide_distribution: RevenueBreakdown
    difference_monthly: float
    difference_annual: float
    recommendation: str
    details: dict[str, Any]
