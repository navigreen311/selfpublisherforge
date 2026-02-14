"""SQLAlchemy ORM models for Publishing Operations Center.

ExportJob — tracks EPUB/PDF export generation jobs.
FormattingTemplateModel — stores custom formatting templates per org.
ISBNRecord — tracks ISBN assignments per org.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


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


class ISBNRecord(TenantModel):
    """Tracks ISBN assignments for an organisation."""

    __tablename__ = "isbns"

    isbn: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    format: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. paperback, hardcover, ebook
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    barcode_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    book = relationship("Book", backref="isbns")

    __table_args__ = (
        Index("ix_isbns_org_id", "org_id"),
        Index("ix_isbns_isbn", "isbn", unique=True),
        Index(
            "ix_isbns_deleted_at_partial",
            "id",
            postgresql_where="deleted_at IS NULL",
        ),
    )
