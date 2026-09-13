"""Pydantic v2 schemas for the Puzzle Book Generator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PuzzleType(str, Enum):
    WORD_SEARCH = "word-search"
    CROSSWORD = "crossword"
    MAZE = "maze"
    SUDOKU = "sudoku"
    WORD_SCRAMBLE = "word-scramble"
    CRYPTOGRAM = "cryptogram"
    NUMBER_SEARCH = "number-search"
    WORD_CONNECT = "word-connect"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DifficultyMode(str, Enum):
    """Book-level difficulty progression mode."""

    PROGRESSIVE = "progressive"  # easy -> hard ramp
    FIXED = "fixed"  # same difficulty throughout
    MIXED = "mixed"  # random mix


class ClueStyle(str, Enum):
    STANDARD = "standard"
    KID_FRIENDLY = "kid-friendly"
    TRIVIA = "trivia"
    THEMED = "themed"


class WordDifficulty(str, Enum):
    SIMPLE = "simple"  # 3-6 letters
    STANDARD = "standard"  # 4-10 letters
    ADVANCED = "advanced"  # 6-15 letters


class AnswerKeyPosition(str, Enum):
    BACK_OF_BOOK = "back-of-book"
    REVERSE_OF_PUZZLE = "reverse-of-puzzle"
    NONE = "none"


class LayoutMode(str, Enum):
    ONE_PER_PAGE = "one-per-page"
    TWO_PER_PAGE = "two-per-page"


class PuzzleBookStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PuzzleAudience(str, Enum):
    KIDS = "kids"
    TEENS = "teens"
    ADULTS = "adults"
    LARGE_PRINT = "large-print"


class PuzzleExportFormat(str, Enum):
    PRINT_PDF = "print-pdf"
    INDIVIDUAL_PNG = "individual-png"
    SVG_VECTOR = "svg-vector"


class LargePrintScale(str, Enum):
    SCALE_125 = "125"
    SCALE_150 = "150"
    SCALE_175 = "175"


# ---------------------------------------------------------------------------
# Puzzle type configuration (used in creation wizard)
# ---------------------------------------------------------------------------


class PuzzleTypeConfig(BaseModel):
    """Configuration for a specific puzzle type within a book."""

    puzzle_type: PuzzleType
    quantity: int = Field(..., ge=1, le=200, description="Number of puzzles of this type")
    difficulty: Difficulty = Field(Difficulty.MEDIUM, description="Default difficulty for this type")
    grid_size: str | None = Field(
        None,
        max_length=20,
        description="Grid dimensions, e.g. '15x15', '9x9'. Varies by puzzle type.",
    )


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


class PuzzleBookCreate(BaseModel):
    """Create a new puzzle book project."""

    title: str = Field(..., min_length=1, max_length=300, description="Book title")
    subtitle: str | None = Field(
        None,
        max_length=300,
        description="Optional subtitle (AI may suggest including puzzle types + 'with answers')",
    )
    audience: PuzzleAudience = Field(..., description="Target audience")
    puzzle_config: list[PuzzleTypeConfig] = Field(
        ...,
        min_length=1,
        description="Puzzle types with quantities, difficulty, and grid size",
    )
    difficulty_mode: DifficultyMode = Field(
        DifficultyMode.PROGRESSIVE,
        description="How difficulty progresses through the book",
    )
    themes: list[str] = Field(default_factory=list, description="Theme categories for content")
    seasonal_theme: str | None = Field(
        None, max_length=100, description="Seasonal/holiday theme applied across all puzzles"
    )
    word_difficulty: WordDifficulty = Field(WordDifficulty.STANDARD, description="Word length/difficulty level")
    clue_style: ClueStyle = Field(ClueStyle.STANDARD, description="Style for crossword and other clues")
    answer_key_position: AnswerKeyPosition = Field(
        AnswerKeyPosition.BACK_OF_BOOK, description="Where answer keys appear"
    )
    layout_mode: LayoutMode = Field(LayoutMode.ONE_PER_PAGE, description="Puzzles per page")
    trim_size: str = Field(..., max_length=20, description="Trim size, e.g. '8.5x11'")
    include_toc: bool = Field(True, description="Include table of contents")
    include_instructions: bool = Field(True, description="Include instruction pages per puzzle type")
    include_difficulty_badges: bool = Field(True, description="Show difficulty badge on each puzzle")
    include_section_dividers: bool = Field(True, description="Include divider pages between puzzle type sections")
    include_hints: bool = Field(False, description="Include hint system (crossword first letter, theme hints)")
    series_id: UUID | None = Field(None, description="Series ID if part of a set")
    volume_number: int | None = Field(None, ge=1, description="Volume number in series")


class PuzzleBookUpdate(BaseModel):
    """Update a puzzle book. All fields optional."""

    title: str | None = Field(None, min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    audience: PuzzleAudience | None = None
    puzzle_config: list[PuzzleTypeConfig] | None = None
    difficulty_mode: DifficultyMode | None = None
    themes: list[str] | None = None
    seasonal_theme: str | None = Field(None, max_length=100)
    word_difficulty: WordDifficulty | None = None
    clue_style: ClueStyle | None = None
    answer_key_position: AnswerKeyPosition | None = None
    layout_mode: LayoutMode | None = None
    trim_size: str | None = Field(None, max_length=20)
    include_toc: bool | None = None
    include_instructions: bool | None = None
    include_difficulty_badges: bool | None = None
    include_section_dividers: bool | None = None
    include_hints: bool | None = None
    series_id: UUID | None = None
    volume_number: int | None = Field(None, ge=1)


class PuzzleBookResponse(BaseModel):
    """Full puzzle book record returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    audience: PuzzleAudience
    puzzle_config: list[PuzzleTypeConfig] = Field(default_factory=list)
    difficulty_mode: DifficultyMode
    themes: list[str] = Field(default_factory=list)
    seasonal_theme: str | None = None
    word_difficulty: WordDifficulty
    clue_style: ClueStyle
    answer_key_position: AnswerKeyPosition
    layout_mode: LayoutMode
    trim_size: str
    include_toc: bool
    include_instructions: bool
    include_difficulty_badges: bool
    include_section_dividers: bool
    include_hints: bool
    series_id: UUID | None = None
    volume_number: int | None = None
    status: PuzzleBookStatus
    qa_score: float | None = Field(None, ge=0, le=100, description="Overall QA score")
    total_puzzles: int = Field(0, ge=0)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Individual Puzzle
# ---------------------------------------------------------------------------


class PuzzleClue(BaseModel):
    """A single clue for a crossword or similar puzzle."""

    number: int = Field(..., ge=1)
    direction: str | None = Field(None, description="'across' or 'down' for crosswords")
    clue_text: str = Field(..., max_length=500)
    answer: str = Field(..., max_length=100)
    difficulty: Difficulty | None = None


class PuzzleVerification(BaseModel):
    """Verification data for a puzzle."""

    is_solvable: bool = Field(..., description="True if the puzzle has at least one solution")
    has_unique_solution: bool | None = Field(None, description="True if exactly one solution exists (where applicable)")
    content_hash: str = Field(..., description="Hash for duplicate detection")
    verified_at: datetime | None = None


class PuzzleResponse(BaseModel):
    """Full puzzle record with grid data, clues, and verification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    puzzle_type: PuzzleType
    puzzle_number: int
    theme: str | None = None
    difficulty: Difficulty
    difficulty_score: float | None = Field(None, ge=0, le=100, description="Calculated difficulty score")
    grid_size: str | None = Field(None, description="e.g. '15x15'")
    grid_data: dict[str, Any] | None = Field(None, description="JSON grid structure (cells, walls, etc.)")
    word_list: list[str] = Field(default_factory=list, description="Words used in this puzzle")
    clues: list[PuzzleClue] = Field(default_factory=list, description="Clues for crossword/cryptogram puzzles")
    answer_data: dict[str, Any] | None = Field(
        None, description="Answer key data (filled grid, highlighted paths, etc.)"
    )
    verification: PuzzleVerification | None = Field(None, description="Solvability and uniqueness verification")
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Puzzle Generation
# ---------------------------------------------------------------------------


class GeneratePuzzleRequest(BaseModel):
    """Generate a single puzzle."""

    puzzle_type: PuzzleType = Field(..., description="Type of puzzle to generate")
    theme: str | None = Field(None, max_length=200, description="Theme for content/word selection")
    difficulty: Difficulty = Field(Difficulty.MEDIUM, description="Target difficulty")
    grid_size: str | None = Field(
        None,
        max_length=20,
        description="Grid dimensions, e.g. '15x15'. Uses default for type if not specified.",
    )
    word_list: list[str] | None = Field(
        None,
        description="Custom word list to use (overrides AI generation)",
    )


# ---------------------------------------------------------------------------
# Word List Generation & Sanitization
# ---------------------------------------------------------------------------


class GenerateWordListRequest(BaseModel):
    """AI-generate a themed word list."""

    theme: str = Field(..., min_length=1, max_length=200, description="Theme for word generation")
    count: int = Field(20, ge=5, le=200, description="Number of words to generate")
    difficulty: WordDifficulty = Field(WordDifficulty.STANDARD, description="Word length / difficulty level")
    language: str = Field("en", max_length=10, description="Language code")


class WordListResponse(BaseModel):
    """Generated word list."""

    words: list[str] = Field(..., description="Generated words")
    theme: str
    difficulty: WordDifficulty
    total_count: int = Field(..., ge=0)


class SanitizeWordListRequest(BaseModel):
    """Run sanitization pipeline on a word list."""

    words: list[str] = Field(..., min_length=1, description="Words to sanitize")
    check_offensive: bool = Field(True, description="Filter offensive language")
    check_trademarks: bool = Field(True, description="Filter trademarked terms")
    check_abbreviations: bool = Field(True, description="Filter abbreviations")
    check_spelling: bool = Field(True, description="Validate spelling")
    remove_duplicates: bool = Field(True, description="Remove duplicate words")
    min_length: int | None = Field(None, ge=1, description="Minimum word length")
    max_length: int | None = Field(None, ge=1, description="Maximum word length")


class RemovedWord(BaseModel):
    """A word removed during sanitization with the reason."""

    word: str
    reason: str = Field(
        ..., description="e.g. 'offensive', 'trademark', 'abbreviation', 'misspelling', 'duplicate', 'too-short'"
    )


class SanitizeWordListResponse(BaseModel):
    """Sanitized word list result."""

    clean_words: list[str] = Field(..., description="Words that passed all filters")
    removed_words: list[RemovedWord] = Field(default_factory=list, description="Words removed with reasons")
    original_count: int = Field(..., ge=0)
    clean_count: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Clue Generation & QA
# ---------------------------------------------------------------------------


class GenerateCluesRequest(BaseModel):
    """AI-generate clues for a puzzle."""

    style: ClueStyle = Field(..., description="Clue writing style")
    grade_level: str | None = Field(
        None,
        max_length=50,
        description="Target reading grade level for clues",
    )
    include_hints: bool = Field(False, description="Include hints with clues")


class AmbiguousClue(BaseModel):
    """A clue flagged as potentially ambiguous."""

    clue_number: int
    clue_text: str
    answer: str
    ambiguity_score: float = Field(..., ge=0, le=1, description="How ambiguous the clue is (1 = very ambiguous)")
    alternative_answers: list[str] = Field(default_factory=list, description="Other valid answers for this clue")
    suggested_rewrite: str | None = Field(None, description="AI-suggested unambiguous alternative")


class ClueQAIssue(BaseModel):
    """A clue quality issue."""

    issue_type: str = Field(
        ...,
        description="e.g. 'ambiguous', 'duplicate-phrasing', 'wrong-tense', 'grade-level-mismatch'",
    )
    clue_number: int | None = None
    description: str
    severity: str = Field(..., description="'warning' or 'error'")


class ClueQAResponse(BaseModel):
    """Clue quality assurance result."""

    issues: list[ClueQAIssue] = Field(default_factory=list, description="All clue quality issues")
    ambiguous_clues: list[AmbiguousClue] = Field(default_factory=list, description="Clues flagged as ambiguous")
    total_clues_checked: int = Field(..., ge=0)
    passed: bool = Field(..., description="True if no critical clue issues")


# ---------------------------------------------------------------------------
# Answer Key
# ---------------------------------------------------------------------------


class AnswerKeyResponse(BaseModel):
    """Generated answer key section for the book."""

    book_id: UUID
    position: AnswerKeyPosition
    total_puzzles: int = Field(..., ge=0)
    answer_pages: list[dict[str, Any]] = Field(..., description="Rendered answer key pages with puzzle answers")
    compact_layout: bool = Field(True, description="True if using compact layout (4 answers per page)")


class VerifyAnswerKeyResponse(BaseModel):
    """Verification that all answer keys match their puzzles."""

    all_keys_present: bool = Field(..., description="True if every puzzle has an answer key")
    all_keys_correct: bool = Field(..., description="True if all keys match their puzzles")
    numbering_consistent: bool = Field(
        ..., description="True if puzzle numbering matches between puzzle and key sections"
    )
    missing_answers: list[int] = Field(default_factory=list, description="Puzzle numbers missing answer keys")
    mismatched_answers: list[int] = Field(default_factory=list, description="Puzzle numbers with incorrect answers")
    total_verified: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Difficulty Calibration
# ---------------------------------------------------------------------------


class PuzzleDifficultyScore(BaseModel):
    """Difficulty score for a single puzzle."""

    puzzle_number: int
    puzzle_type: PuzzleType
    difficulty: Difficulty
    score: float = Field(..., ge=0, le=100, description="Calculated difficulty score")
    factors: dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring factors (e.g. grid_density, direction_count, givens_count)",
    )


class PacingAnalysis(BaseModel):
    """Difficulty pacing analysis across the book."""

    mode: DifficultyMode
    distribution: dict[str, int] = Field(..., description="Count of puzzles per difficulty level")
    ramp_quality: float | None = Field(
        None,
        ge=0,
        le=100,
        description="How well the difficulty ramp follows the target progression (progressive mode only)",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Pacing issues, e.g. 'difficulty spike at puzzle #15'",
    )


class DifficultyCalibrationResponse(BaseModel):
    """Difficulty calibration result for the entire book."""

    scores: list[PuzzleDifficultyScore] = Field(..., description="Difficulty score per puzzle")
    distribution_chart: dict[str, Any] = Field(
        ..., description="Data for rendering the difficulty distribution visualization"
    )
    pacing_analysis: PacingAnalysis
    average_score: float = Field(..., ge=0, le=100)


# ---------------------------------------------------------------------------
# Large Print Variant
# ---------------------------------------------------------------------------


class GenerateLargePrintRequest(BaseModel):
    """Create a large print variant of an existing puzzle book."""

    scale: LargePrintScale = Field(LargePrintScale.SCALE_150, description="Scale factor (125%, 150%, or 175%)")
    auto_adjust_grid: bool = Field(True, description="Automatically reduce grid size to fit at larger scale")
    auto_adjust_words: bool = Field(True, description="Automatically reduce words per puzzle if needed")
    increase_letter_spacing: bool = Field(True, description="Increase letter spacing for readability")
    bold_grid_lines: bool = Field(True, description="Use thicker grid lines")


class LargePrintResponse(BaseModel):
    """Created large print variant."""

    model_config = ConfigDict(from_attributes=True)

    original_book_id: UUID
    large_print_book_id: UUID = Field(..., description="ID of the new large print book copy")
    scale: LargePrintScale
    adjustments_made: list[str] = Field(
        default_factory=list,
        description="List of auto-adjustments applied (grid reductions, word removals, etc.)",
    )
    total_puzzles: int = Field(..., ge=0)
    puzzles_modified: int = Field(0, ge=0, description="Number of puzzles that required modifications")
    created_at: datetime


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


class ExportRequest(BaseModel):
    """Export a puzzle book."""

    format: PuzzleExportFormat = Field(..., description="Export format")
    dpi: int = Field(300, ge=72, le=600, description="Output resolution")
    include_bleed: bool = Field(True, description="Include bleed area")
    include_answer_key: bool = Field(True, description="Include answer key section")
    include_toc: bool = Field(True, description="Include table of contents")
    include_instructions: bool = Field(True, description="Include instruction pages")


class PreflightCheck(BaseModel):
    """A single preflight check result."""

    check_name: str
    passed: bool
    severity: str = Field(..., description="'info', 'warning', or 'error'")
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class PreflightRequest(BaseModel):
    """Run full preflight on a puzzle book."""

    book_id: UUID


class PreflightReport(BaseModel):
    """Full preflight report for a puzzle book."""

    checks: list[PreflightCheck] = Field(..., description="Individual check results")
    passed: bool = Field(..., description="True if all critical checks passed")
    issues: list[str] = Field(default_factory=list)
    total_checks: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
