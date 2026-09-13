"""SQLAlchemy models for Comic Books."""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel
from app.modules.specialty.models.enums import (
    BookStatus,
    BorderStyle,
    BubbleType,
    ColorMode,
    ComicArtStyle,
    ComicFormat,
    ComicPacing,
    GutterStyle,
    InkStyle,
    PanelType,
    TargetAudience,
)


class Comic(TenantModel):
    """Master record for a comic book."""

    __tablename__ = "comics"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    artist: Mapped[str | None] = mapped_column(String(200), nullable=True)
    letterer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    colorist: Mapped[str | None] = mapped_column(String(200), nullable=True)

    format: Mapped[str] = mapped_column(
        Enum(ComicFormat, name="comic_format", native_enum=True),
        nullable=False,
        default=ComicFormat.graphic_novel,
    )
    art_style: Mapped[str] = mapped_column(
        Enum(ComicArtStyle, name="comic_art_style", native_enum=True),
        nullable=False,
        default=ComicArtStyle.american_classic,
    )
    color_mode: Mapped[str] = mapped_column(
        Enum(ColorMode, name="comic_color_mode", native_enum=True),
        nullable=False,
        default=ColorMode.full_color,
    )
    ink_style: Mapped[str] = mapped_column(
        Enum(InkStyle, name="comic_ink_style", native_enum=True),
        nullable=False,
        default=InkStyle.clean,
    )
    pacing: Mapped[str] = mapped_column(
        Enum(ComicPacing, name="comic_pacing", native_enum=True),
        nullable=False,
        default=ComicPacing.balanced,
    )
    target_audience: Mapped[str] = mapped_column(
        Enum(TargetAudience, name="comic_target_audience", native_enum=True),
        nullable=False,
        default=TargetAudience.all_ages,
    )

    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    trim_size: Mapped[str] = mapped_column(String(20), nullable=False, default="6.625x10.25")

    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    premise: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    border_style: Mapped[str] = mapped_column(
        Enum(BorderStyle, name="comic_border_style", native_enum=True),
        nullable=False,
        default=BorderStyle.solid,
    )
    gutter_style: Mapped[str] = mapped_column(
        Enum(GutterStyle, name="comic_gutter_style", native_enum=True),
        nullable=False,
        default=GutterStyle.standard,
    )

    content_rating: Mapped[str | None] = mapped_column(String(20), nullable=True)
    violence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    safety_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(BookStatus, name="specialty_book_status", native_enum=True, create_constraint=False),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
    )
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    pages: Mapped[list[ComicPage]] = relationship(
        "app.modules.specialty.models.comic.ComicPage",
        back_populates="comic",
        cascade="all, delete-orphan",
        order_by="ComicPage.page_number",
    )
    characters: Mapped[list[ComicCharacter]] = relationship(
        "app.modules.specialty.models.comic.ComicCharacter",
        back_populates="comic",
        cascade="all, delete-orphan",
    )


class ComicPage(BaseModel):
    """Individual page in a comic book."""

    __tablename__ = "comic_pages"

    comic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str] = mapped_column(String(30), nullable=False, default="story")
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_art_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_template: Mapped[str | None] = mapped_column(String(50), nullable=True)
    panel_count: Mapped[int] = mapped_column(Integer, nullable=False, default=6)

    # Relationships
    comic: Mapped[Comic] = relationship("app.modules.specialty.models.comic.Comic", back_populates="pages")
    panels: Mapped[list[ComicPanel]] = relationship(
        "app.modules.specialty.models.comic.ComicPanel",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="ComicPanel.panel_order",
    )


class ComicPanel(BaseModel):
    """Individual panel within a comic page."""

    __tablename__ = "comic_panels"

    page_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comic_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    panel_order: Mapped[int] = mapped_column(Integer, nullable=False)
    panel_type: Mapped[str] = mapped_column(
        Enum(PanelType, name="comic_panel_type", native_enum=True),
        nullable=False,
        default=PanelType.standard,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    art_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    art_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    art_seed: Mapped[str | None] = mapped_column(String(50), nullable=True)

    border_style: Mapped[str | None] = mapped_column(
        Enum(BorderStyle, name="comic_border_style", native_enum=True, create_constraint=False),
        nullable=True,
    )
    background_color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    page: Mapped[ComicPage] = relationship("app.modules.specialty.models.comic.ComicPage", back_populates="panels")
    bubbles: Mapped[list[ComicBubble]] = relationship(
        "app.modules.specialty.models.comic.ComicBubble",
        back_populates="panel",
        cascade="all, delete-orphan",
        order_by="ComicBubble.bubble_order",
    )


class ComicBubble(BaseModel):
    """Speech/thought bubble within a panel."""

    __tablename__ = "comic_bubbles"

    panel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comic_panels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bubble_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bubble_type: Mapped[str] = mapped_column(
        Enum(BubbleType, name="comic_bubble_type", native_enum=True),
        nullable=False,
        default=BubbleType.speech,
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    character_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    font: Mapped[str | None] = mapped_column(String(100), nullable=True)
    font_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tail_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    panel: Mapped[ComicPanel] = relationship("app.modules.specialty.models.comic.ComicPanel", back_populates="bubbles")


class ComicCharacter(BaseModel):
    """Character definition for a comic book, with expressions/poses/costumes."""

    __tablename__ = "comic_characters"

    comic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)  # hero, villain, supporting
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_images: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    auto_append: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    default_costume: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color_palette: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    comic: Mapped[Comic] = relationship("app.modules.specialty.models.comic.Comic", back_populates="characters")
    expressions: Mapped[list[CharacterExpression]] = relationship(
        "app.modules.specialty.models.comic.CharacterExpression",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    poses: Mapped[list[CharacterPose]] = relationship(
        "app.modules.specialty.models.comic.CharacterPose",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    costumes: Mapped[list[CharacterCostume]] = relationship(
        "app.modules.specialty.models.comic.CharacterCostume",
        back_populates="character",
        cascade="all, delete-orphan",
    )


class CharacterExpression(BaseModel):
    """Named expression for a comic character (happy, angry, etc.)."""

    __tablename__ = "comic_character_expressions"

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comic_characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # happy, sad, angry, etc.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    character: Mapped[ComicCharacter] = relationship(
        "app.modules.specialty.models.comic.ComicCharacter",
        back_populates="expressions",
    )


class CharacterPose(BaseModel):
    """Named pose for a comic character (action, standing, flying, etc.)."""

    __tablename__ = "comic_character_poses"

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comic_characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    character: Mapped[ComicCharacter] = relationship(
        "app.modules.specialty.models.comic.ComicCharacter",
        back_populates="poses",
    )


class CharacterCostume(BaseModel):
    """Named costume/outfit for a comic character."""

    __tablename__ = "comic_character_costumes"

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("comic_characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Relationships
    character: Mapped[ComicCharacter] = relationship(
        "app.modules.specialty.models.comic.ComicCharacter",
        back_populates="costumes",
    )
