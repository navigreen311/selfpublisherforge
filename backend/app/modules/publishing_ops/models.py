"""SQLAlchemy ORM models for Publishing Operations Center.

ExportJob — tracks EPUB/PDF export generation jobs.
FormattingTemplateModel — stores custom formatting templates per org.
ISBN — tracks ISBN assignments per org/book.
BookPricing — stores per-book pricing across formats.
PricingHistory — audit log for pricing changes.
"""

from __future__ import annotations

import uuid

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class ExportJob(TenantModel):
    __tablename__ = "export_jobs"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # epub, pdf
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    book = relationship("Book", backref="export_jobs")

    __table_args__ = (
        Index("ix_export_jobs_status", "status"),
        Index("ix_export_jobs_org_id_created_at", "org_id", "created_at"),
        Index(
            "ix_export_jobs_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )


class FormattingTemplateModel(TenantModel):
    __tablename__ = "formatting_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trim_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    style_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    __table_args__ = (
        Index("ix_formatting_templates_genre", "genre"),
        Index("ix_formatting_templates_org_id_created_at", "org_id", "created_at"),
        Index(
            "ix_formatting_templates_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )


class ISBN(TenantModel):
    __tablename__ = "isbns"

    isbn: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="available", server_default="available"
    )
    barcode_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    book = relationship("Book", backref="isbns")

    __table_args__ = (
        Index("ix_isbns_org_id_created_at", "org_id", "created_at"),
        Index("ix_isbns_status", "status"),
        Index(
            "ix_isbns_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )


class BookPricing(TenantModel):
    __tablename__ = "book_pricing"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kindle_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    paperback_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    hardcover_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    audiobook_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="USD", server_default="USD"
    )

    # Relationships
    book = relationship("Book", backref="pricing")

    __table_args__ = (
        Index("ix_book_pricing_org_id_created_at", "org_id", "created_at"),
        Index(
            "ix_book_pricing_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )


class PricingHistory(BaseModel):
    __tablename__ = "pricing_history"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    new_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Relationships
    book = relationship("Book", backref="pricing_history")

    __table_args__ = (
        Index("ix_pricing_history_book_id_created_at", "book_id", "created_at"),
        Index(
            "ix_pricing_history_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )
