"""SQLAlchemy models for the Audiobook Production Studio module."""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class AudiobookStatus(str, enum.Enum):
    DRAFT = "draft"
    CASTING = "casting"
    RECORDING = "recording"
    EDITING = "editing"
    MASTERING = "mastering"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AudiobookChapterStatus(str, enum.Enum):
    PENDING = "pending"
    RECORDING = "recording"
    RECORDED = "recorded"
    EDITING = "editing"
    MASTERED = "mastered"


class VoiceProvider(str, enum.Enum):
    ELEVENLABS = "elevenlabs"
    AMAZON_POLLY = "amazon_polly"
    GOOGLE_TTS = "google_tts"
    CUSTOM = "custom"


class VoiceType(str, enum.Enum):
    SYSTEM = "system"
    CUSTOM = "custom"


class AudiobookProject(TenantModel):
    """An audiobook project linked to a source book."""

    __tablename__ = "audiobook_projects"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[AudiobookStatus] = mapped_column(
        SAEnum(AudiobookStatus, name="audiobook_status", create_constraint=True),
        default=AudiobookStatus.DRAFT,
        server_default="draft",
    )
    narrator_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_voices.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    total_duration_seconds: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Relationships
    chapters = relationship(
        "AudiobookChapter", back_populates="project", lazy="selectin",
        cascade="all, delete-orphan",
    )
    narrator_voice = relationship("AudiobookVoice", foreign_keys=[narrator_voice_id])

    __table_args__ = (
        Index("ix_audiobook_projects_status", "status"),
        Index("ix_audiobook_projects_book_id_org", "book_id", "org_id"),
        Index("ix_audiobook_projects_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_audiobook_projects_org_id_created_at", "org_id", "created_at"),
    )


class AudiobookChapter(TenantModel):
    """A chapter within an audiobook project, mapped from the source manuscript."""

    __tablename__ = "audiobook_chapters"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[AudiobookChapterStatus] = mapped_column(
        SAEnum(AudiobookChapterStatus, name="audiobook_chapter_status", create_constraint=True),
        default=AudiobookChapterStatus.PENDING,
        server_default="pending",
    )
    voice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_voices.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    project = relationship("AudiobookProject", back_populates="chapters")

    __table_args__ = (
        Index("ix_audiobook_chapters_status", "status"),
        Index("ix_audiobook_chapters_order", "project_id", "order_index"),
        Index("ix_audiobook_chapters_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookVoice(TenantModel):
    """A voice profile for audiobook narration (system-provided or custom-cloned)."""

    __tablename__ = "audiobook_voices"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_type: Mapped[VoiceType] = mapped_column(
        SAEnum(VoiceType, name="audiobook_voice_type", create_constraint=True),
        default=VoiceType.SYSTEM,
        server_default="system",
    )
    provider: Mapped[VoiceProvider] = mapped_column(
        SAEnum(VoiceProvider, name="audiobook_voice_provider", create_constraint=True),
        default=VoiceProvider.ELEVENLABS,
        server_default="elevenlabs",
    )
    external_voice_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None,
    )
    preview_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    sample_urls: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    accent: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", server_default="en")
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    __table_args__ = (
        Index("ix_audiobook_voices_type", "voice_type"),
        Index("ix_audiobook_voices_provider", "provider"),
        Index("ix_audiobook_voices_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_audiobook_voices_org_id_created_at", "org_id", "created_at"),
    )
