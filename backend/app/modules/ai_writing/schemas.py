"""Pydantic schemas for the AI Writing Studio module."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return timezone-aware UTC now (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GenerationType(str, Enum):
    chapter = "chapter"
    blurb = "blurb"
    outline = "outline"
    title_suggestions = "title_suggestions"
    continue_writing = "continue_writing"
    edit_selection = "edit_selection"
    tone_adjustment = "tone_adjustment"


class ModelPreference(str, Enum):
    auto = "auto"
    claude = "claude"
    gpt4 = "gpt4"
    gemini = "gemini"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    generation_type: GenerationType
    project_id: UUID
    style_profile_id: UUID | None = None
    instructions: str = Field(..., min_length=1, max_length=10000)
    context: dict[str, Any] = Field(default_factory=dict)
    model_preference: ModelPreference = ModelPreference.auto
    stream: bool = True
    quality_checks: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    """Returned when stream=false or as the event:complete payload."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: UUID
    generation_type: GenerationType
    content: str
    tokens_used: int = 0
    quality_results: dict[str, Any] = Field(default_factory=dict)
    model_used: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Chapters / Manuscript
# ---------------------------------------------------------------------------

class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = ""
    order: int = 0
    synopsis: str = ""


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    order: int | None = None
    synopsis: str | None = None


class ChapterContent(BaseModel):
    id: UUID
    book_id: UUID
    title: str
    content: str
    order: int
    synopsis: str = ""
    word_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterReorderItem(BaseModel):
    chapter_id: UUID
    order: int


class ChapterReorderRequest(BaseModel):
    chapters: list[ChapterReorderItem]


class ManuscriptResponse(BaseModel):
    book_id: UUID
    title: str = ""
    chapters: list[ChapterContent] = []
    total_word_count: int = 0


# ---------------------------------------------------------------------------
# Readability
# ---------------------------------------------------------------------------

class ReadabilityScore(BaseModel):
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    gunning_fog: float
    smog_index: float
    word_count: int
    sentence_count: int
    syllable_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float
    reading_level: str


class ManuscriptAnalysis(BaseModel):
    book_id: UUID
    readability: ReadabilityScore
    total_word_count: int
    chapter_count: int
    avg_chapter_word_count: float
    pacing_notes: list[str] = []


# ---------------------------------------------------------------------------
# Outline
# ---------------------------------------------------------------------------

class OutlineChapter(BaseModel):
    title: str
    synopsis: str
    key_points: list[str] = []


class OutlineRequest(BaseModel):
    genre: str = ""
    premise: str = ""
    num_chapters: int = Field(default=12, ge=1, le=100)
    tone: str = ""
    target_audience: str = ""
    additional_instructions: str = ""


class OutlineResponse(BaseModel):
    book_id: UUID
    chapters: list[OutlineChapter]
    summary: str = ""
    generated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Standalone Outline Generation (no book_id required)
# ---------------------------------------------------------------------------

class OutlineGenerateRequest(BaseModel):
    book_title: str
    genre: str
    target_audience: str | None = None
    num_chapters: int = Field(default=12, ge=3, le=50)
    premise: str | None = None
    tone: str = "commercial"  # formal, casual, literary, commercial


class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    description: str
    key_points: list[str] = []
    estimated_word_count: int = 3000


class OutlineGenerateResponse(BaseModel):
    book_title: str
    genre: str
    total_chapters: int
    chapters: list[ChapterOutline]
    synopsis: str


# ---------------------------------------------------------------------------
# Writing Sessions
# ---------------------------------------------------------------------------

class WritingSessionCreate(BaseModel):
    book_id: UUID
    words_written: int = 0
    duration_minutes: int = 0
    chapter_id: UUID | None = None
    notes: str = ""


class WritingSessionRecord(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    words_written: int
    duration_minutes: int
    chapter_id: UUID | None = None
    notes: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}
