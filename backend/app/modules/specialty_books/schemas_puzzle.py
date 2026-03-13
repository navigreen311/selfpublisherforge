"""Pydantic schemas for the Puzzle Book Generator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas_shared import PreflightCheck, TrimSize


class PuzzleType(str, Enum):
    WORD_SEARCH = "word_search"
    CROSSWORD = "crossword"
    MAZE = "maze"
    SUDOKU = "sudoku"
    WORD_SCRAMBLE = "word_scramble"
    CRYPTOGRAM = "cryptogram"
    NUMBER_SEARCH = "number_search"
    WORD_CONNECT = "word_connect"


class PuzzleAudience(str, Enum):
    KIDS = "kids"
    TEEN = "teen"
    ADULT = "adult"
    SENIOR = "senior"


class DifficultyMode(str, Enum):
    FIXED = "fixed"
    PROGRESSIVE = "progressive"
    RANDOM = "random"


class ClueStyle(str, Enum):
    STANDARD = "standard"
    FILL_IN_BLANK = "fill_in_blank"
    SYNONYM = "synonym"
    PLAYFUL = "playful"
    EDUCATIONAL = "educational"


class PuzzleExportFormat(str, Enum):
    PRINT_PDF = "print_pdf"
    KPF = "kpf"
    FIXED_EPUB = "fixed_epub"
    PNG = "png"


class LargePrintScale(int, Enum):
    SCALE_125 = 125
    SCALE_150 = 150
    SCALE_175 = 175


class PuzzleBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    audience: PuzzleAudience = PuzzleAudience.ADULT
    puzzle_config: dict[str, Any] = Field(...)
    difficulty_mode: DifficultyMode = DifficultyMode.PROGRESSIVE
    themes: list[str] | None = None
    seasonal_theme: str | None = Field(None, max_length=100)
    word_difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    clue_style: ClueStyle = ClueStyle.STANDARD
    trim_size: TrimSize = TrimSize.SIZE_8_5X11
    template_id: UUID | None = None


class PuzzleBookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    audience: PuzzleAudience | None = None
    puzzle_config: dict[str, Any] | None = None
    difficulty_mode: DifficultyMode | None = None
    themes: list[str] | None = None
    seasonal_theme: str | None = Field(None, max_length=100)
    word_difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    clue_style: ClueStyle | None = None
    trim_size: TrimSize | None = None


class PuzzleBookResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    author: str
    audience: PuzzleAudience
    puzzle_config: dict[str, Any]
    difficulty_mode: DifficultyMode
    themes: list[str] | None = None
    seasonal_theme: str | None = None
    word_difficulty: str
    clue_style: ClueStyle
    trim_size: TrimSize
    template_id: UUID | None = None
    status: str = "draft"
    qa_score: float | None = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PuzzleBookListResponse(BaseModel):
    items: list[PuzzleBookResponse]
    total: int


class PuzzleCreate(BaseModel):
    puzzle_type: PuzzleType
    theme: str | None = Field(None, max_length=255)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    grid_size: str | None = Field(None, max_length=20)
    word_list: list[str] | None = None
    clues: dict[str, str] | None = None
    title: str | None = Field(None, max_length=255)


class PuzzleUpdate(BaseModel):
    theme: str | None = Field(None, max_length=255)
    difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    grid_size: str | None = Field(None, max_length=20)
    word_list: list[str] | None = None
    clues: dict[str, str] | None = None
    title: str | None = Field(None, max_length=255)


class PuzzleResponse(BaseModel):
    id: UUID
    book_id: UUID
    puzzle_type: PuzzleType
    puzzle_number: int
    theme: str | None = None
    difficulty: str
    difficulty_score: float | None = Field(None, ge=0.0, le=100.0)
    grid_size: str | None = None
    grid_data: dict[str, Any] | None = None
    word_list: list[str] | None = None
    clues: dict[str, str] | None = None
    solution_data: dict[str, Any] | None = None
    content_hash: str | None = None
    is_verified: bool = False
    title: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class GeneratePuzzleRequest(BaseModel):
    puzzle_type: PuzzleType
    theme: str | None = Field(None, max_length=255)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    grid_size: str | None = Field(None, max_length=20)
    word_list: list[str] | None = None
    seed: int | None = None


class GeneratePuzzleResponse(BaseModel):
    puzzle_id: UUID
    puzzle_type: PuzzleType
    grid_data: dict[str, Any]
    solution_data: dict[str, Any]
    word_list: list[str] | None = None
    difficulty_score: float = Field(..., ge=0.0, le=100.0)
    content_hash: str
    is_verified: bool = True


class WordListGenerateRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=255)
    count: int = Field(20, ge=5, le=100)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    min_length: int = Field(3, ge=2, le=20)
    max_length: int = Field(15, ge=3, le=30)


class WordListResponse(BaseModel):
    words: list[str]
    theme: str
    count: int
    difficulty: str


class RemovedWord(BaseModel):
    word: str
    reason: str
    category: str | None = None


class SanitizeWordListRequest(BaseModel):
    words: list[str] = Field(..., min_length=1)
    audience: PuzzleAudience = PuzzleAudience.ADULT


class SanitizeWordListResponse(BaseModel):
    clean_words: list[str]
    removed_words: list[RemovedWord] = Field(default_factory=list)
    total_input: int
    total_clean: int
    total_removed: int


class GenerateCluesRequest(BaseModel):
    style: ClueStyle = ClueStyle.STANDARD
    word_list: list[str] | None = None


class GenerateCluesResponse(BaseModel):
    clues: dict[str, str] = Field(...)
    style: ClueStyle
    total_clues: int


class ClueIssue(BaseModel):
    word: str
    clue: str
    ambiguity_score: float = Field(..., ge=0.0, le=1.0)
    alternatives: list[str] = Field(default_factory=list)
    issue_description: str | None = None


class ClueQAResponse(BaseModel):
    puzzle_id: UUID
    total_clues: int
    issues: list[ClueIssue] = Field(default_factory=list)
    overall_quality: float = Field(..., ge=0.0, le=100.0)
    passed: bool = True


class PuzzleDifficultyScore(BaseModel):
    puzzle_id: UUID
    puzzle_number: int
    puzzle_type: PuzzleType
    difficulty_score: float = Field(..., ge=0.0, le=100.0)
    target_difficulty: str


class DifficultyCalibrationResponse(BaseModel):
    book_id: UUID
    per_puzzle: list[PuzzleDifficultyScore] = Field(default_factory=list)
    distribution: dict[str, int] = Field(default_factory=dict)
    pacing_ok: bool = True
    pacing_notes: list[str] = Field(default_factory=list)
    overall_difficulty: float = Field(..., ge=0.0, le=100.0)


class AnswerKeyResponse(BaseModel):
    book_id: UUID
    generated: bool
    verification_result: dict[str, Any] | None = None
    total_puzzles: int = 0
    verified_count: int = 0
    mismatch_count: int = 0


class LargePrintGenerateRequest(BaseModel):
    scale: LargePrintScale = LargePrintScale.SCALE_150
    trim_size_override: TrimSize | None = None
    aph_compliant: bool = True


class LargePrintResponse(BaseModel):
    variant_book_id: UUID
    source_book_id: UUID
    scale: int
    trim_size: TrimSize
    page_count: int
    aph_compliant: bool
    created_at: datetime


class PuzzleExportRequest(BaseModel):
    format: PuzzleExportFormat
    include_answer_key: bool = True


class PuzzleExportResponse(BaseModel):
    book_id: UUID
    format: PuzzleExportFormat
    url: str
    file_size_bytes: int | None = None
    preflight_results: list[PreflightCheck] | None = None


class PuzzlePreflightResponse(BaseModel):
    book_id: UUID
    checks: list[PreflightCheck] = Field(default_factory=list)
    all_passed: bool = False
    total_checks: int = 0
    passed_count: int = 0
    failed_count: int = 0
