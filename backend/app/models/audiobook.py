"""Audiobook production models — voices, projects, chapters, pronunciation, jobs."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
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


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VoiceProvider(str, enum.Enum):
    COQUI_XTTS = "coqui_xtts"
    ELEVENLABS = "elevenlabs"
    PIPER = "piper"
    CUSTOM_CLONE = "custom_clone"


class VoiceType(str, enum.Enum):
    NARRATOR = "narrator"
    CHARACTER = "character"
    CUSTOM = "custom"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AudiobookProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURING = "configuring"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    MASTERING = "mastering"
    COMPLETE = "complete"
    PUBLISHED = "published"


class AudiobookChapterStatus(str, enum.Enum):
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    REVIEW = "review"
    APPROVED = "approved"
    FAILED = "failed"


class JobType(str, enum.Enum):
    CHAPTER_GENERATE = "chapter_generate"
    CHAPTER_REGENERATE = "chapter_regenerate"
    SEGMENT_REGENERATE = "segment_regenerate"
    MASTER_MERGE = "master_merge"
    QUALITY_CHECK = "quality_check"
    FORMAT_CONVERT = "format_convert"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class AudiobookVoice(TenantModel):
    __tablename__ = "audiobook_voices"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[VoiceProvider] = mapped_column(
        SAEnum(VoiceProvider, name="voice_provider", create_constraint=True),
        nullable=False,
    )
    provider_voice_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    voice_type: Mapped[VoiceType] = mapped_column(
        SAEnum(VoiceType, name="voice_type", create_constraint=True),
        nullable=False,
    )
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    age_range: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)
    accent: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", server_default="en")
    sample_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    clone_source_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    voice_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    cost_per_minute: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, default=None
    )
    is_system_voice: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    __table_args__ = (
        Index("ix_audiobook_voices_provider", "provider"),
        Index("ix_audiobook_voices_voice_type", "voice_type"),
        Index("ix_audiobook_voices_active", "active"),
        Index("ix_audiobook_voices_voice_settings_gin", "voice_settings", postgresql_using="gin"),
        Index("ix_audiobook_voices_org_id_created_at", "org_id", "created_at"),
        Index("ix_audiobook_voices_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookProject(TenantModel):
    __tablename__ = "audiobook_projects"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    status: Mapped[AudiobookProjectStatus] = mapped_column(
        SAEnum(AudiobookProjectStatus, name="audiobook_project_status", create_constraint=True),
        default=AudiobookProjectStatus.DRAFT,
        server_default="draft",
    )
    narrator_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_voices.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    character_voices: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    narration_style: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    output_format: Mapped[str] = mapped_column(
        String(20), nullable=False, default="mp3", server_default="mp3"
    )
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100, server_default="44100")
    bit_rate: Mapped[int] = mapped_column(Integer, default=192, server_default="192")
    channels: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    target_platform: Mapped[str] = mapped_column(
        String(50), nullable=False, default="acx", server_default="acx"
    )
    total_chapters: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completed_chapters: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    estimated_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=None
    )
    actual_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0"), server_default="0"
    )
    master_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cover_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Relationships
    narrator_voice = relationship("AudiobookVoice", foreign_keys=[narrator_voice_id])
    chapters = relationship(
        "AudiobookChapter", back_populates="audiobook_project", lazy="selectin"
    )
    generation_jobs = relationship(
        "AudiobookGenerationJob", back_populates="audiobook_project", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_audiobook_projects_status", "status"),
        Index("ix_audiobook_projects_target_platform", "target_platform"),
        Index("ix_audiobook_projects_character_voices_gin", "character_voices", postgresql_using="gin"),
        Index("ix_audiobook_projects_narration_style_gin", "narration_style", postgresql_using="gin"),
        Index("ix_audiobook_projects_metadata_gin", "metadata", postgresql_using="gin"),
        Index("ix_audiobook_projects_settings_gin", "settings", postgresql_using="gin"),
        Index("ix_audiobook_projects_org_id_created_at", "org_id", "created_at"),
        Index("ix_audiobook_projects_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookChapter(BaseModel):
    __tablename__ = "audiobook_chapters"

    audiobook_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter_title: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
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
    ssml_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    waveform_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    generation_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    generation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    quality_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    audio_edits: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    cost_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("0"), server_default="0"
    )

    # Relationships
    audiobook_project = relationship("AudiobookProject", back_populates="chapters")
    voice = relationship("AudiobookVoice", foreign_keys=[voice_id])

    __table_args__ = (
        Index("ix_audiobook_chapters_status", "status"),
        Index("ix_audiobook_chapters_chapter_number", "chapter_number"),
        Index("ix_audiobook_chapters_generation_params_gin", "generation_params", postgresql_using="gin"),
        Index("ix_audiobook_chapters_quality_metrics_gin", "quality_metrics", postgresql_using="gin"),
        Index("ix_audiobook_chapters_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookPronunciation(TenantModel):
    __tablename__ = "audiobook_pronunciation"

    audiobook_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    phonetic: Mapped[str] = mapped_column(String(500), nullable=False)
    ssml_phoneme: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    audio_sample_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    context: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    __table_args__ = (
        Index("ix_audiobook_pronunciation_word", "word"),
        Index("ix_audiobook_pronunciation_active", "active"),
        Index("ix_audiobook_pronunciation_org_id_created_at", "org_id", "created_at"),
        Index("ix_audiobook_pronunciation_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookGenerationJob(BaseModel):
    __tablename__ = "audiobook_generation_jobs"

    audiobook_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audiobook_chapters.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    job_type: Mapped[JobType] = mapped_column(
        SAEnum(JobType, name="audiobook_job_type", create_constraint=True),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="audiobook_job_status", create_constraint=True),
        default=JobStatus.QUEUED,
        server_default="queued",
    )
    priority: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    input_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    # Relationships
    audiobook_project = relationship("AudiobookProject", back_populates="generation_jobs")
    chapter = relationship("AudiobookChapter", foreign_keys=[chapter_id])

    __table_args__ = (
        Index("ix_audiobook_generation_jobs_status", "status"),
        Index("ix_audiobook_generation_jobs_job_type", "job_type"),
        Index("ix_audiobook_generation_jobs_priority", "priority"),
        Index("ix_audiobook_generation_jobs_celery_task_id", "celery_task_id"),
        Index("ix_audiobook_generation_jobs_input_params_gin", "input_params", postgresql_using="gin"),
        Index("ix_audiobook_generation_jobs_output_gin", "output", postgresql_using="gin"),
        Index("ix_audiobook_generation_jobs_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
