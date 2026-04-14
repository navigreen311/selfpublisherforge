"""SQLAlchemy models for the Proof Orders module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class ProofOrder(TenantModel):
    """A proof copy order against an in-progress publishing workflow."""

    __tablename__ = "proof_orders"

    publishing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    interior_file_url: Mapped[str] = mapped_column(Text, nullable=False)
    cover_file_url: Mapped[str] = mapped_column(Text, nullable=False)
    trim_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interior_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    shipping_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(10), nullable=True)
    shipping_zip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    print_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ordered")
    checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    issues: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_proof_orders_publishing_id", "publishing_id"),
        {"extend_existing": True},
    )
