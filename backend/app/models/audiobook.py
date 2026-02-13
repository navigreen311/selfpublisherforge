"""Audiobook production models — voices, projects, chapters, pronunciation, jobs."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel

# ── Enums ──────────────────────────────────────────────────────────────────


class VoiceProvider(str, enum.Enum):
    COQUI_XTTS = "coqui_xtts"
    ELEVENLABS = "elevenlabs"
    PIPER = "piper"
    CUSTOM_CLONE = "custom_clone"


class VoiceType(str, enum.Enum):
    NARRATOR = "narrator"
    CHARACTER = "character"
    CUSTOM = "custom"


class AudiobookStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURING = "configuring"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    MASTERING = "mastering"
    COMPLETE = "complete"
    PUBLISHED = "published"


class ChapterAudioStatus(str, enum.Enum):
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    REVIEW = "review"
    APPROVED = "approved"
    FAILED = "failed"


class AudiobookJobType(str, enum.Enum):
    CHAPTER_GENERATE = "chapter_generate"
    CHAPTER_REGENERATE = "chapter_regenerate"
    SEGMENT_REGENERATE = "segment_regenerate"
    MASTER_MERGE = "master_merge"
    QUALITY_CHECK = "quality_check"
    FORMAT_CONVERT = "format_convert"


class AudiobookJobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ── Models ─────────────────────────────────────────────────────────────────


class AudiobookVoice(TenantModel):
    """A TTS voice configuration for audiobook narration."""

    __tablename__ = "audiobook_voices"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voice_type: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_range: Mapped[str | None] = mapped_column(String(30), nullable=True)
    accent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")
    sample_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    clone_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_per_minute: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    is_system_voice: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (
        Index("ix_audiobook_voices_provider", "provider"),
        Index("ix_audiobook_voices_voice_type", "voice_type"),
        Index("ix_audiobook_voices_active", "active"),
    )


class AudiobookProject(TenantModel):
    """An audiobook project linked to a book."""

    __tablename__ = "audiobook_projects"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="draft", server_default="draft"
    )
    narrator_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_voices.id", ondelete="SET NULL"), nullable=True
    )
    character_voices: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    narration_style: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    output_format: Mapped[str] = mapped_column(
        String(20), default="mp3", server_default="mp3"
    )
    sample_rate: Mapped[int] = mapped_column(
        Integer, default=44100, server_default="44100"
    )
    bit_rate: Mapped[int] = mapped_column(
        Integer, default=192, server_default="192"
    )
    channels: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    target_platform: Mapped[str] = mapped_column(
        String(50), default="acx", server_default="acx"
    )
    total_chapters: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    completed_chapters: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    total_duration_seconds: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    estimated_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    actual_cost: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, server_default="0"
    )
    master_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    settings: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    chapters: Mapped[list["AudiobookChapter"]] = relationship(
        "AudiobookChapter",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AudiobookChapter.chapter_number",
    )

    __table_args__ = (
        Index("ix_audiobook_projects_org_book", "org_id", "book_id"),
        Index("ix_audiobook_projects_status", "status"),
    )


class AudiobookChapter(BaseModel):
    """A chapter within an audiobook project."""

    __tablename__ = "audiobook_chapters"

    audiobook_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(50), default="pending", server_default="pending"
    )
    voice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_voices.id", ondelete="SET NULL"), nullable=True
    )
    ssml_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    waveform_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    generation_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    generation_params: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    quality_metrics: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_edits: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    cost_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 4), default=0, server_default="0"
    )

    # Relationships
    project: Mapped["AudiobookProject"] = relationship(
        "AudiobookProject", back_populates="chapters"
    )

    __table_args__ = (
        Index("ix_audiobook_chapters_project_status", "audiobook_project_id", "status"),
        Index("ix_audiobook_chapters_chapter_number", "chapter_number"),
    )


class AudiobookPronunciation(TenantModel):
    """Custom pronunciation entry for audiobook narration."""

    __tablename__ = "audiobook_pronunciation"

    audiobook_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"), nullable=True
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    phonetic: Mapped[str] = mapped_column(String(500), nullable=False)
    ssml_phoneme: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_sample_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (
        Index("ix_audiobook_pronunciation_org", "org_id"),
        Index("ix_audiobook_pronunciation_project", "audiobook_project_id"),
        Index("ix_audiobook_pronunciation_word", "word"),
    )


class AudiobookGenerationJob(BaseModel):
    """An async generation job for audiobook audio production."""

    __tablename__ = "audiobook_generation_jobs"

    audiobook_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_chapters.id", ondelete="SET NULL"), nullable=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="queued", server_default="queued"
    )
    priority: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 4), default=0, server_default="0"
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_audiobook_generation_jobs_status", "status"),
        Index("ix_audiobook_generation_jobs_job_type", "job_type"),
        Index("ix_audiobook_generation_jobs_priority", "priority"),
        Index("ix_audiobook_generation_jobs_celery_task_id", "celery_task_id"),
    )
