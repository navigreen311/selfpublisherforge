"""Extended Pydantic schemas for audiobook project CRUD, voices, mastering, export & download."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Project schemas ──────────────────────────────────────────────────────


class ProjectCreateRequest(BaseModel):
    """Request body for creating an audiobook project."""

    book_id: UUID = Field(..., description="ID of the book to create an audiobook from.")
    title: str | None = Field(None, description="Optional title override (defaults to book title).")
    narrator_voice_id: UUID | None = Field(None, description="Default narrator voice ID.")
    character_voices: dict[str, str] | None = Field(None, description="Mapping of character names to voice IDs.")
    narration_style: dict[str, Any] | None = Field(None, description="Narration style settings.")
    output_format: str = Field("mp3", description="Output audio format.", pattern="^(mp3|m4b|flac|wav)$")
    sample_rate: int = Field(44100, description="Audio sample rate in Hz.")
    bit_rate: int = Field(192, description="Audio bit rate in kbps.")
    channels: int = Field(1, description="Number of audio channels (1=mono, 2=stereo).")
    target_platform: str = Field("acx", description="Target distribution platform.", pattern="^(acx|findaway|authors_republic|generic)$")
    settings: dict[str, Any] | None = Field(None, description="Additional project settings.")
    created_by: UUID | None = Field(None, description="User who created the project.")

    def model_dump(self, **kwargs):
        """Ensure dict-style access compatibility with service layer."""
        return super().model_dump(**kwargs)


class ProjectUpdateRequest(BaseModel):
    """Request body for updating an audiobook project (partial update)."""

    title: str | None = None
    narrator_voice_id: UUID | None = None
    character_voices: dict[str, str] | None = None
    narration_style: dict[str, Any] | None = None
    output_format: str | None = None
    sample_rate: int | None = None
    bit_rate: int | None = None
    channels: int | None = None
    target_platform: str | None = None
    settings: dict[str, Any] | None = None


class ChapterSummary(BaseModel):
    """Summary of a chapter within a project detail response."""

    id: UUID
    chapter_number: int
    chapter_title: str | None = None
    word_count: int = 0
    status: str = "pending"
    duration_seconds: float = 0
    audio_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Response for a single audiobook project."""

    id: UUID
    org_id: UUID
    book_id: UUID
    title: str | None = None
    status: str = "draft"
    narrator_voice_id: UUID | None = None
    output_format: str = "mp3"
    sample_rate: int = 44100
    bit_rate: int = 192
    channels: int = 1
    target_platform: str = "acx"
    total_chapters: int = 0
    completed_chapters: int = 0
    total_duration_seconds: int = 0
    estimated_cost: float | None = None
    actual_cost: float = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed response for a single audiobook project, including chapters."""

    character_voices: dict[str, str] | None = None
    narration_style: dict[str, Any] | None = None
    master_audio_url: str | None = None
    cover_audio_url: str | None = None
    settings: dict[str, Any] | None = None
    chapters: list[ChapterSummary] = []


class ProjectListResponse(BaseModel):
    """Paginated list of audiobook projects."""

    items: list[ProjectResponse]
    total: int
    page: int = 1
    per_page: int = 20


# ── Voice schemas ────────────────────────────────────────────────────────


class VoiceResponse(BaseModel):
    """Response for a single TTS voice."""

    id: UUID
    name: str
    provider: str
    provider_voice_id: str | None = None
    voice_type: str
    gender: str | None = None
    age_range: str | None = None
    accent: str | None = None
    language: str = "en"
    sample_audio_url: str | None = None
    quality_score: float | None = None
    cost_per_minute: float | None = None
    is_system_voice: bool = False
    active: bool = True

    model_config = ConfigDict(from_attributes=True)


class VoiceListResponse(BaseModel):
    """List of available voices."""

    items: list[VoiceResponse]
    total: int


class VoiceCloneRequest(BaseModel):
    """Request body for cloning a voice."""

    name: str = Field(..., min_length=1, max_length=255, description="Name for the cloned voice.")
    provider: str = Field("coqui_xtts", description="TTS provider for cloning.", pattern="^(coqui_xtts|elevenlabs|custom_clone)$")
    voice_type: str = Field("custom", description="Voice type.", pattern="^(narrator|character|custom)$")
    gender: str | None = Field(None, description="Voice gender.")
    language: str = Field("en", description="Language code.")
    clone_source_url: str = Field(..., description="URL to the audio sample for cloning.")
    voice_settings: dict[str, Any] | None = Field(None, description="Additional voice settings.")


class VoicePreviewResponse(BaseModel):
    """Response for a voice preview."""

    voice_id: UUID
    text: str
    audio_url: str
    duration_seconds: float | None = None


# ── Mastering schemas ────────────────────────────────────────────────────


class MasterRequest(BaseModel):
    """Request body for starting the mastering pipeline."""

    target_lufs: float = Field(-16.0, description="Target loudness in LUFS.")
    normalize: bool = Field(True, description="Apply loudness normalization.")
    noise_gate: bool = Field(True, description="Apply noise gate for silence cleanup.")
    output_format: str = Field("mp3", description="Output format.", pattern="^(mp3|m4b|flac|wav)$")
    sample_rate: int = Field(44100, description="Output sample rate in Hz.")
    bit_rate: int = Field(192, description="Output bit rate in kbps.")


class MasteringJobResponse(BaseModel):
    """Response after starting a mastering job."""

    job_id: str
    status: str
    project_id: str


class MasteringStatusResponse(BaseModel):
    """Current mastering job status."""

    job_id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    output: dict[str, Any] | None = None


# ── ACX Validation schemas ───────────────────────────────────────────────


class ACXChapterResult(BaseModel):
    """ACX validation result for a single chapter."""

    chapter_id: str
    chapter_number: int
    passed: bool
    issues: list[str] = []


class ACXValidationSummary(BaseModel):
    """Summary statistics for ACX validation."""

    total: int
    passed: int
    failed: int
    specs: dict[str, str] = {}


class ACXValidationResponse(BaseModel):
    """Full ACX validation response for a project."""

    passed: bool
    chapters: list[ACXChapterResult]
    summary: ACXValidationSummary


# ── Export schemas ───────────────────────────────────────────────────────


class ExportRequest(BaseModel):
    """Request body for starting an audiobook export."""

    format: str = Field(
        ...,
        description="Output audio format.",
        pattern="^(mp3|m4b|flac|wav)$",
    )
    include_chapters: bool = Field(
        True,
        description="Include chapter markers in the exported file.",
    )
    include_cover: bool = Field(
        True,
        description="Embed cover art in the exported file.",
    )
    platform: str = Field(
        "generic",
        description="Target distribution platform.",
        pattern="^(acx|findaway|authors_republic|generic)$",
    )


class ExportJobResponse(BaseModel):
    """Response for a single export job."""

    id: UUID
    audiobook_id: UUID
    format: str
    target_platform: str
    status: str
    file_url: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportListResponse(BaseModel):
    """List of export jobs."""

    items: list[ExportJobResponse]
    total: int


class DownloadResponse(BaseModel):
    """Pre-signed download URL response."""

    download_url: str
    expires_at: datetime
    filename: str
    file_size_bytes: int
