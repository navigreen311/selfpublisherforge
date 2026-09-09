"""SQLAlchemy models for Children's Books -- books, pages, characters."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class ChildrensBook(TenantModel):
    """Master record for a children's book project."""

    __tablename__ = "childrens_books"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    age_range: Mapped[str | None] = mapped_column(String(20), default="3-5")
    page_count: Mapped[int] = mapped_column(Integer, default=32)
    trim_size: Mapped[str | None] = mapped_column(String(20), default="8.5x8.5")
    illustration_style: Mapped[str | None] = mapped_column(String(50), default="watercolor")
    color_palette: Mapped[str | None] = mapped_column(String(100), nullable=True)
    story_mode: Mapped[str | None] = mapped_column(String(20), default="manual")
    is_bilingual: Mapped[bool] = mapped_column(Boolean, default=False)
    target_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    fear_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    pages: Mapped[list[ChildrensBookPage]] = relationship(
        back_populates="book", cascade="all, delete-orphan", lazy="selectin"
    )
    characters: Mapped[list[ChildrensBookCharacter]] = relationship(
        back_populates="book", cascade="all, delete-orphan", lazy="selectin"
    )


class ChildrensBookPage(BaseModel):
    """Individual page content and layout metadata."""

    __tablename__ = "childrens_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("childrens_books.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str | None] = mapped_column(String(20), default="spread")
    layout: Mapped[str | None] = mapped_column(String(50), default="text_bottom")
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    illustration_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    illustration_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_font: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_position: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    text_plate: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    book: Mapped[ChildrensBook] = relationship(back_populates="pages")


class ChildrensBookCharacter(BaseModel):
    """Character consistency sheet for a children's book."""

    __tablename__ = "childrens_book_characters"

    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("childrens_books.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    species: Mapped[str | None] = mapped_column(String(100), default="human")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_images: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    auto_append: Mapped[bool] = mapped_column(Boolean, default=True)
    clothing_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scale_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    book: Mapped[ChildrensBook] = relationship(back_populates="characters")
