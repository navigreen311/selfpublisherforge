"""Extended Pydantic schemas for audiobook project CRUD, voices, mastering, export & download."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Project schemas ──────────────────────────────────────────────────────



class AudiobookCreateFromWizardRequest(BaseModel):
    """Request body for creating an audiobook project via the wizard flow."""

    manuscript_id: UUID = Field(..., description="ID of the manuscript to convert to audiobook.")
    voice_id: str = Field(..., description="Selected voice ID for narration.")
    tier: str = Field(..., description="Service tier.", pattern="^(standard|premium)$")
    target_platform: str = Field(..., description="Target distribution platform.", pattern="^(acx|findaway|custom)$")
    narration_speed: str = Field("normal", description="Narration speed.", pattern="^(slow|normal|fast)$")
    narration_style: str | None = Field(None, description="Optional narration style description.")
    budget_limit: float | None = Field(None, description="Optional budget limit for the project.", ge=0)


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



# ── Statistics & List schemas ────────────────────────────────────────────


class AudiobookStatsResponse(BaseModel):
    """Statistics summary for audiobook projects."""

    total_projects: int = Field(..., description="Total number of audiobook projects.")
    in_progress: int = Field(..., description="Number of projects in progress.")
    completed: int = Field(..., description="Number of completed projects.")
    total_duration_seconds: int = Field(..., description="Total duration of all audiobooks in seconds.")


class AudiobookProjectListItem(BaseModel):
    """Compact audiobook project item for list views."""

    id: UUID
    title: str
    chapter_count: int = 0
    total_duration: int = 0
    narrator: str | None = None
    status: str = "draft"
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    cost_spent: float = 0.0
    cost_budget: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


class VoiceSampleResponse(BaseModel):
    """Response for a voice sample with pricing information."""

    id: UUID
    name: str
    gender: str | None = None
    accent: str | None = None
    description: str | None = None
    sample_url: str | None = None
    tier: str = Field(..., description="Service tier.", pattern="^(standard|premium)$")
    price_per_minute: float = Field(..., description="Price per minute of audio generation.", ge=0)

    model_config = ConfigDict(from_attributes=True)


class VoicePreviewRequest(BaseModel):
    """Request body for generating a voice preview."""

    voice_id: str = Field(..., description="Voice ID to preview.")
    text: str = Field(..., min_length=1, max_length=500, description="Text to synthesize for preview.")
    tier: str = Field(..., description="Service tier.", pattern="^(standard|premium)$")



class VoicePreviewResponse(BaseModel):
    """Response for a voice preview."""

    audio_url: str
    duration_seconds: float = Field(..., description="Duration of the preview audio in seconds.")




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


# ── Creation Wizard schemas ──────────────────────────────────────────────


class WizardCreateRequest(BaseModel):
    """Request body for creating an audiobook project from the creation wizard."""

    manuscript_id: UUID = Field(..., description="ID of the manuscript to create audiobook from.")
    voice_id: UUID = Field(..., description="Primary narrator voice ID.")
    tier: str = Field(..., description="Service tier: free, standard, premium.", pattern="^(free|standard|premium)$")
    platform: str = Field("acx", description="Target distribution platform.", pattern="^(acx|findaway|authors_republic|generic)$")
    speed: float = Field(1.0, description="Narration speed multiplier.", ge=0.5, le=2.0)
    style: str = Field("neutral", description="Narration style preset.")
    budget: float | None = Field(None, description="Optional budget cap in USD.", ge=0)
    title: str | None = Field(None, description="Optional title override.")
    settings: dict[str, Any] | None = Field(None, description="Additional project settings.")

    def model_dump(self, **kwargs):
        """Ensure dict-style access compatibility with service layer."""
        return super().model_dump(**kwargs)


class AudiobookStatsResponse(BaseModel):
    """Statistics for audiobook projects in the organization."""

    total_projects: int = Field(..., description="Total number of audiobook projects.")
    in_progress: int = Field(..., description="Number of projects currently in progress.")
    completed: int = Field(..., description="Number of completed projects.")
    total_duration: float = Field(..., description="Total duration in seconds across all projects.")


class VoicePreviewRequest(BaseModel):
    """Request body for generating a voice preview."""

    voice_id: UUID = Field(..., description="Voice ID to preview.")
    text: str = Field("The quick brown fox jumps over the lazy dog.", max_length=500, description="Sample text to generate.")


class ProjectPauseResponse(BaseModel):
    """Response for pausing a project."""

    project_id: UUID
    status: str
    message: str


class ProjectResumeResponse(BaseModel):
    """Response for resuming a project."""

    project_id: UUID
    status: str
    message: str
