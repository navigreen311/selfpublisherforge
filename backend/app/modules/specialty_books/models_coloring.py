"""SQLAlchemy models for Coloring Books."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class ColoringBook(TenantModel):
    __tablename__ = "coloring_books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=30)
    trim_size: Mapped[str | None] = mapped_column(String(30), nullable=True, default="8.5x11")
    line_style: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    line_weight: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    complexity: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    stroke_uniformity: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    single_sided: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    pages: Mapped[list[ColoringBookPage]] = relationship(
        "app.modules.specialty_books.models_coloring.ColoringBookPage",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ColoringBookPage(TenantModel):
    __tablename__ = "coloring_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("coloring_books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str | None] = mapped_column(String(20), default="content")
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cleaned_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    vectorized_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    illustration_seed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    qa_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    book: Mapped[ColoringBook] = relationship(
        "app.modules.specialty_books.models_coloring.ColoringBook", back_populates="pages"
    )


class ColoringBatchJob(TenantModel):
    __tablename__ = "coloring_batch_jobs"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("coloring_books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    budget_limit_cents: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    spent_cents: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    pages_total: Mapped[int] = mapped_column(Integer, default=0)
    pages_completed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
