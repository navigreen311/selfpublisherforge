"""Pydantic schemas for audiobook generation, regeneration, and approval."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChapterAudioStatus(str, enum.Enum):
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
# Requests
# ---------------------------------------------------------------------------


class GenerateChapterRequest(BaseModel):
    """Request to generate audio for a single chapter."""

    voice_id: UUID | None = Field(None, description="Override the project narrator voice")
    generation_params: dict | None = Field(default=None, description="Custom generation parameters")


class GenerateAllRequest(BaseModel):
    """Request to queue audio generation for all pending chapters."""

    parallel: bool = Field(
        default=False,
        description="Generate chapters in parallel vs sequentially",
    )
    voice_overrides: dict[int, UUID] | None = Field(
        default=None,
        description="Map of chapter_number -> voice_id for per-chapter overrides",
    )


class RegenerateSegmentRequest(BaseModel):
    """Request to regenerate a specific segment of a chapter."""

    replacement_text: str | None = Field(
        None,
        max_length=5000,
        description="Optional replacement text for the segment",
    )
    voice_id: UUID | None = Field(None, description="Override voice for this segment")


class ChapterApproveRequest(BaseModel):
    """Request to approve or request changes for a chapter's audio."""

    approved: bool = Field(..., description="True to approve, False to request changes")
    review_notes: str | None = Field(
        None,
        max_length=2000,
        description="Review feedback notes",
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class GenerationJobResponse(BaseModel):
    """Response for a queued generation job."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audiobook_project_id: UUID
    chapter_id: UUID | None = None
    job_type: str
    status: str
    priority: int
    provider: str | None = None
    input_params: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cost_usd: Decimal = Decimal("0")
    celery_task_id: str | None = None
    created_at: datetime


class GenerateAllResponse(BaseModel):
    """Response for a batch generation request."""

    jobs: list[GenerationJobResponse]
    total_chapters: int
    queued_count: int


class ChapterAudioResponse(BaseModel):
    """Response with chapter audio details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audiobook_project_id: UUID
    chapter_id: UUID | None = None
    chapter_number: int
    chapter_title: str | None = None
    word_count: int = 0
    status: str
    voice_id: UUID | None = None
    audio_url: str | None = None
    waveform_data: dict | None = None
    duration_seconds: float = 0
    file_size_bytes: int = 0
    generation_attempts: int = 0
    quality_metrics: dict = Field(default_factory=dict)
    review_notes: str | None = None
    audio_edits: list = Field(default_factory=list)
    cost_usd: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime


class ChapterAudioFileResponse(BaseModel):
    """Response with pre-signed audio URL and metadata."""

    chapter_id: UUID
    chapter_number: int
    chapter_title: str | None = None
    audio_url: str
    duration_seconds: float
    file_size_bytes: int
    format: str
    sample_rate: int
    bit_rate: int
