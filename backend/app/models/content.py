"""Manuscript, Chapter, StyleProfile, WritingSession, and ContentAsset models."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[ChapterStatus] = mapped_column(
        SAEnum(ChapterStatus, name="chapter_status", create_constraint=True),
        default=ChapterStatus.OUTLINE,
        server_default="outline",
    )
    ai_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="chapters")
    writing_sessions = relationship("WritingSession", back_populates="chapter", lazy="selectin")

    __table_args__ = (
        Index("ix_chapters_status", "status"),
        Index("ix_chapters_order_index", "order_index"),
        Index("ix_chapters_ai_metrics_gin", "ai_metrics", postgresql_using="gin"),
        Index(
            "ix_chapters_content_fulltext",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
        Index("ix_chapters_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class StyleProfile(TenantModel):
    __tablename__ = "style_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_fingerprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    vocabulary_stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    sentence_patterns: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    sample_sources: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization", back_populates="style_profiles",
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
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

    # Relationships
    user = relationship("User", back_populates="writing_sessions")
    book = relationship("Book", back_populates="writing_sessions")
    chapter = relationship("Chapter", back_populates="writing_sessions")

    __table_args__ = (
        Index("ix_writing_sessions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ContentAsset(TenantModel):
    __tablename__ = "content_assets"

    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, name="asset_type", create_constraint=True),
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=None
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="content_assets",
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
