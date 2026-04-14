"""SQLAlchemy models for the Royalty Tracking & Tax Dashboard module.

The ``royalty_records`` table is defined in ``app.modules.analytics.models``.
This module adds:

* :class:`TaxDocument` - backed by ``tax_documents``.
* :class:`PlatformRoyaltyImport` - backed by ``platform_royalty_imports``.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaxDocument(Base):
    """Generated tax documents (1099 summaries, year-end summaries, CSVs)."""

    __tablename__ = "tax_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ready")
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="pdf")
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gross_income: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_expenses: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    estimated_tax: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    doc_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_tax_documents_org_year", "org_id", "tax_year"),
        Index("idx_tax_documents_type", "document_type"),
        {"extend_existing": True},
    )


class PlatformRoyaltyImport(Base):
    """Tracks royalty CSV/XLSX imports from distribution platforms."""

    __tablename__ = "platform_royalty_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_platform_royalty_imports_org", "org_id", "imported_at"),
        Index("idx_platform_royalty_imports_platform", "platform"),
        {"extend_existing": True},
    )
