"""Pydantic v2 schemas for the Analytics & BI module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------- Enums ----------

class Platform(str, Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram_spark"
    DRAFT2DIGITAL = "draft2digital"
    OTHER = "other"


class ReportType(str, Enum):
    REVENUE_SUMMARY = "revenue_summary"
    BOOK_PERFORMANCE = "book_performance"
    MARKETING_ROI = "marketing_roi"
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"


class AggregationPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class FormatType(str, Enum):
    EBOOK = "ebook"
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    AUDIOBOOK = "audiobook"


# ---------- Analytics Event ----------

class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(..., max_length=100)
    event_source: str = Field(default="system", max_length=100)
    actor_id: UUID | None = None
    actor_type: str = Field(default="user", max_length=50)
    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class AnalyticsEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    event_type: str
    event_source: str
    actor_id: UUID | None = None
    actor_type: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    data: dict[str, Any] = {}
    occurred_at: datetime
    created_at: datetime


# ---------- Royalty Records ----------

class RoyaltyRecordBase(BaseModel):
    platform: str
    marketplace: str = "US"
    title: str
    asin: str | None = None
    isbn: str | None = None
    format_type: str = "ebook"
    units_sold: int = 0
    units_refunded: int = 0
    net_units: int = 0
    list_price: Decimal = Decimal("0.00")
    royalty_rate: Decimal = Decimal("0.70")
    gross_revenue: Decimal = Decimal("0.00")
    net_revenue: Decimal = Decimal("0.00")
    currency: str = "USD"
    period_start: datetime
    period_end: datetime


class RoyaltyRecordResponse(RoyaltyRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID | None = None
    import_batch_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class RoyaltyImportRequest(BaseModel):
    platform: Platform
    file_content: str | None = Field(default=None, description="Base64-encoded CSV content")
    file_name: str | None = None


class RoyaltyImportResponse(BaseModel):
    import_batch_id: UUID
    records_imported: int
    records_skipped: int
    errors: list[str] = []
    platform: str


# ---------- Revenue ----------

class RevenueDataPoint(BaseModel):
    period: str
    revenue: Decimal
    units: int
    platform: str | None = None
    book_title: str | None = None


class RevenueResponse(BaseModel):
    total_revenue: Decimal
    total_units: int
    data_points: list[RevenueDataPoint]
    period_start: datetime
    period_end: datetime
    aggregation: AggregationPeriod
    by_platform: dict[str, Decimal] = {}
    by_book: list[dict[str, Any]] = []


class RevenueQueryParams(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    platform: Platform | None = None
    book_id: UUID | None = None
    aggregation: AggregationPeriod = AggregationPeriod.MONTHLY


# ---------- Dashboard ----------

class KPICard(BaseModel):
    label: str
    value: str
    change_percent: float | None = None
    change_direction: str | None = None  # "up" | "down" | "flat"
    period: str = "vs last month"


class DashboardData(BaseModel):
    kpis: list[KPICard]
    revenue_chart: list[RevenueDataPoint]
    top_books: list[dict[str, Any]]
    platform_breakdown: dict[str, Decimal]
    recent_royalties: list[RoyaltyRecordResponse]
    period_start: datetime
    period_end: datetime


# ---------- Portfolio Metrics ----------

class PortfolioMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_books: int = 0
    total_revenue: Decimal = Decimal("0.00")
    total_units_sold: int = 0
    total_expenses: Decimal = Decimal("0.00")
    net_profit: Decimal = Decimal("0.00")
    avg_roi: Decimal = Decimal("0.00")
    platform_breakdown: dict[str, Any] = {}
    format_breakdown: dict[str, Any] = {}
    top_books: list[dict[str, Any]] = []
    snapshot_date: datetime | None = None


# ---------- Reports ----------

class ReportRequest(BaseModel):
    title: str = Field(..., max_length=500)
    report_type: ReportType
    output_format: OutputFormat = OutputFormat.PDF
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    title: str
    report_type: str
    status: str
    output_format: str
    parameters: dict[str, Any] = {}
    file_path: str | None = None
    file_size: int | None = None
    generated_by: UUID | None = None
    generated_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Trends ----------

class TrendDataPoint(BaseModel):
    period: str
    value: Decimal
    label: str | None = None


class TrendData(BaseModel):
    metric: str
    data_points: list[TrendDataPoint]
    aggregation: AggregationPeriod
    period_start: datetime
    period_end: datetime
    total: Decimal
    average: Decimal
    change_percent: float | None = None


# ---------- Sales Data ----------

class SalesDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    marketplace: str = "US"
    format: str | None = None
    units: int = 0
    revenue: Decimal = Decimal("0.00")
    royalties: Decimal = Decimal("0.00")
    kenp_read: int = 0


class DailySalesRow(BaseModel):
    date: str
    kindle_units: int = 0
    print_units: int = 0
    audio_units: int = 0
    kenp_read: int = 0
    revenue: Decimal = Decimal("0.00")
    royalties: Decimal = Decimal("0.00")


class SalesResponse(BaseModel):
    daily_data: list[DailySalesRow]
    totals: dict[str, Any]
    by_marketplace: list[dict[str, Any]]


# ---------- BSR Tracking ----------

class BSRDataPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime
    bsr: int | None = None
    category_rank: int | None = None
    category_name: str | None = None


# ---------- Book Performance ----------

class BookPerformanceResponse(BaseModel):
    book_id: str
    stats: dict[str, Any]
    bsr_history: list[BSRDataPoint]
    revenue_breakdown: list[dict[str, Any]]
    review_trend: list[dict[str, Any]]


# ---------- Enhanced Dashboard ----------

class EnhancedDashboardResponse(BaseModel):
    stats: list[dict[str, Any]]
    trend_data: list[dict[str, Any]]
    revenue_by_book: list[dict[str, Any]]
    revenue_by_format: list[dict[str, Any]]
    insights: list[dict[str, Any]]
    period: str
    compare_period: str | None = None


# ---------- AI Insights ----------

class AIAnalyticsInsight(BaseModel):
    type: str
    message: str
    book_id: str | None = None
    metric: str | None = None
    severity: str = "info"


# ---------- Enhanced Report Generation ----------

class ReportGenerateRequest(BaseModel):
    title: str = Field(..., max_length=500)
    type: str
    period_start: str | None = None
    period_end: str | None = None
    book_ids: list[str] | None = None
    format: str = "pdf"
    sections: list[str] | None = None
