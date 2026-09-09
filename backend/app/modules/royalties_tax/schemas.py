"""Pydantic schemas for Royalty Tracking & Tax Dashboard."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RoyaltySummary(BaseModel):
    """Top-level KPI card data."""

    ytd_earnings: Decimal = Field(default=Decimal("0"))
    month_earnings: Decimal = Field(default=Decimal("0"))
    pending_payout: Decimal = Field(default=Decimal("0"))
    next_payout_date: date | None = None
    period: str = "ytd"
    year: int
    currency: str = "USD"


class RoyaltyRecordOut(BaseModel):
    id: UUID
    book_id: UUID | None = None
    platform: str
    title: str | None = None
    format_type: str | None = None
    units_sold: int = 0
    royalty_rate: Decimal | None = None
    gross_revenue: Decimal = Decimal("0")
    net_revenue: Decimal = Decimal("0")
    currency: str = "USD"
    period_start: datetime | date | None = None
    period_end: datetime | date | None = None


class RoyaltyRecordList(BaseModel):
    items: list[RoyaltyRecordOut]
    total: int
    limit: int
    offset: int


class PlatformBreakdownEntry(BaseModel):
    platform: str
    amount: Decimal
    percentage: float
    units_sold: int = 0
    last_payment_amount: Decimal | None = None
    last_payment_date: date | None = None
    royalty_rate: Decimal | None = None


class PlatformBreakdown(BaseModel):
    total: Decimal
    currency: str = "USD"
    entries: list[PlatformBreakdownEntry]


class BookBreakdownEntry(BaseModel):
    book_id: UUID | None
    title: str
    units_sold: int
    gross_revenue: Decimal
    net_revenue: Decimal
    platforms: list[str] = Field(default_factory=list)


class BookBreakdown(BaseModel):
    total: Decimal
    entries: list[BookBreakdownEntry]


class RoyaltyImportRequest(BaseModel):
    """JSON body for the import endpoint. File is uploaded separately."""

    platform: str = Field(description="kdp | ingram | d2d | manual")


class RoyaltyImportOut(BaseModel):
    id: UUID
    platform: str
    status: str
    source_filename: str | None
    records_processed: int
    records_failed: int
    total_amount: Decimal | None
    currency: str
    imported_at: datetime


class TaxDocumentOut(BaseModel):
    id: UUID
    tax_year: int
    document_type: str
    platform: str | None = None
    title: str
    status: str
    format: str
    gross_income: Decimal | None = None
    total_expenses: Decimal | None = None
    estimated_tax: Decimal | None = None
    file_size_bytes: int | None = None
    generated_at: datetime


class TaxDocumentList(BaseModel):
    items: list[TaxDocumentOut]
    total: int


class TaxDocumentGenerateRequest(BaseModel):
    tax_year: int = Field(ge=2000, le=2100)
    document_type: str = Field(description="1099_summary | year_end_summary | tax_preparer_csv")
    platform: str | None = None
    format: str = Field(default="pdf", description="pdf | csv")
