"""Pydantic v2 schemas for audiobook generation, SSML, pronunciation,
mastering, export, ACX validation, cost estimation, and WebSocket events."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GenerationJobType(str, Enum):
    chapter = "chapter"
    full_book = "full_book"
    segment = "segment"
    preview = "preview"


class GenerationJobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    retrying = "retrying"


class OutputFormat(str, Enum):
    mp3 = "mp3"
    wav = "wav"
    flac = "flac"
    m4a = "m4a"
    m4b = "m4b"


class TargetPlatform(str, Enum):
    acx = "acx"
    findawayvoices = "findawayvoices"
    authors_republic = "authors_republic"
    custom = "custom"


class WSEventType(str, Enum):
    generation_progress = "generation_progress"
    generation_complete = "generation_complete"
    generation_failed = "generation_failed"
    mastering_progress = "mastering_progress"
    mastering_complete = "mastering_complete"
    validation_complete = "validation_complete"
    cost_update = "cost_update"


# ---------------------------------------------------------------------------
# Generation Schemas
# ---------------------------------------------------------------------------


class GenerateChapterRequest(BaseModel):
    """Request to generate audio for a single chapter."""

    voice_id: UUID | None = Field(default=None, description="Override the project narrator voice for this chapter")
    generation_params: dict[str, Any] | None = Field(
        default=None,
        description="Provider-specific generation parameters (speed, pitch, stability, etc.)",
    )


class GenerateAllRequest(BaseModel):
    """Request to generate audio for all chapters in the project."""

    parallel: bool = Field(default=False, description="Generate chapters in parallel workers")
    voice_overrides: dict[int, UUID] | None = Field(
        default=None,
        description="Per-chapter voice overrides keyed by chapter_number",
    )


class RegenerateSegmentRequest(BaseModel):
    """Request to regenerate a specific audio segment within a chapter."""

    segment_index: int = Field(..., ge=0, description="Zero-based segment index to regenerate")
    replacement_text: str | None = Field(default=None, description="Optional replacement text for the segment")
    voice_id: UUID | None = Field(default=None, description="Override voice for this segment")


class ChapterApproveRequest(BaseModel):
    """Approve or reject a chapter's generated audio."""

    approved: bool
    review_notes: str | None = Field(default=None, max_length=2000, description="Reviewer notes")


class GenerationJobResponse(BaseModel):
    """Response representing a generation job."""

    id: UUID
    audiobook_project_id: UUID
    chapter_id: UUID | None = None
    job_type: GenerationJobType
    status: GenerationJobStatus
    priority: int = 0
    provider: str | None = None
    input_params: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cost_usd: float = 0.0
    celery_task_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# SSML Schemas
# ---------------------------------------------------------------------------


class DialogueSegment(BaseModel):
    """A detected dialogue segment within chapter text."""

    character: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=1)
    emotion: str | None = None
    start_index: int = Field(..., ge=0)
    end_index: int = Field(..., ge=0)


class EmotionSegment(BaseModel):
    """A detected emotion segment within chapter text."""

    text: str = Field(..., min_length=1)
    emotion: str = Field(..., min_length=1, max_length=100)
    intensity: float = Field(..., ge=0.0, le=1.0, description="Emotion intensity 0-1")
    start_index: int = Field(..., ge=0)
    end_index: int = Field(..., ge=0)


class SSMLGenerateRequest(BaseModel):
    """Request to generate SSML from chapter text (text is pulled from DB)."""

    options: dict[str, Any] | None = Field(
        default=None,
        description="SSML generation options (emphasis_level, pause_duration, etc.)",
    )


class SSMLUpdateRequest(BaseModel):
    """Request to update SSML text directly."""

    ssml_text: str = Field(..., min_length=1, description="Updated SSML markup")


class SSMLResponse(BaseModel):
    """Response with generated SSML and detected segments."""

    chapter_id: UUID
    original_text: str
    ssml_text: str
    dialogue_segments: list[DialogueSegment] = Field(default_factory=list)
    emotion_segments: list[EmotionSegment] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pronunciation Schemas
# ---------------------------------------------------------------------------


class PronunciationCreate(BaseModel):
    """Create a custom pronunciation entry."""

    word: str = Field(..., min_length=1, max_length=200)
    phonetic: str = Field(..., min_length=1, max_length=500)
    ssml_phoneme: str | None = Field(default=None, max_length=500, description="IPA or x-sampa phoneme for SSML")
    context: str | None = Field(default=None, max_length=1000, description="Usage context or example sentence")
    audiobook_project_id: UUID | None = Field(default=None, description="Scope to a specific project (None = org-wide)")


class PronunciationResponse(BaseModel):
    """Pronunciation entry response."""

    id: UUID
    org_id: UUID
    audiobook_project_id: UUID | None = None
    word: str
    phonetic: str
    ssml_phoneme: str | None = None
    audio_sample_url: str | None = None
    context: str | None = None
    active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PronunciationListResponse(BaseModel):
    """Paginated list of pronunciation entries."""

    items: list[PronunciationResponse]
    total: int


# ---------------------------------------------------------------------------
# Mastering & Export Schemas
# ---------------------------------------------------------------------------


class MasterRequest(BaseModel):
    """Audio mastering configuration."""

    normalize: bool = True
    noise_gate: bool = True
    compression: bool = True
    eq: bool = True
    room_tone: bool = True
    target_rms_db: float = Field(
        default=-20.0,
        ge=-30.0,
        le=-10.0,
        description="Target RMS level in dB (ACX requires -23 to -18)",
    )
    target_peak_db: float = Field(
        default=-3.0,
        ge=-10.0,
        le=0.0,
        description="Target peak level in dB (ACX requires -3 or lower)",
    )


class ExportRequest(BaseModel):
    """Request to export the mastered audiobook."""

    format: OutputFormat = OutputFormat.mp3
    platform: TargetPlatform = TargetPlatform.acx
    include_cover_art: bool = True
    include_retail_sample: bool = True


class ExportResponse(BaseModel):
    """Export job response."""

    id: UUID
    status: str
    download_url: str | None = None
    format: str
    platform: str
    file_size_bytes: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ACX Validation Schemas
# ---------------------------------------------------------------------------


class ACXCheck(BaseModel):
    """Individual ACX compliance check result."""

    name: str
    passed: bool
    actual_value: str
    expected_value: str
    auto_fixable: bool = False


class ACXValidationResult(BaseModel):
    """Overall ACX validation result."""

    overall_pass: bool
    score: int = Field(..., ge=0, le=100, description="Compliance score 0-100")
    checks: list[ACXCheck] = Field(default_factory=list)
    auto_fixable_issues: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Cost Schemas
# ---------------------------------------------------------------------------


class CostEstimate(BaseModel):
    """Cost estimate for a single TTS provider."""

    provider: str
    estimated_duration_minutes: float = Field(..., ge=0.0)
    cost_per_minute: float = Field(..., ge=0.0)
    total_cost: float = Field(..., ge=0.0)
    word_count: int = Field(..., ge=0)


class CostBreakdown(BaseModel):
    """Comparative cost breakdown across providers."""

    estimates: list[CostEstimate]
    recommended_provider: str
    total_word_count: int = Field(..., ge=0)
    human_narrator_comparison: float = Field(
        ..., ge=0.0, description="Estimated cost for a human narrator (for comparison)"
    )


# ---------------------------------------------------------------------------
# WebSocket Event Schemas
# ---------------------------------------------------------------------------


class QualityMetrics(BaseModel):
    """Audio quality metrics from analysis."""

    naturalness_score: float = Field(..., ge=0.0, le=1.0)
    clarity_score: float = Field(..., ge=0.0, le=1.0)
    pace_consistency: float = Field(..., ge=0.0, le=1.0)
    pronunciation_accuracy: float = Field(..., ge=0.0, le=1.0)


class AudiobookWSEvent(BaseModel):
    """WebSocket event for real-time audiobook generation updates."""

    type: WSEventType
    chapter_id: UUID | None = None
    percent: float | None = Field(default=None, ge=0.0, le=100.0)
    stage: str | None = None
    eta_seconds: float | None = Field(default=None, ge=0.0)
    audio_url: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    cost_usd: float | None = Field(default=None, ge=0.0)
    quality_metrics: QualityMetrics | None = None
    error: str | None = None
    retry_available: bool | None = None
    master_url: str | None = None
    total_duration: float | None = Field(default=None, ge=0.0)
    total_cost: float | None = Field(default=None, ge=0.0)
    results: ACXValidationResult | None = None
    budget_remaining: float | None = Field(default=None, ge=0.0)
