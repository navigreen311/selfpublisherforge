"""Pydantic schemas for the Audiobook module — SSML & Pronunciation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── SSML Schemas ───────────────────────────────────────────────────────────


class DialogueSegment(BaseModel):
    """A detected dialogue segment with character attribution."""

    character: str
    text: str
    emotion: str | None = None
    start_index: int = 0
    end_index: int = 0


class EmotionSegment(BaseModel):
    """A text passage with detected emotional tone."""

    text: str
    emotion: str
    intensity: float = Field(0.5, ge=0.0, le=1.0)
    start_index: int = 0
    end_index: int = 0


class SSMLGenerateRequest(BaseModel):
    """Request body for generating SSML from chapter text."""

    options: dict | None = Field(
        default=None,
        description="Generation options: emphasis_level, pause_duration, etc.",
    )


class SSMLUpdateRequest(BaseModel):
    """Request body for updating SSML text (manual edits)."""

    ssml_text: str = Field(..., min_length=1)


class SSMLResponse(BaseModel):
    """Response containing generated/updated SSML for a chapter."""

    chapter_id: UUID
    original_text: str
    ssml_text: str
    dialogue_segments: list[DialogueSegment] = Field(default_factory=list)
    emotion_segments: list[EmotionSegment] = Field(default_factory=list)


# ── Pronunciation Schemas ──────────────────────────────────────────────────


class PronunciationCreate(BaseModel):
    """Request body for adding a pronunciation entry."""

    word: str = Field(..., min_length=1, max_length=255)
    phonetic: str = Field(..., min_length=1, max_length=500)
    ssml_phoneme: str | None = Field(None, max_length=500)
    context: str | None = None
    audiobook_project_id: UUID | None = None


class PronunciationResponse(BaseModel):
    """A pronunciation dictionary entry."""

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
    """List of pronunciation entries."""

    items: list[PronunciationResponse]
    total: int
