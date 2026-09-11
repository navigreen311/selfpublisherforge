"""SQLAlchemy models for Children's Books."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel
from app.modules.specialty.models.enums import (
    AgeRange,
    BilingualLayout,
    BookStatus,
    ColorPalette,
    FearIntensity,
    IllustrationStyle,
    PageLayout,
    StoryMode,
    TextPosition,
)


class ChildrensBook(TenantModel):
    """Master record for a children's book."""

    __tablename__ = "childrens_books"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    age_range: Mapped[str] = mapped_column(
        Enum(AgeRange, name="age_range", native_enum=True),
        nullable=False,
        default=AgeRange.preschool,
    )
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    trim_size: Mapped[str] = mapped_column(String(20), nullable=False, default="8.5x8.5")
    illustration_style: Mapped[str] = mapped_column(
        Enum(IllustrationStyle, name="illustration_style", native_enum=True),
        nullable=False,
        default=IllustrationStyle.watercolor,
    )
    color_palette: Mapped[str] = mapped_column(
        Enum(ColorPalette, name="color_palette", native_enum=True),
        nullable=False,
        default=ColorPalette.bright,
    )
    story_mode: Mapped[str] = mapped_column(
        Enum(StoryMode, name="story_mode", native_enum=True),
        nullable=False,
        default=StoryMode.ai_generated,
    )
    # Fed to the AI story generator and scanned for trademarks; the create and
    # update payloads have always carried them.
    story_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    theme_moral: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_bilingual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    bilingual_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bilingual_layout: Mapped[str | None] = mapped_column(
        Enum(BilingualLayout, name="bilingual_layout", native_enum=True),
        nullable=True,
    )
    fear_intensity: Mapped[str] = mapped_column(
        Enum(FearIntensity, name="fear_intensity", native_enum=True),
        nullable=False,
        default=FearIntensity.none,
    )
    status: Mapped[str] = mapped_column(
        Enum(BookStatus, name="specialty_book_status", native_enum=True),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
    )
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    pages: Mapped[list[ChildrensBookPage]] = relationship(
        "ChildrensBookPage",
        back_populates="book",
        cascade="all, delete-orphan",
    )
    characters: Mapped[list[ChildrensBookCharacter]] = relationship(
        "ChildrensBookCharacter",
        back_populates="book",
        cascade="all, delete-orphan",
    )


class ChildrensBookPage(BaseModel):
    """Individual page in a children's book."""

    __tablename__ = "childrens_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("childrens_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str] = mapped_column(String(30), nullable=False, default="story")
    layout: Mapped[str] = mapped_column(
        Enum(PageLayout, name="page_layout", native_enum=True),
        nullable=False,
        default=PageLayout.image_top_text_bottom,
    )
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_font: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_position: Mapped[str | None] = mapped_column(
        Enum(TextPosition, name="text_position", native_enum=True),
        nullable=True,
    )
    text_plate_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    illustration_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    illustration_seed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contrast_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gutter_safe: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Illustration provenance (model, prompt hash, generation date) and upload
    # details, written by generate_illustration and upload_page_image.
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    book: Mapped[ChildrensBook] = relationship("ChildrensBook", back_populates="pages")


class ChildrensBookCharacter(BaseModel):
    """Character consistency sheet for a children's book."""

    __tablename__ = "childrens_book_characters"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("childrens_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    auto_append: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    clothing_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    scale_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    setting_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    time_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    book: Mapped[ChildrensBook] = relationship("ChildrensBook", back_populates="characters")
