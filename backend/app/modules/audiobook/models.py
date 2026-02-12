"""Audiobook mastering, export, and chapter models."""
import enum
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class AudiobookStatus(str, enum.Enum):
    DRAFT = "draft"
    RECORDING = "recording"
    REVIEWING = "reviewing"
    MASTERING = "mastering"
    MASTERED = "mastered"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChapterStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"


class MasteringStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, enum.Enum):
    MP3 = "mp3"
    M4B = "m4b"
    FLAC = "flac"
    WAV = "wav"


class TargetPlatform(str, enum.Enum):
    ACX = "acx"
    FINDAWAY = "findaway"
    AUTHORS_REPUBLIC = "authors_republic"
    GENERIC = "generic"


class Audiobook(TenantModel):
    __tablename__ = "audiobooks"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    narrator: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[AudiobookStatus] = mapped_column(
        SAEnum(AudiobookStatus, name="audiobook_status", create_constraint=True),
        default=AudiobookStatus.DRAFT,
        server_default="draft",
    )
    total_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    master_file_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    chapters = relationship("AudiobookChapter", back_populates="audiobook", lazy="selectin")
    mastering_jobs = relationship("MasteringJob", back_populates="audiobook", lazy="selectin")
    exports = relationship("AudiobookExport", back_populates="audiobook", lazy="selectin")

    __table_args__ = (
        Index("ix_audiobooks_status", "status"),
        Index("ix_audiobooks_org_status", "org_id", "status"),
        Index("ix_audiobooks_project_id", "project_id"),
        Index("ix_audiobooks_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookChapter(BaseModel):
    __tablename__ = "audiobook_chapters"

    audiobook_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_file_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    status: Mapped[ChapterStatus] = mapped_column(
        SAEnum(ChapterStatus, name="chapter_audio_status", create_constraint=True),
        default=ChapterStatus.PENDING,
        server_default="pending",
    )
    validation_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    generation_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    # Relationships
    audiobook = relationship("Audiobook", back_populates="chapters")

    __table_args__ = (
        Index("ix_audiobook_chapters_status", "status"),
        Index("ix_audiobook_chapters_audiobook_id", "audiobook_id"),
        Index("ix_audiobook_chapters_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class MasteringJob(BaseModel):
    __tablename__ = "mastering_jobs"

    audiobook_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[MasteringStatus] = mapped_column(
        SAEnum(MasteringStatus, name="mastering_status", create_constraint=True),
        default=MasteringStatus.QUEUED,
        server_default="queued",
    )
    output_file_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    processing_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # Relationships
    audiobook = relationship("Audiobook", back_populates="mastering_jobs")

    __table_args__ = (
        Index("ix_mastering_jobs_status", "status"),
        Index("ix_mastering_jobs_audiobook_id", "audiobook_id"),
        Index("ix_mastering_jobs_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AudiobookExport(BaseModel):
    __tablename__ = "audiobook_exports"

    audiobook_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audiobooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[ExportFormat] = mapped_column(
        SAEnum(ExportFormat, name="audiobook_export_format", create_constraint=True),
        nullable=False,
    )
    target_platform: Mapped[TargetPlatform] = mapped_column(
        SAEnum(TargetPlatform, name="audiobook_target_platform", create_constraint=True),
        default=TargetPlatform.GENERIC,
        server_default="generic",
    )
    status: Mapped[ExportStatus] = mapped_column(
        SAEnum(ExportStatus, name="audiobook_export_status", create_constraint=True),
        default=ExportStatus.QUEUED,
        server_default="queued",
    )
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    download_expires_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None,
    )

    # Relationships
    audiobook = relationship("Audiobook", back_populates="exports")

    __table_args__ = (
        Index("ix_audiobook_exports_status", "status"),
        Index("ix_audiobook_exports_audiobook_id", "audiobook_id"),
        Index("ix_audiobook_exports_format", "format"),
        Index("ix_audiobook_exports_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
