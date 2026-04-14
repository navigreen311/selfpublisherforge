"""Pydantic schemas for the Royalties module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Distributor(str, Enum):
    KDP = "kdp"
    INGRAM = "ingram"
    D2D = "d2d"
    OTHER = "other"


class RoyaltyType(str, Enum):
    KINDLE_EBOOK = "kindle_ebook"
    KU_KENP = "ku_kenp"
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    EBOOK = "ebook"
    PRINT = "print"
    OTHER = "other"


class Period(str, Enum):
    YTD = "ytd"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class RoyaltyEntryBase(BaseModel):
    distributor: str
    royalty_type: str
    amount: Decimal
    currency: str = "USD"
    units_sold: int | None = None
    kenp_pages: int | None = None
    royalty_rate: Decimal | None = None
    period_month: int | None = Field(default=None, ge=1, le=12)
    period_year: int | None = Field(default=None, ge=2000, le=2100)
    payment_date: date | None = None
    book_id: UUID | None = None
    pen_name_id: UUID | None = None
    notes: str | None = None


class RoyaltyEntryCreate(RoyaltyEntryBase):
    source: str = "manual"


class RoyaltyEntryOut(RoyaltyEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    source: str
    import_batch_id: UUID | None = None
    created_at: datetime


class DistributorSummary(BaseModel):
    distributor: str
    total: Decimal
    pct: float
    breakdown: dict[str, Decimal]
    units_sold: int
    kenp_pages: int
    last_payment_amount: Decimal | None = None
    last_payment_date: date | None = None


class RoyaltyDashboard(BaseModel):
    ytd_earnings: Decimal
    this_month_earnings: Decimal
    pending_payout: Decimal
    next_payout_date: date | None = None
    by_distributor: list[DistributorSummary]
    total: Decimal
    period: str
    year: int


class MonthlyStatementRow(BaseModel):
    month: int
    year: int
    label: str
    kdp_ebook: Decimal = Decimal("0")
    kdp_print: Decimal = Decimal("0")
    ku_kenp: Decimal = Decimal("0")
    ingram: Decimal = Decimal("0")
    d2d: Decimal = Decimal("0")
    other: Decimal = Decimal("0")
    total: Decimal = Decimal("0")


class MonthlyStatement(BaseModel):
    year: int
    rows: list[MonthlyStatementRow]
    ytd_totals: MonthlyStatementRow


class RoyaltyImportResult(BaseModel):
    imported: int
    skipped: int
    distributor: str
    import_batch_id: UUID
    errors: list[str] = Field(default_factory=list)
    total_amount: Decimal
