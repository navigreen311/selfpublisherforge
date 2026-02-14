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


class WritingAction(str, Enum):
    write = "write"
    rewrite = "rewrite"
    expand = "expand"
    shorten = "shorten"
    continue_ = "continue"
    ideas = "ideas"


class ModelPreference(str, Enum):
    auto = "auto"
    claude = "claude"
    gpt4 = "gpt4"
    gemini = "gemini"


class ManuscriptStatusEnum(str, Enum):
    draft = "draft"
    revision = "revision"
    final = "final"
    archived = "archived"


class ManuscriptTypeEnum(str, Enum):
    fiction = "fiction"
    nonfiction = "nonfiction"
    poetry = "poetry"
    screenplay = "screenplay"


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
# Action-based generation (6-action Writing Studio)
# ---------------------------------------------------------------------------

class ActionGenerateRequest(BaseModel):
    """Request for a 6-action writing generation (write/rewrite/expand/shorten/continue/ideas)."""
    model_config = ConfigDict(protected_namespaces=())

    action: WritingAction
    project_id: UUID | None = None
    instruction: str = ""
    selected_text: str = ""
    context_before: str = ""
    context_after: str = ""
    chapter_outline: str = ""
    previous_content: str = ""
    style_profile: str = ""
    tone: str = ""
    length: str = ""
    genre: str = ""
    model_preference: ModelPreference = ModelPreference.auto
    stream: bool = True
    quality_checks: list[str] = Field(default_factory=list)


class ActionGenerateResponse(BaseModel):
    """Response from a 6-action writing generation."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: UUID
    action: WritingAction
    content: str
    word_count: int = 0
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


class ChapterContentUpdate(BaseModel):
    """Lightweight body for auto-save of chapter content."""
    content: str


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
# Manuscript CRUD (Writing Studio)
# ---------------------------------------------------------------------------

class ManuscriptCreateRequest(BaseModel):
    """Body for POST /manuscripts."""
    project_id: UUID | None = None
    title: str = Field("Untitled Manuscript", min_length=1, max_length=500)
    type: ManuscriptTypeEnum = ManuscriptTypeEnum.fiction


class ManuscriptUpdateRequest(BaseModel):
    """Body for PATCH /manuscripts/{id}."""
    title: str | None = None
    status: ManuscriptStatusEnum | None = None
    target_word_count: int | None = None


class ManuscriptDetail(BaseModel):
    """Full manuscript representation returned by the API."""
    id: UUID
    book_id: UUID | None = None
    title: str = ""
    status: str = "draft"
    content_type: str = "fiction"
    word_count: int = 0
    target_word_count: int = 0
    chapter_count: int = 0
    chapters: list[ChapterContent] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManuscriptListItem(BaseModel):
    """Summary representation for list endpoint."""
    id: UUID
    book_id: UUID | None = None
    title: str = ""
    status: str = "draft"
    content_type: str = "fiction"
    word_count: int = 0
    target_word_count: int = 0
    chapter_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Chapter Versions
# ---------------------------------------------------------------------------

class ChapterVersionSummary(BaseModel):
    """Summary of a chapter version in a list."""
    id: UUID
    chapter_id: UUID
    version_number: int
    word_count: int = 0
    created_at: datetime
    snapshot_reason: str = ""


class ChapterVersionDetail(BaseModel):
    """Full chapter version with content."""
    id: UUID
    chapter_id: UUID
    version_number: int
    title: str
    content: str
    word_count: int = 0
    created_at: datetime
    snapshot_reason: str = ""


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


class ReadabilityRequest(BaseModel):
    """Body for POST /writing/readability."""
    text: str = Field(..., min_length=1)


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


class WritingSessionStartRequest(BaseModel):
    """Body for POST /writing/sessions/start."""
    manuscript_id: UUID | None = None
    chapter_id: UUID | None = None


class WritingSessionStartResponse(BaseModel):
    """Response for starting a writing session."""
    session_id: UUID
    started_at: datetime


class WritingSessionHeartbeatRequest(BaseModel):
    """Body for POST /writing/sessions/{id}/heartbeat."""
    words_written: int = 0
    current_chapter_id: UUID | None = None


class WritingSessionEndRequest(BaseModel):
    """Body for POST /writing/sessions/{id}/end."""
    words_written: int = 0
    notes: str = ""


class WritingSessionEndResponse(BaseModel):
    """Response for ending a writing session."""
    session_id: UUID
    duration_seconds: int
    words_written: int
    ended_at: datetime


class WritingSessionListItem(BaseModel):
    """Session summary for list endpoint."""
    id: UUID
    user_id: UUID
    manuscript_id: UUID | None = None
    chapter_id: UUID | None = None
    words_written: int = 0
    duration_seconds: int = 0
    started_at: datetime
    ended_at: datetime | None = None
    notes: str = ""


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    """Body for POST /manuscripts/{id}/export."""
    format: str = Field("docx", pattern="^(docx|pdf|epub|markdown|txt)$")
    include_toc: bool = True
    include_metadata: bool = True


class ExportResponse(BaseModel):
    """Response with download information."""
    download_url: str
    format: str
    manuscript_id: UUID
    exported_at: datetime = Field(default_factory=_utcnow)


class ImportResponse(BaseModel):
    """Response after importing a manuscript."""
    manuscript_id: UUID
    title: str
    chapter_count: int
    word_count: int
    imported_at: datetime = Field(default_factory=_utcnow)
