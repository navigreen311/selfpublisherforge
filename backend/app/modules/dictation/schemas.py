"""Pydantic v2 schemas for voice dictation sessions, commands, refinement, and WebSocket messages."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DictationStatus(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    abandoned = "abandoned"


class DictationAction(str, Enum):
    new_paragraph = "new_paragraph"
    new_line = "new_line"
    insert_period = "insert_period"
    insert_comma = "insert_comma"
    insert_question_mark = "insert_question_mark"
    delete_last_sentence = "delete_last_sentence"
    undo = "undo"
    apply_bold = "apply_bold"
    apply_italic = "apply_italic"
    chapter_break = "chapter_break"
    stop_dictation = "stop_dictation"
    read_back = "read_back"


# ---------------------------------------------------------------------------
# Session Schemas
# ---------------------------------------------------------------------------

class DictationSessionCreate(BaseModel):
    book_id: UUID | None = None
    chapter_id: UUID | None = None
    language: str = "en"
    asr_provider: str = "faster_whisper"
    asr_model: str = "large-v3"


class DictationSessionUpdate(BaseModel):
    status: DictationStatus | None = None


class DictationSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    user_id: UUID
    book_id: UUID | None = None
    chapter_id: UUID | None = None
    status: DictationStatus
    duration_seconds: int
    words_dictated: int
    words_after_refinement: int
    raw_transcript: str | None = None
    refined_text: str | None = None
    asr_provider: str
    asr_model: str
    language: str
    audio_recording_url: str | None = None
    refinement_applied: bool
    refinement_style_profile_id: UUID | None = None
    session_metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    ended_at: datetime | None = None


class DictationSessionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    book_id: UUID | None = None
    chapter_id: UUID | None = None
    status: DictationStatus
    duration_seconds: int
    words_dictated: int
    created_at: datetime
    ended_at: datetime | None = None


class DictationSessionListResponse(BaseModel):
    items: list[DictationSessionList]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Refinement Schemas
# ---------------------------------------------------------------------------

class DiffSegment(BaseModel):
    type: str = Field(..., description="One of: added, removed, unchanged, changed")
    original_text: str
    new_text: str
    start_index: int
    end_index: int


class RefineRequest(BaseModel):
    style_profile_id: UUID | None = None
    options: dict[str, Any] | None = Field(
        default=None,
        description="Refinement options: auto_punctuate, remove_fillers, structure_paragraphs, apply_style",
    )


class RefineTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    style_profile_id: UUID | None = None
    options: dict[str, Any] | None = Field(
        default=None,
        description="Refinement options: auto_punctuate, remove_fillers, structure_paragraphs, apply_style",
    )


class RefineResponse(BaseModel):
    raw_text: str
    refined_text: str
    diff: list[DiffSegment]
    style_match_score: float | None = None
    changes_summary: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Command Schemas
# ---------------------------------------------------------------------------

class DictationCommandCreate(BaseModel):
    command_phrase: str = Field(..., min_length=1, max_length=200)
    action: str = Field(..., min_length=1, max_length=100)


class DictationCommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    command_phrase: str
    action: str
    is_system: bool
    active: bool
    created_at: datetime


class DictationCommandList(BaseModel):
    items: list[DictationCommandResponse]
    total: int


# ---------------------------------------------------------------------------
# Settings Schemas
# ---------------------------------------------------------------------------

class DictationSettings(BaseModel):
    language: str = "en"
    auto_refine: bool = False
    voice_commands_enabled: bool = True
    auto_punctuate: bool = True
    remove_fillers: bool = True
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    default_style_profile_id: UUID | None = None


class DictationSettingsUpdate(BaseModel):
    language: str | None = None
    auto_refine: bool | None = None
    voice_commands_enabled: bool | None = None
    auto_punctuate: bool | None = None
    remove_fillers: bool | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    default_style_profile_id: UUID | None = None


# ---------------------------------------------------------------------------
# WebSocket Message Schemas
# ---------------------------------------------------------------------------

class WordTiming(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    confidence: float = Field(ge=0.0, le=1.0)


class DictationClientMessage(BaseModel):
    type: str = Field(..., description="One of: audio_chunk, pause, resume, end_session, set_language")
    data: bytes | None = None
    language: str | None = None


class DictationPartialTranscript(BaseModel):
    type: str = "partial_transcript"
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class DictationFinalTranscript(BaseModel):
    type: str = "final_transcript"
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    words: list[WordTiming]


class DictationVoiceCommand(BaseModel):
    type: str = "voice_command"
    command: str
    action: str


class DictationError(BaseModel):
    type: str = "error"
    message: str
    recoverable: bool


class DictationMetrics(BaseModel):
    type: str = "session_metrics"
    wpm: float
    accuracy: float = Field(ge=0.0, le=1.0)
    duration: int


class DictationRefinementReady(BaseModel):
    type: str = "refinement_ready"
    raw_text: str
    refined_text: str
    diff: list[DiffSegment]
