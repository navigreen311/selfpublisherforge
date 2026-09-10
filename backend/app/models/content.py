"""Manuscript, Chapter, ChapterVersion, StyleProfile, WritingSession, EditorSettings, and ContentAsset models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class ContentType(str, enum.Enum):
    FICTION = "fiction"
    NONFICTION = "nonfiction"
    POETRY = "poetry"
    SCREENPLAY = "screenplay"


class ManuscriptStatus(str, enum.Enum):
    DRAFT = "draft"
    REVISION = "revision"
    FINAL = "final"
    ARCHIVED = "archived"


class ChapterStatus(str, enum.Enum):
    OUTLINE = "outline"
    DRAFT = "draft"
    REVISION = "revision"
    FINAL = "final"


class AssetType(str, enum.Enum):
    COVER = "cover"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


class Manuscript(BaseModel):
    __tablename__ = "manuscripts"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type", create_constraint=True),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[ManuscriptStatus] = mapped_column(
        SAEnum(ManuscriptStatus, name="manuscript_status", create_constraint=True),
        default=ManuscriptStatus.DRAFT,
        server_default="draft",
    )

    # Relationships
    book = relationship("Book", back_populates="manuscripts")
    chapters = relationship("Chapter", back_populates="manuscript", lazy="selectin")

    __table_args__ = (
        Index("ix_manuscripts_status", "status"),
        Index("ix_manuscripts_content_type", "content_type"),
        Index("ix_manuscripts_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class Chapter(BaseModel):
    __tablename__ = "chapters"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content: Mapped[dict | str | None] = mapped_column(JSONB, nullable=True, default=None)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    target_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        server_default="draft",
    )
    chapter_type: Mapped[str] = mapped_column(
        String(50),
        default="chapter",
        server_default="chapter",
    )
    ai_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="chapters")
    writing_sessions = relationship("WritingSession", back_populates="chapter", lazy="selectin")
    versions = relationship("ChapterVersion", back_populates="chapter", lazy="noload")

    __table_args__ = (
        Index("ix_chapters_status", "status"),
        Index("ix_chapters_order_index", "order_index"),
        Index("ix_chapters_ai_metrics_gin", "ai_metrics", postgresql_using="gin"),
        Index("ix_chapters_content_gin", "content", postgresql_using="gin"),
        Index("ix_chapters_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ChapterVersion(BaseModel):
    """Immutable snapshot of a chapter's content at a point in time."""

    __tablename__ = "chapter_versions"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[dict | str | None] = mapped_column(JSONB, nullable=True, default=None)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Relationships
    chapter = relationship("Chapter", back_populates="versions")
    user = relationship("User")

    __table_args__ = (
        Index(
            "idx_chapter_versions_chapter",
            "chapter_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
        Index("ix_chapter_versions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class StyleProfile(TenantModel):
    __tablename__ = "style_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_fingerprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    vocabulary_stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    sentence_patterns: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    sample_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sample_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    style_card: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    sample_texts: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    tuning_adjustments: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="style_profiles",
        primaryjoin="StyleProfile.org_id == Organization.id",
        foreign_keys="[StyleProfile.org_id]",
    )

    __table_args__ = (
        Index("ix_style_profiles_voice_fingerprint_gin", "voice_fingerprint", postgresql_using="gin"),
        Index("ix_style_profiles_vocabulary_stats_gin", "vocabulary_stats", postgresql_using="gin"),
        Index("ix_style_profiles_sentence_patterns_gin", "sentence_patterns", postgresql_using="gin"),
        Index("ix_style_profiles_sample_sources_gin", "sample_sources", postgresql_using="gin"),
        Index("ix_style_profiles_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_style_profiles_org_id_created_at", "org_id", "created_at"),
    )


class WritingSession(BaseModel):
    __tablename__ = "writing_sessions"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    words_written: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ai_assists_used: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    organization = relationship("Organization")
    user = relationship("User", back_populates="writing_sessions")
    manuscript = relationship("Manuscript")
    book = relationship("Book", back_populates="writing_sessions")
    chapter = relationship("Chapter", back_populates="writing_sessions")

    __table_args__ = (
        Index("idx_writing_sessions_user", "user_id"),
        Index("idx_writing_sessions_manuscript", "manuscript_id"),
        Index("ix_writing_sessions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class EditorSettings(BaseModel):
    """Per-user editor configuration for the Writing Studio."""

    __tablename__ = "editor_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    font_family: Mapped[str] = mapped_column(
        String(100),
        default="Georgia",
        server_default="Georgia",
    )
    font_size: Mapped[int] = mapped_column(
        Integer,
        default=16,
        server_default="16",
    )
    theme: Mapped[str] = mapped_column(
        String(20),
        default="light",
        server_default="light",
    )
    line_height: Mapped[float] = mapped_column(
        Float,
        default=1.8,
        server_default="1.8",
    )
    show_ai_panel: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    show_chapter_panel: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    style_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("style_profiles.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    tone_preference: Mapped[str] = mapped_column(
        String(50),
        default="match_profile",
        server_default="match_profile",
    )
    length_preference: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        server_default="medium",
    )
    auto_save_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=2,
        server_default="2",
    )
    daily_word_goal: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        server_default="1000",
    )

    # Relationships
    user = relationship("User")
    style_profile = relationship("StyleProfile")

    __table_args__ = (Index("ix_editor_settings_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),)


class ContentAsset(TenantModel):
    __tablename__ = "content_assets"

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # Legacy columns (kept for backward-compat with other modules)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=None)
    # Storage-service columns
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    content_type: Mapped[str | None] = mapped_column(String(127), nullable=True, default=None)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="content_assets",
        primaryjoin="ContentAsset.org_id == Organization.id",
        foreign_keys="[ContentAsset.org_id]",
    )

    __table_args__ = (
        Index("ix_content_assets_asset_type", "asset_type"),
        Index("ix_content_assets_mime_type", "mime_type"),
        Index("ix_content_assets_metadata_gin", "metadata", postgresql_using="gin"),
        Index("ix_content_assets_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_content_assets_org_id_created_at", "org_id", "created_at"),
    )
