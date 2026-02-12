"""Pydantic schemas for extended Audiobook endpoints — CRUD, Voice, Mastering, Export."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Project CRUD Schemas ──────────────────────────────────────────────────


class ProjectCreateRequest(BaseModel):
    """Request body for creating an audiobook project."""

    book_id: UUID
    title: str | None = None
    narrator_voice_id: UUID | None = None
    output_format: str = "mp3"
    target_platform: str = "acx"
    sample_rate: int = 44100
    bit_rate: int = 192
    channels: int = 1


class ProjectUpdateRequest(BaseModel):
    """Request body for updating an audiobook project."""

    title: str | None = None
    narrator_voice_id: UUID | None = None
    character_voices: dict | None = None
    narration_style: dict | None = None
    output_format: str | None = None
    sample_rate: int | None = None
    bit_rate: int | None = None
    channels: int | None = None
    target_platform: str | None = None
    settings: dict | None = None


class ChapterSummary(BaseModel):
    """Summary of a chapter within a project."""

    id: UUID
    chapter_number: int
    chapter_title: str | None = None
    word_count: int
    status: str
    duration_seconds: float = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Response for an audiobook project."""

    id: UUID
    org_id: UUID
    book_id: UUID
    title: str | None
    status: str
    narrator_voice_id: UUID | None
    output_format: str
    target_platform: str
    total_chapters: int
    completed_chapters: int
    total_duration_seconds: int
    estimated_cost: float | None
    actual_cost: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response including chapters and configuration."""

    chapters: list[ChapterSummary] = []
    character_voices: dict | None = None
    narration_style: dict | None = None
    settings: dict | None = None


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    items: list[ProjectResponse]
    total: int
    page: int
    per_page: int


# ── Voice Schemas ─────────────────────────────────────────────────────────


class VoiceResponse(BaseModel):
    """Response for a voice entry."""

    id: UUID
    name: str
    provider: str
    provider_voice_id: str | None
    voice_type: str
    gender: str | None
    age_range: str | None
    accent: str | None
    language: str
    sample_audio_url: str | None
    quality_score: float | None
    cost_per_minute: float | None
    is_system_voice: bool
    active: bool

    model_config = ConfigDict(from_attributes=True)


class VoiceListResponse(BaseModel):
    """List of voices."""

    items: list[VoiceResponse]
    total: int


class VoiceCloneRequest(BaseModel):
    """Request body for cloning a voice from audio samples."""

    name: str = Field(..., min_length=1, max_length=255)
    audio_urls: list[str] = Field(..., min_length=1, max_length=10)
    voice_type: str = "custom"
    gender: str | None = None
    language: str = "en"
    description: str | None = None


class VoicePreviewResponse(BaseModel):
    """Response for a voice preview/audition."""

    voice_id: UUID
    audio_url: str
    duration_seconds: float
    text: str


# ── Mastering Schemas ─────────────────────────────────────────────────────


class MasterRequest(BaseModel):
    """Request body for mastering an audiobook project."""

    target_lufs: float = -20.0
    normalize: bool = True
    noise_gate: bool = True
    output_format: str = "mp3"
    sample_rate: int = 44100
    bit_rate: int = 192


class MasteringJobResponse(BaseModel):
    """Response for a newly created mastering job."""

    job_id: UUID
    project_id: UUID
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MasteringStatusResponse(BaseModel):
    """Status of a mastering job."""

    job_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    progress_percent: int = 0
    master_audio_url: str | None = None


class ACXChapterResult(BaseModel):
    """ACX compliance result for a single chapter."""

    chapter_id: UUID
    chapter_number: int
    passed: bool
    issues: list[str] = []
    peak_db: float | None = None
    rms_db: float | None = None
    noise_floor_db: float | None = None


class ACXValidationResponse(BaseModel):
    """ACX compliance validation result for an entire project."""

    project_id: UUID
    passed: bool
    chapters: list[ACXChapterResult]
    summary: str


# ── Export Schemas ────────────────────────────────────────────────────────


class ExportRequest(BaseModel):
    """Request body for exporting an audiobook project."""

    format: str = Field("mp3", description="mp3, m4b, flac, wav")
    include_chapters: bool = True
    include_cover: bool = True
    platform: str = "acx"

    model_config = ConfigDict(protected_namespaces=())


class ExportJobResponse(BaseModel):
    """Response for an export job."""

    export_id: UUID
    project_id: UUID
    status: str
    format: str
    created_at: datetime
    download_url: str | None = None
    file_size_bytes: int | None = None

    model_config = ConfigDict(protected_namespaces=())


class ExportListResponse(BaseModel):
    """List of export jobs."""

    items: list[ExportJobResponse]
    total: int


class DownloadResponse(BaseModel):
    """Response containing a temporary download link."""

    download_url: str
    expires_at: datetime
    filename: str
    file_size_bytes: int
