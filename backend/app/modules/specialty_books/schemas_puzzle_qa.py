"""Pydantic schemas for Puzzle Book QA."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ClueStyle(str, Enum):
    STANDARD = "standard"
    KID_FRIENDLY = "kid_friendly"
    TRIVIA = "trivia"
    THEMED = "themed"


class PuzzleType(str, Enum):
    WORD_SEARCH = "word_search"
    CROSSWORD = "crossword"
    SUDOKU = "sudoku"
    MAZE = "maze"
    SCRAMBLE = "scramble"
    CRYPTOGRAM = "cryptogram"
    NUMBER_SEARCH = "number_search"
    WORD_CONNECT = "word_connect"


class WordDifficulty(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    ADVANCED = "advanced"


class Audience(str, Enum):
    KIDS = "kids"
    TEENS = "teens"
    ADULTS = "adults"
    SENIORS = "seniors"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PacingMode(str, Enum):
    PROGRESSIVE = "progressive"
    FIXED = "fixed"
    MIXED = "mixed"


class LargePrintScale(str, Enum):
    SCALE_125 = "125"
    SCALE_150 = "150"
    SCALE_175 = "175"


class Region(str, Enum):
    US = "US"
    UK = "UK"
    CA = "CA"
    AU = "AU"


class SanitizationStepName(str, Enum):
    OFFENSIVE_LANGUAGE = "offensive_language"
    TRADEMARK = "trademark"
    ABBREVIATION = "abbreviation"
    SPELLING = "spelling"
    DUPLICATE = "duplicate"
    LENGTH = "length"


class GenerateCluesRequest(BaseModel):
    style: ClueStyle = ClueStyle.STANDARD


class ClueMapping(BaseModel):
    word: str
    clue: str
    position: int | None = None
    direction: str | None = None


class GenerateCluesResponse(BaseModel):
    puzzle_id: UUID
    style: ClueStyle
    clues: list[ClueMapping]
    generated_at: datetime


class ClueIssue(BaseModel):
    issue_type: str
    description: str
    severity: str = Field("warning", pattern="^(info|warning|error)$")


class ClueQAResult(BaseModel):
    word: str
    clue: str
    ambiguity_score: int = Field(..., ge=0, le=100)
    issues: list[ClueIssue] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    passed: bool = True


class QACluesResponse(BaseModel):
    puzzle_id: UUID
    total_clues: int
    passed_clues: int
    failed_clues: int
    results: list[ClueQAResult]
    overall_passed: bool


class AutoFixCluesResponse(BaseModel):
    book_id: UUID
    total_fixed: int
    total_skipped: int
    fixes: list[dict[str, Any]] = Field(default_factory=list)


class SanitizeWordListRequest(BaseModel):
    words: list[str] = Field(..., min_length=1)
    audience: Audience = Audience.ADULTS
    difficulty: WordDifficulty = WordDifficulty.STANDARD


class RemovedWord(BaseModel):
    word: str
    step: SanitizationStepName
    reason: str


class SanitizeWordListResponse(BaseModel):
    cleaned_words: list[str]
    removed_words: list[RemovedWord]
    original_count: int
    cleaned_count: int
    steps_applied: list[SanitizationStepName]


class PuzzleDifficultyScore(BaseModel):
    puzzle_id: UUID
    puzzle_type: PuzzleType
    difficulty_score: float = Field(..., ge=0.0, le=100.0)
    difficulty_level: DifficultyLevel
    factors: dict[str, Any] = Field(default_factory=dict)
    position_in_book: int | None = None


class DifficultyDistribution(BaseModel):
    easy_count: int = 0
    easy_pct: float = 0.0
    medium_count: int = 0
    medium_pct: float = 0.0
    hard_count: int = 0
    hard_pct: float = 0.0


class PacingCompliance(BaseModel):
    mode: PacingMode
    compliant: bool
    expected_distribution: dict[str, float] = Field(default_factory=dict)
    actual_distribution: dict[str, float] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)


class CalibrateDifficultyResponse(BaseModel):
    book_id: UUID
    total_puzzles: int
    scores: list[PuzzleDifficultyScore]
    distribution: DifficultyDistribution
    pacing: PacingCompliance
    visualization_data: list[dict[str, Any]] = Field(default_factory=list)


class GenerateLargePrintRequest(BaseModel):
    scale: LargePrintScale = LargePrintScale.SCALE_150


class LargePrintAdjustments(BaseModel):
    grid_size_reduced: bool = False
    words_per_puzzle_reduced: bool = False
    letter_spacing_increased: bool = True
    grid_line_thickness_increased: bool = True
    original_grid_size: str | None = None
    new_grid_size: str | None = None


class GenerateLargePrintResponse(BaseModel):
    source_book_id: UUID
    new_book_id: UUID
    scale: LargePrintScale
    adjustments: LargePrintAdjustments
    created_at: datetime


class AnswerKeyIssue(BaseModel):
    puzzle_id: UUID | None = None
    puzzle_number: int | None = None
    issue_type: str
    description: str
    severity: str = Field("error", pattern="^(info|warning|error)$")


class VerifyAnswerKeyResponse(BaseModel):
    book_id: UUID
    total_puzzles: int
    keys_found: int
    keys_missing: int
    all_verified: bool
    issues: list[AnswerKeyIssue] = Field(default_factory=list)


class RegionalVariantResponse(BaseModel):
    word: str
    variants: dict[str, str] = Field(default_factory=dict)
