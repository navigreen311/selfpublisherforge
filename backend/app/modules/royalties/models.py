"""SQLAlchemy models for the Royalties module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class RoyaltyEntry(TenantModel):
    """Single royalty line item imported from a distributor report."""

    __tablename__ = "royalty_entries"

    # FK to pen_names added post-merge with Stream 1 (pen_names module).
    pen_name_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    distributor: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    royalty_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    units_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kenp_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    royalty_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    period_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="import")
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_royalty_entries_org_period", "org_id", "period_year", "period_month"),
        {"extend_existing": True},
    )


class TaxExpense(TenantModel):
    """Deductible business expense entry (self-reported)."""

    __tablename__ = "tax_expenses"

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    receipt_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_tax_expenses_org_year", "org_id", "tax_year"),
        {"extend_existing": True},
    )


class QuarterlyTaxPayment(TenantModel):
    """Tracked quarterly estimated tax payment."""

    __tablename__ = "quarterly_tax_payments"

    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid: Mapped[bool] = mapped_column(default=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index(
            "uq_quarterly_tax_org_year_quarter",
            "org_id",
            "tax_year",
            "quarter",
            unique=True,
        ),
        {"extend_existing": True},
    )
