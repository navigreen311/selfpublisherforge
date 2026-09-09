"""SQLAlchemy models for Coloring Books."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel
from app.modules.specialty.models.enums import (
    Audience,
    BookStatus,
    ColoringPageType,
    LineStyle,
)


class ColoringBook(TenantModel):
    """Master record for a coloring book."""

    __tablename__ = "coloring_books"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    audience: Mapped[str] = mapped_column(
        Enum(Audience, name="audience", native_enum=True),
        nullable=False,
        default=Audience.adults,
    )
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    trim_size: Mapped[str] = mapped_column(String(20), nullable=False, default="8.5x11")
    line_style: Mapped[str] = mapped_column(
        Enum(LineStyle, name="line_style", native_enum=True),
        nullable=False,
        default=LineStyle.medium,
    )
    line_weight: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    complexity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    stroke_uniformity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    single_sided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("book_series.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(BookStatus, name="book_status", native_enum=True, create_type=False),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
    )
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    pages: Mapped[list[ColoringBookPage]] = relationship(
        "ColoringBookPage",
        back_populates="book",
        cascade="all, delete-orphan",
    )


class ColoringBookPage(BaseModel):
    """Individual page in a coloring book."""

    __tablename__ = "coloring_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coloring_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str] = mapped_column(
        Enum(ColoringPageType, name="coloring_page_type", native_enum=True),
        nullable=False,
        default=ColoringPageType.illustration,
    )
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    vectorized_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    illustration_seed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    closed_shapes_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    speck_free: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    stroke_uniform: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ink_density_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    bg_pure_white: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    book: Mapped[ColoringBook] = relationship("ColoringBook", back_populates="pages")
