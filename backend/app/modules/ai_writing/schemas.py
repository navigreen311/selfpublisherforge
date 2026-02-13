"""Pydantic schemas for the AI Writing Studio module."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return timezone-aware UTC now (replaces deprecated datetime.utcnow)."""
    return datetime.now(UTC)


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


class WritingAction(str, Enum):
    """The 6 AI writing actions supported by the Writing Studio."""
    write = "write"
    rewrite = "rewrite"
    expand = "expand"
    shorten = "shorten"
    continue_ = "continue"
    ideas = "ideas"


# ---------------------------------------------------------------------------
# Generation (legacy unified endpoint)
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


# ---------------------------------------------------------------------------
# Action-based Generation (6-action Writing Studio)
# ---------------------------------------------------------------------------

class ActionGenerateRequest(BaseModel):
    """Request schema for the 6-action AI writing generation endpoint.

    Actions:
      - write: Generate new content based on instruction and context
      - rewrite: Improve/rewrite selected text
      - expand: Add detail and elaboration to selected text
      - shorten: Condense selected text while preserving key information
      - continue: Continue writing from cursor position
      - ideas: Brainstorm 5 directions for the next section
    """
    model_config = ConfigDict(protected_namespaces=())

    action: WritingAction = Field(..., description="The writing action to perform")
    project_id: UUID = Field(..., description="ID of the project/book")
    chapter_id: UUID | None = Field(None, description="ID of the current chapter")
    instruction: str = Field(
        "", max_length=10000,
        description="User instruction for what to write/do",
    )
    selected_text: str = Field(
        "", max_length=50000,
        description="Text selected by the user (for rewrite/expand/shorten)",
    )
    context_before: str = Field(
        "", max_length=50000,
        description="Text before cursor position (~500 words for continue action)",
    )
    context_after: str = Field(
        "", max_length=50000,
        description="Text after cursor position",
    )
    chapter_outline: str = Field(
        "", max_length=10000,
        description="Current chapter outline/synopsis for context",
    )
    previous_content: str = Field(
        "", max_length=50000,
        description="Previous chapter content for continuity",
    )
    style_profile: str = Field(
        "", max_length=5000,
        description="Voice/style characteristics (e.g., 'formal, lyrical, sparse')",
    )
    tone: str = Field(
        "", max_length=200,
        description="Tone modifier (e.g., 'suspenseful', 'humorous', 'melancholic')",
    )
    length: str = Field(
        "medium", max_length=50,
        description="Target length: 'short' (~100 words), 'medium' (~300 words), 'long' (~800 words)",
    )
    genre: str = Field("", max_length=200, description="Genre of the work")
    model_preference: ModelPreference = ModelPreference.auto
    stream: bool = True
    quality_checks: list[str] = Field(default_factory=list)


class ActionGenerateResponse(BaseModel):
    """Response for non-streaming action generation."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: UUID
    action: WritingAction
    content: str
    word_count: int = 0
    tokens_used: int = 0
    quality_results: dict[str, Any] = Field(default_factory=dict)
    model_used: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


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
