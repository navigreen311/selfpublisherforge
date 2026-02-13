"""Pydantic schemas for the AI Writing Studio module."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
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


class ChapterType(str, Enum):
    front_matter = "front_matter"
    chapter = "chapter"
    back_matter = "back_matter"


class ManuscriptStatus(str, Enum):
    draft = "draft"
    writing = "writing"
    editing = "editing"
    review = "review"
    complete = "complete"


class ChapterStatus(str, Enum):
    draft = "draft"
    writing = "writing"
    revision = "revision"
    complete = "complete"


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
# Manuscripts
# ---------------------------------------------------------------------------

class ManuscriptCreate(BaseModel):
    """Create a new manuscript, optionally linked to a project."""
    project_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=500)
    type: str = Field(default="book", description="Manuscript type: book, novella, short_story, etc.")


class ManuscriptUpdate(BaseModel):
    """Update manuscript metadata. All fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    status: str | None = None
    target_word_count: int | None = Field(default=None, ge=0)


class ManuscriptResponse(BaseModel):
    book_id: UUID
    title: str = ""
    chapters: list["ChapterContent"] = []
    total_word_count: int = 0


class ManuscriptDetailResponse(BaseModel):
    """Full manuscript with metadata and chapters."""
    id: UUID
    project_id: UUID | None = None
    title: str
    type: str = "book"
    status: str = "draft"
    target_word_count: int | None = None
    total_word_count: int = 0
    chapter_count: int = 0
    chapters: list["ChapterContent"] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManuscriptListItem(BaseModel):
    """Lightweight manuscript item for list views."""
    id: UUID
    project_id: UUID | None = None
    title: str
    type: str = "book"
    status: str = "draft"
    target_word_count: int | None = None
    total_word_count: int = 0
    chapter_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManuscriptListResponse(BaseModel):
    """Paginated list of manuscripts."""
    manuscripts: list[ManuscriptListItem] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Chapters / Manuscript
# ---------------------------------------------------------------------------

class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str | dict[str, Any] = ""
    order: int = 0
    order_index: int | None = Field(default=None, description="Alias for order; takes precedence if set.")
    synopsis: str = ""
    chapter_type: ChapterType = ChapterType.chapter


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | dict[str, Any] | None = None
    order: int | None = None
    synopsis: str | None = None
    status: str | None = None
    target_word_count: int | None = Field(default=None, ge=0)


class ChapterContentSave(BaseModel):
    """Lightweight schema for editor auto-save. Accepts TipTap JSON content."""
    content: dict[str, Any] = Field(..., description="TipTap JSON document content")
    word_count: int = Field(..., ge=0, description="Current word count of the chapter")


class ChapterContent(BaseModel):
    id: UUID
    book_id: UUID
    title: str
    content: str | dict[str, Any]
    order: int
    synopsis: str = ""
    word_count: int = 0
    status: str = "draft"
    chapter_type: str = "chapter"
    target_word_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterReorderItem(BaseModel):
    chapter_id: UUID
    order: int


class ChapterReorderRequest(BaseModel):
    """Reorder chapters. Supports both the legacy format (list of {chapter_id, order})
    and a simplified format (flat list of chapter UUIDs in desired order)."""
    chapters: list[ChapterReorderItem] = Field(default_factory=list)
    chapter_ids: list[UUID] = Field(
        default_factory=list,
        description="Simplified reorder: list of chapter UUIDs in desired order.",
    )


# ---------------------------------------------------------------------------
# Chapter Version History
# ---------------------------------------------------------------------------

class ChapterVersionResponse(BaseModel):
    """Summary of a chapter version (without full content)."""
    id: UUID
    chapter_id: UUID | None = None
    word_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterVersionDetailResponse(ChapterVersionResponse):
    """Full chapter version including content."""
    content: dict[str, Any] = Field(default_factory=dict)


class ChapterVersionListResponse(BaseModel):
    """List of chapter versions."""
    versions: list[ChapterVersionResponse] = []


# ---------------------------------------------------------------------------
# AI Writing (enhanced)
# ---------------------------------------------------------------------------

class AIWriteRequest(BaseModel):
    """Request schema for AI writing actions within the Writing Studio."""
    model_config = ConfigDict(protected_namespaces=())

    manuscript_id: UUID
    chapter_id: UUID
    action: Literal["write", "rewrite", "expand", "shorten", "continue", "ideas"] = Field(
        ..., description="The type of AI writing action to perform."
    )
    instruction: str | None = Field(
        default=None,
        max_length=5000,
        description="Additional instructions for the AI.",
    )
    selected_text: str | None = Field(
        default=None,
        description="Text selected by the user for rewrite/expand/shorten actions.",
    )
    context_before: str | None = Field(
        default=None,
        description="Text preceding the cursor or selection for context.",
    )
    style_profile_id: UUID | None = None
    tone: str | None = Field(
        default=None,
        description="Desired tone: formal, casual, literary, commercial, etc.",
    )
    length: Literal["short", "medium", "long"] | None = Field(
        default=None,
        description="Desired output length.",
    )


class AIWriteResponse(BaseModel):
    """Response schema for AI writing actions."""
    content: str = ""
    tokens_used: int = 0
    action: str = ""
    model_used: str = ""


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
    """Request to compute readability metrics on raw text."""
    text: str = Field(..., min_length=1, description="The text to analyze for readability.")


class ReadabilityResponse(BaseModel):
    """Enhanced readability response with actionable suggestions."""
    grade_level: float = 0.0
    flesch_ease: float = 0.0
    flesch_label: str = "N/A"
    passive_voice_pct: float = 0.0
    avg_sentence_length: float = 0.0
    word_count: int = 0
    suggestions: list[str] = Field(default_factory=list)


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


class WritingSessionStart(BaseModel):
    """Start a new timed writing session."""
    manuscript_id: UUID
    chapter_id: UUID | None = None


class WritingSessionHeartbeat(BaseModel):
    """Periodic heartbeat during a writing session to track progress."""
    words_written: int = Field(..., ge=0)


class WritingSessionEnd(BaseModel):
    """End an active writing session with final stats."""
    words_written: int = Field(..., ge=0)
    duration_seconds: int = Field(..., ge=0)


class WritingSessionResponse(BaseModel):
    """Unified writing session response for list/detail views."""
    id: UUID
    manuscript_title: str = ""
    chapter_title: str | None = None
    words_written: int = 0
    duration: int = Field(default=0, description="Duration in seconds")
    date: datetime = Field(default_factory=_utcnow)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    """Request to export a manuscript in a specific format."""
    format: Literal["docx", "epub", "pdf", "txt", "markdown"] = Field(
        ..., description="The output format for export."
    )


class ExportResponse(BaseModel):
    """Response with download URL for an exported manuscript."""
    download_url: str
    format: str = ""


# ---------------------------------------------------------------------------
# Editor Settings
# ---------------------------------------------------------------------------

class EditorSettingsResponse(BaseModel):
    """Current editor settings for the user."""
    font_family: str = "Georgia"
    font_size: int = 16
    line_height: float = 1.8
    paragraph_spacing: float = 1.5
    page_width: str = "narrow"
    theme: str = "light"
    show_word_count: bool = True
    show_paragraph_count: bool = False
    show_reading_time: bool = True
    autosave_interval_seconds: int = 30
    spell_check: bool = True
    focus_mode: bool = False
    typewriter_mode: bool = False

    model_config = {"from_attributes": True}


class EditorSettingsUpdate(BaseModel):
    """Update editor settings. All fields optional."""
    font_family: str | None = None
    font_size: int | None = Field(default=None, ge=8, le=72)
    line_height: float | None = Field(default=None, ge=1.0, le=3.0)
    paragraph_spacing: float | None = Field(default=None, ge=0.0, le=5.0)
    page_width: str | None = None
    theme: str | None = None
    show_word_count: bool | None = None
    show_paragraph_count: bool | None = None
    show_reading_time: bool | None = None
    autosave_interval_seconds: int | None = Field(default=None, ge=5, le=300)
    spell_check: bool | None = None
    focus_mode: bool | None = None
    typewriter_mode: bool | None = None
