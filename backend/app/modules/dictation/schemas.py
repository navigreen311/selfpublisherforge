"""Pydantic request/response schemas for the dictation module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums / constants
# ---------------------------------------------------------------------------

VALID_SESSION_STATUSES = ("active", "paused", "ended")
VALID_SESSION_ACTIONS = ("pause", "resume", "end")


# ---------------------------------------------------------------------------
# Session requests
# ---------------------------------------------------------------------------


class SessionCreateRequest(BaseModel):
    """Request to start a new dictation session."""

    title: str | None = Field(None, max_length=500)
    project_id: UUID | None = None
    language: str = Field(default="en", max_length=10)


class SessionUpdateRequest(BaseModel):
    """Request to update a dictation session (pause, resume, end)."""

    action: str = Field(..., pattern="^(pause|resume|end)$")
    raw_transcript: str | None = None
    duration_seconds: int | None = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Refinement requests
# ---------------------------------------------------------------------------


class RefineSessionRequest(BaseModel):
    """Apply style refinement to a session's raw transcript."""

    style_profile_id: UUID | None = None


class RefineTextRequest(BaseModel):
    """One-off refinement of arbitrary text."""

    text: str = Field(..., min_length=1, max_length=100_000)
    style_profile_id: UUID | None = None


# ---------------------------------------------------------------------------
# Command requests
# ---------------------------------------------------------------------------


class CommandCreateRequest(BaseModel):
    """Create a custom voice command."""

    trigger_phrase: str = Field(..., min_length=1, max_length=200)
    action: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Settings requests
# ---------------------------------------------------------------------------


class SettingsUpdateRequest(BaseModel):
    """Update user dictation preferences."""

    auto_punctuation: bool | None = None
    voice_language: str | None = Field(None, max_length=10)
    noise_cancellation: bool | None = None
    auto_save_interval_seconds: int | None = Field(None, ge=5, le=300)
    preferred_style_profile_id: UUID | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    """Dictation session details."""

    id: UUID
    user_id: UUID
    org_id: UUID
    title: str | None
    project_id: UUID | None
    language: str
    status: str
    raw_transcript: str | None
    refined_text: str | None
    refinement_applied: bool
    word_count: int
    words_after_refinement: int | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime


class SessionListItem(BaseModel):
    """Session summary for list view."""

    id: UUID
    title: str | None
    status: str
    word_count: int
    duration_seconds: int
    refinement_applied: bool
    created_at: datetime


class SessionListResponse(BaseModel):
    """Response containing list of dictation sessions."""

    sessions: list[SessionListItem]
    total: int


class RefineResponse(BaseModel):
    """Result of a transcript refinement."""

    refined_text: str
    original_length: int
    refined_length: int
    style_profile_id: UUID | None = None


class CommandResponse(BaseModel):
    """Voice command details."""

    id: UUID
    trigger_phrase: str
    action: str
    description: str | None
    is_system: bool
    org_id: UUID | None
    created_at: datetime


class CommandListResponse(BaseModel):
    """Response containing list of voice commands."""

    commands: list[CommandResponse]
    total: int


class SettingsResponse(BaseModel):
    """User dictation preferences."""

    auto_punctuation: bool
    voice_language: str
    noise_cancellation: bool
    auto_save_interval_seconds: int
    preferred_style_profile_id: UUID | None
