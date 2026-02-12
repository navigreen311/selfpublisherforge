"""Pydantic schemas for the Audiobook Production Studio module."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AudiobookStatusEnum(str, Enum):
    draft = "draft"
    casting = "casting"
    recording = "recording"
    editing = "editing"
    mastering = "mastering"
    review = "review"
    published = "published"
    archived = "archived"


class AudiobookChapterStatusEnum(str, Enum):
    pending = "pending"
    recording = "recording"
    recorded = "recorded"
    editing = "editing"
    mastered = "mastered"


class VoiceTypeEnum(str, Enum):
    system = "system"
    custom = "custom"


class VoiceProviderEnum(str, Enum):
    elevenlabs = "elevenlabs"
    amazon_polly = "amazon_polly"
    google_tts = "google_tts"
    custom = "custom"


# ---------------------------------------------------------------------------
# Audiobook Project
# ---------------------------------------------------------------------------

class AudiobookProjectCreate(BaseModel):
    book_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    narrator_voice_id: UUID | None = None
    settings: dict | None = None


class AudiobookProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    status: AudiobookStatusEnum | None = None
    narrator_voice_id: UUID | None = None
    settings: dict | None = None


class AudiobookChapterResponse(BaseModel):
    id: UUID
    project_id: UUID
    source_chapter_id: UUID | None = None
    title: str
    order_index: int
    status: AudiobookChapterStatusEnum
    voice_id: UUID | None = None
    audio_url: str | None = None
    duration_seconds: int = 0
    word_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AudiobookProjectResponse(BaseModel):
    id: UUID
    org_id: UUID
    book_id: UUID
    title: str
    status: AudiobookStatusEnum
    narrator_voice_id: UUID | None = None
    settings: dict | None = None
    total_duration_seconds: int = 0
    created_by: UUID | None = None
    chapters: list[AudiobookChapterResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AudiobookProjectListItem(BaseModel):
    id: UUID
    org_id: UUID
    book_id: UUID
    title: str
    status: AudiobookStatusEnum
    narrator_voice_id: UUID | None = None
    total_duration_seconds: int = 0
    chapter_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AudiobookProjectListResponse(BaseModel):
    items: list[AudiobookProjectListItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Voices
# ---------------------------------------------------------------------------

class AudiobookVoiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider: VoiceProviderEnum = VoiceProviderEnum.elevenlabs
    accent: str | None = None
    language: str = "en"
    gender: str | None = None
    settings: dict | None = None


class AudiobookVoiceResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    voice_type: VoiceTypeEnum
    provider: VoiceProviderEnum
    external_voice_id: str | None = None
    preview_url: str | None = None
    accent: str | None = None
    language: str = "en"
    gender: str | None = None
    settings: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VoicePreviewResponse(BaseModel):
    voice_id: UUID
    preview_url: str
    sample_text: str
    duration_seconds: float = 0.0


class DeleteResponse(BaseModel):
    detail: str = "Deleted successfully"
