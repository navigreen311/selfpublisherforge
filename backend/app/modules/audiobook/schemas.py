"""Pydantic schemas for the Audiobook module — projects, voices, and chapters."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AudiobookStatus(str, Enum):
    draft = "draft"
    configuring = "configuring"
    generating = "generating"
    reviewing = "reviewing"
    mastering = "mastering"
    complete = "complete"
    published = "published"


class VoiceProvider(str, Enum):
    coqui_xtts = "coqui_xtts"
    elevenlabs = "elevenlabs"
    piper = "piper"
    custom_clone = "custom_clone"


class VoiceType(str, Enum):
    narrator = "narrator"
    character = "character"
    custom = "custom"


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


class ChapterAudioStatus(str, Enum):
    pending = "pending"
    preprocessing = "preprocessing"
    generating = "generating"
    post_processing = "post_processing"
    review = "review"
    approved = "approved"
    failed = "failed"


# ---------------------------------------------------------------------------
# Voice Schemas
# ---------------------------------------------------------------------------

class VoiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    provider: VoiceProvider
    voice_type: VoiceType
    gender: str | None = None
    age_range: str | None = None
    accent: str | None = None
    language: str = "en"
    voice_settings: dict[str, Any] = Field(default_factory=dict)


class VoiceCreate(VoiceBase):
    pass


class VoiceResponse(VoiceBase):
    id: UUID
    org_id: UUID
    provider_voice_id: str | None = None
    sample_audio_url: str | None = None
    clone_source_url: str | None = None
    quality_score: float | None = None
    cost_per_minute: float | None = None
    is_system_voice: bool = False
    active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoicePreviewRequest(BaseModel):
    voice_id: UUID
    sample_text: str = Field(..., max_length=500)


class VoiceCloneRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    provider: VoiceProvider = VoiceProvider.coqui_xtts


# ---------------------------------------------------------------------------
# Project Schemas
# ---------------------------------------------------------------------------

class AudiobookProjectCreate(BaseModel):
    book_id: UUID
    title: str | None = None
    narrator_voice_id: UUID | None = None
    output_format: OutputFormat = OutputFormat.mp3
    sample_rate: int = 44100
    bit_rate: int = 192
    channels: int = 1
    target_platform: TargetPlatform = TargetPlatform.acx
    narration_style: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)


class AudiobookProjectUpdate(BaseModel):
    title: str | None = None
    narrator_voice_id: UUID | None = None
    character_voices: dict[str, Any] | None = None
    narration_style: dict[str, Any] | None = None
    output_format: OutputFormat | None = None
    sample_rate: int | None = None
    bit_rate: int | None = None
    channels: int | None = None
    target_platform: TargetPlatform | None = None
    settings: dict[str, Any] | None = None


class AudiobookProjectResponse(BaseModel):
    id: UUID
    org_id: UUID
    book_id: UUID
    title: str
    status: AudiobookStatus
    narrator_voice_id: UUID | None = None
    character_voices: dict[str, Any] = Field(default_factory=dict)
    narration_style: dict[str, Any] = Field(default_factory=dict)
    output_format: OutputFormat
    sample_rate: int
    bit_rate: int
    channels: int
    target_platform: TargetPlatform
    total_chapters: int = 0
    completed_chapters: int = 0
    total_duration_seconds: float = 0.0
    estimated_cost: float | None = None
    actual_cost: float = 0.0
    master_audio_url: str | None = None
    cover_audio_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class AudiobookProjectList(BaseModel):
    id: UUID
    book_id: UUID
    title: str
    status: AudiobookStatus
    total_chapters: int = 0
    completed_chapters: int = 0
    total_duration_seconds: float = 0.0
    estimated_cost: float | None = None
    actual_cost: float = 0.0
    created_at: datetime


# ---------------------------------------------------------------------------
# Chapter Audio Schemas
# ---------------------------------------------------------------------------

class ChapterAudioResponse(BaseModel):
    id: UUID
    audiobook_project_id: UUID
    chapter_id: UUID | None = None
    chapter_number: int
    chapter_title: str | None = None
    source_text: str
    word_count: int = 0
    status: ChapterAudioStatus
    voice_id: UUID | None = None
    ssml_text: str | None = None
    audio_url: str | None = None
    waveform_data: dict[str, Any] | None = None
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    generation_attempts: int = 0
    quality_metrics: dict[str, Any] = Field(default_factory=dict)
    review_notes: str | None = None
    audio_edits: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class AudiobookProjectListResponse(BaseModel):
    items: list[AudiobookProjectList]
    total: int
    page: int
    page_size: int


class VoiceListResponse(BaseModel):
    items: list[VoiceResponse]
    total: int
