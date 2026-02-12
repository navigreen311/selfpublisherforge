"""Pydantic request/response schemas for the audiobook mastering & export module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class MasterAudiobookRequest(BaseModel):
    """Request to start mastering an audiobook."""
    normalize_loudness: bool = Field(default=True, description="Apply LUFS normalization")
    target_lufs: float = Field(default=-20.0, ge=-30.0, le=-10.0)
    noise_reduction: bool = Field(default=True)
    compress_dynamics: bool = Field(default=True)
    crossfade_ms: int = Field(default=500, ge=0, le=5000, description="Crossfade between chapters in ms")


class ExportAudiobookRequest(BaseModel):
    """Request to export an audiobook for a specific platform."""
    format: str = Field(default="mp3", pattern="^(mp3|m4b|flac|wav)$")
    target_platform: str = Field(default="generic", pattern="^(acx|findaway|authors_republic|generic)$")
    bitrate_kbps: int = Field(default=192, ge=64, le=320)
    sample_rate_hz: int = Field(default=44100, ge=22050, le=96000)
    include_metadata: bool = Field(default=True)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class MasteringJobResponse(BaseModel):
    """Response for a mastering job."""
    id: UUID
    audiobook_id: UUID
    status: str
    celery_task_id: str | None
    output_file_url: str | None
    processing_settings: dict | None
    error_message: str | None
    duration_seconds: float | None
    created_at: datetime
    updated_at: datetime


class ExportResponse(BaseModel):
    """Response for an audiobook export."""
    id: UUID
    audiobook_id: UUID
    format: str
    target_platform: str
    status: str
    file_url: str | None
    file_size_bytes: int | None
    celery_task_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DownloadResponse(BaseModel):
    """Response with a pre-signed download URL."""
    export_id: UUID
    download_url: str
    expires_in_seconds: int
    file_size_bytes: int | None
    format: str
    filename: str


class ValidationResultItem(BaseModel):
    """Validation result for a single chapter."""
    chapter_number: int
    chapter_title: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    details: dict | None = None


class ValidationResponse(BaseModel):
    """Aggregate validation response for the audiobook."""
    audiobook_id: UUID
    overall_passed: bool
    total_chapters: int
    chapters_passed: int
    chapters_failed: int
    results: list[ValidationResultItem]
    validated_at: datetime


class ChapterCostItem(BaseModel):
    """Cost breakdown for a single chapter."""
    chapter_number: int
    chapter_title: str
    provider: str | None
    duration_seconds: float | None
    generation_cost_usd: float | None


class CostBreakdownResponse(BaseModel):
    """Detailed cost breakdown for the audiobook project."""
    audiobook_id: UUID
    title: str
    total_cost_usd: float
    total_chapters: int
    total_duration_seconds: float
    chapters: list[ChapterCostItem]
    cost_by_provider: dict[str, float]
