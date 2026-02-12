"""Pydantic schemas for the Audiobook module — Voice management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Voice Schemas ─────────────────────────────────────────────────────────


class VoiceResponse(BaseModel):
    """A TTS voice configuration."""

    id: UUID
    org_id: UUID | None = None
    name: str
    provider: str
    provider_voice_id: str | None = None
    voice_type: str
    gender: str | None = None
    age_range: str | None = None
    accent: str | None = None
    language: str = "en"
    sample_audio_url: str | None = None
    clone_source_url: str | None = None
    voice_settings: dict | None = None
    quality_score: float | None = None
    cost_per_minute: float | None = None
    is_system_voice: bool = False
    active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceListResponse(BaseModel):
    """List of voice configurations."""

    items: list[VoiceResponse]
    total: int


class VoiceCloneRequest(BaseModel):
    """Request body for cloning a voice from audio samples."""

    name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(default="custom_clone", max_length=50)
    clone_source_url: str = Field(..., description="URL of the audio sample to clone from")
    voice_type: str = Field(default="custom", max_length=50)
    gender: str | None = Field(None, max_length=20)
    language: str = Field(default="en", max_length=10)
    voice_settings: dict | None = None


class VoicePreviewResponse(BaseModel):
    """Response containing a voice preview audio URL."""

    voice_id: UUID
    text: str
    audio_url: str
    duration_seconds: float | None = None
