"""Pydantic v2 schemas for the Children's Book Studio."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AgeRange(str, Enum):
    """Target age range for a children's book."""

    BOARD = "board"  # 0-3, 10-16 pages
    PICTURE = "picture"  # 3-5, 24-32 pages
    EARLY_READER = "early-reader"  # 5-8, 32-48 pages
    CHAPTER = "chapter"  # 8-12, 48-80 pages


class IllustrationStyle(str, Enum):
    WATERCOLOR = "watercolor"
    CARTOON = "cartoon"
    FLAT = "flat"
    STORYBOOK = "storybook"
    REALISTIC = "realistic"
    CRAYON_PENCIL = "crayon-pencil"
    COLLAGE = "collage"
    ANIME_MANGA = "anime-manga"


class ColorPalette(str, Enum):
    BRIGHT_VIBRANT = "bright-vibrant"
    SOFT_PASTEL = "soft-pastel"
    WARM_EARTHY = "warm-earthy"
    COOL_DREAMY = "cool-dreamy"
    MONOCHROME_ACCENT = "monochrome-accent"


class StoryMode(str, Enum):
    PROSE = "prose"
    RHYMING = "rhyming"
    REPETITIVE_CUMULATIVE = "repetitive-cumulative"


class BilingualLayout(str, Enum):
    SIDE_BY_SIDE = "side-by-side"
    ALTERNATING = "alternating"
    BACK_SECTION = "back-section"


class FearIntensity(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"


class PageLayout(str, Enum):
    """Layout options per page (7 layouts)."""

    FULL_BLEED = "full-bleed"
    TOP_IMAGE_BOTTOM_TEXT = "top-image-bottom-text"
    BOTTOM_IMAGE_TOP_TEXT = "bottom-image-top-text"
    LEFT_IMAGE_RIGHT_TEXT = "left-image-right-text"
    RIGHT_IMAGE_LEFT_TEXT = "right-image-left-text"
    TEXT_ONLY = "text-only"
    FULL_BLEED_NO_TEXT = "full-bleed-no-text"


class TextPosition(str, Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class BookStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExportFormat(str, Enum):
    PRINT_PDF = "print-pdf"
    FIXED_LAYOUT_KPF = "fixed-layout-kpf"
    FIXED_LAYOUT_EPUB = "fixed-layout-epub"
    INDIVIDUAL_PAGES = "individual-pages"


class DeviceType(str, Enum):
    KINDLE_FIRE_HD_10 = "kindle-fire-hd-10"
    KINDLE_FIRE_HD_8 = "kindle-fire-hd-8"
    KINDLE_PAPERWHITE = "kindle-paperwhite"
    IPAD = "ipad"
    IPAD_MINI = "ipad-mini"
    IPHONE = "iphone"


class CreationMode(str, Enum):
    AI_GENERATE = "ai-generate"
    WRITE_OWN = "write-own"
    IMPORT_TEXT = "import-text"


class PageType(str, Enum):
    STORY = "story"
    TITLE = "title"
    DEDICATION = "dedication"
    CREDITS = "credits"
    COPYRIGHT = "copyright"


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


class ChildrensBookCreate(BaseModel):
    """Create a new children's book project."""

    title: str = Field(..., min_length=1, max_length=300, description="Book title")
    subtitle: str | None = Field(None, max_length=300, description="Optional subtitle")
    author: str = Field(..., min_length=1, max_length=200, description="Author or pen name")
    age_range: AgeRange = Field(..., description="Target age range")
    page_count: int = Field(
        ...,
        ge=10,
        le=80,
        description="Number of interior pages (varies by age range)",
    )
    trim_size: str = Field(
        ...,
        max_length=20,
        description="Trim size, e.g. '8.5x8.5', '8.5x11', '10x8', '6x9'",
    )
    illustration_style: IllustrationStyle = Field(..., description="Visual illustration style")
    color_palette: ColorPalette = Field(..., description="Color palette for illustrations")
    story_mode: StoryMode = Field(..., description="Story writing mode")
    is_bilingual: bool = Field(False, description="Whether this is a bilingual edition")
    bilingual_language: str | None = Field(
        None,
        max_length=50,
        description="Second language code or name (required if is_bilingual is true)",
    )
    bilingual_layout: BilingualLayout | None = Field(
        None, description="Layout mode for bilingual text (required if is_bilingual is true)"
    )
    fear_intensity: FearIntensity = Field(
        FearIntensity.NONE,
        description="Maximum fear intensity level for content",
    )


class ChildrensBookUpdate(BaseModel):
    """Update an existing children's book. All fields optional."""

    title: str | None = Field(None, min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    author: str | None = Field(None, min_length=1, max_length=200)
    age_range: AgeRange | None = None
    page_count: int | None = Field(None, ge=10, le=80)
    trim_size: str | None = Field(None, max_length=20)
    illustration_style: IllustrationStyle | None = None
    color_palette: ColorPalette | None = None
    story_mode: StoryMode | None = None
    is_bilingual: bool | None = None
    bilingual_language: str | None = Field(None, max_length=50)
    bilingual_layout: BilingualLayout | None = None
    fear_intensity: FearIntensity | None = None


class ChildrensBookResponse(BaseModel):
    """Full children's book record returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    author: str
    age_range: AgeRange
    page_count: int
    trim_size: str
    illustration_style: IllustrationStyle
    color_palette: ColorPalette
    story_mode: StoryMode
    is_bilingual: bool
    bilingual_language: str | None = None
    bilingual_layout: BilingualLayout | None = None
    fear_intensity: FearIntensity
    status: BookStatus
    qa_score: float | None = Field(None, ge=0, le=100, description="Overall QA score")
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


class PageCreate(BaseModel):
    """Create a new page in a children's book."""

    page_number: int = Field(..., ge=1, description="Page position in the book")
    page_type: PageType = Field(PageType.STORY, description="Type of page")
    layout: PageLayout = Field(PageLayout.TOP_IMAGE_BOTTOM_TEXT, description="Page layout")
    text_content: str | None = Field(None, max_length=5000, description="Text on the page")
    translated_text: str | None = Field(None, max_length=5000, description="Translated text for bilingual editions")
    text_font: str | None = Field(None, max_length=100, description="Font family name")
    text_size: int | None = Field(None, ge=10, le=72, description="Font size in points")
    text_color: str | None = Field(None, max_length=20, description="Text color as hex code")
    text_position: TextPosition | None = Field(None, description="Text vertical position")
    text_plate_enabled: bool = Field(False, description="Add a subtle background plate behind text for contrast")
    illustration_prompt: str | None = Field(None, max_length=2000, description="AI illustration generation prompt")


class PageUpdate(BaseModel):
    """Update a page. All fields optional."""

    page_number: int | None = Field(None, ge=1)
    page_type: PageType | None = None
    layout: PageLayout | None = None
    text_content: str | None = Field(None, max_length=5000)
    translated_text: str | None = Field(None, max_length=5000)
    text_font: str | None = Field(None, max_length=100)
    text_size: int | None = Field(None, ge=10, le=72)
    text_color: str | None = Field(None, max_length=20)
    text_position: TextPosition | None = None
    text_plate_enabled: bool | None = None
    illustration_prompt: str | None = Field(None, max_length=2000)


class PageResponse(BaseModel):
    """Full page record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    page_number: int
    page_type: PageType
    layout: PageLayout
    text_content: str | None = None
    translated_text: str | None = None
    text_font: str | None = None
    text_size: int | None = None
    text_color: str | None = None
    text_position: TextPosition | None = None
    text_plate_enabled: bool
    illustration_prompt: str | None = None
    illustration_url: str | None = None
    illustration_model: str | None = None
    illustration_seed: int | None = None
    contrast_score: float | None = Field(None, ge=0, le=100, description="WCAG contrast score")
    gutter_safe: bool | None = Field(None, description="True if content is within gutter safety zone")
    created_at: datetime
    updated_at: datetime


class PageReorderRequest(BaseModel):
    """Reorder pages by providing the new sequence of page IDs."""

    page_ids: list[UUID] = Field(..., min_length=1, description="Ordered list of page IDs in desired sequence")


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


class CharacterCreate(BaseModel):
    """Create a character consistency sheet."""

    name: str = Field(..., min_length=1, max_length=100, description="Character name")
    species: str | None = Field(None, max_length=100, description="Species or type, e.g. 'orange tabby kitten'")
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed visual description appended to illustration prompts",
    )
    auto_append: bool = Field(True, description="Auto-append this description to every page's illustration prompt")
    clothing_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="What the character always wears, e.g. {'collar': 'red with gold bell'}",
    )
    scale_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Size relative to other characters/objects",
    )
    setting_continuity_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Persistent environmental details, e.g. {'gate': 'blue wooden gate'}",
    )
    time_of_day_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Lighting changes across the story",
    )


class CharacterUpdate(BaseModel):
    """Update a character. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=100)
    species: str | None = Field(None, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=2000)
    auto_append: bool | None = None
    clothing_rules: dict[str, Any] | None = None
    scale_rules: dict[str, Any] | None = None
    setting_continuity_rules: dict[str, Any] | None = None
    time_of_day_rules: dict[str, Any] | None = None


class CharacterResponse(BaseModel):
    """Full character sheet record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    name: str
    species: str | None = None
    description: str
    reference_images: list[str] = Field(
        default_factory=list,
        description="URLs of reference images (front, side, happy, scared)",
    )
    auto_append: bool
    clothing_rules: dict[str, Any] = Field(default_factory=dict)
    scale_rules: dict[str, Any] = Field(default_factory=dict)
    setting_continuity_rules: dict[str, Any] = Field(default_factory=dict)
    time_of_day_rules: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# AI Story Generation
# ---------------------------------------------------------------------------


class GenerateStoryRequest(BaseModel):
    """Request AI generation of a full children's story."""

    age_range: AgeRange = Field(..., description="Target age range for vocabulary and length")
    story_prompt: str = Field(..., min_length=1, max_length=2000, description="Story idea or prompt")
    theme: str | None = Field(None, max_length=200, description="Theme or moral, e.g. 'Courage'")
    main_character: str | None = Field(
        None,
        max_length=200,
        description="Main character description, e.g. 'Luna - a small orange tabby kitten'",
    )
    setting: str | None = Field(
        None,
        max_length=200,
        description="Story setting, e.g. 'A cozy village with gardens and woods'",
    )
    tone: str | None = Field(
        None,
        max_length=100,
        description="Story tone: 'warm & reassuring', 'exciting', 'humorous', 'educational'",
    )
    story_mode: StoryMode = Field(..., description="Prose, rhyming, or repetitive-cumulative")


class StoryPageContent(BaseModel):
    """A single page of generated story content."""

    page_number: int = Field(..., ge=1)
    text: str = Field(..., description="Story text for this page")
    illustration_prompt: str = Field(..., description="AI illustration prompt for this page")


class CharacterSheet(BaseModel):
    """Auto-generated character description sheet."""

    name: str
    species: str | None = None
    description: str
    clothing_accessories: str | None = None
    scale_notes: str | None = None


class LanguageReport(BaseModel):
    """Age-band language compliance report."""

    age_range: AgeRange
    max_sentence_length: int
    max_word_length: int
    vocabulary_level: str
    total_word_count: int
    issues: list[str] = Field(default_factory=list, description="Language issues found")
    passed: bool


class StoryGenerationResponse(BaseModel):
    """Full AI-generated story with illustration prompts and metadata."""

    pages: list[StoryPageContent] = Field(..., description="Story content split across pages with illustration prompts")
    character_sheet: CharacterSheet | None = Field(None, description="Auto-generated character description sheet")
    language_report: LanguageReport | None = Field(None, description="Age-band language compliance report")


# ---------------------------------------------------------------------------
# Text Analysis
# ---------------------------------------------------------------------------


class AnalyzeTextRequest(BaseModel):
    """Analyze text readability and pacing for a children's book."""

    book_id: UUID | None = Field(None, description="Book ID to analyze (uses all pages). Mutually exclusive with text.")
    text: str | None = Field(None, max_length=50000, description="Raw text to analyze (alternative to book_id)")
    age_range: AgeRange = Field(..., description="Target age range for scoring")


class TextIssue(BaseModel):
    """A single readability or pacing issue."""

    page_number: int | None = None
    issue_type: str = Field(
        ...,
        description="e.g. 'long-sentence', 'advanced-vocab', 'tongue-twister', 'weak-hook'",
    )
    severity: str = Field(..., description="'info', 'warning', or 'error'")
    description: str
    suggestion: str | None = None


class PageTurnEvent(BaseModel):
    """A page-turn moment with pacing metadata."""

    page_number: int
    surprise_score: float = Field(..., ge=0, le=100, description="How surprising the page turn is")
    is_reveal_moment: bool = Field(..., description="True if this is a story reveal")


class TextAnalysisResponse(BaseModel):
    """Readability and pacing analysis result."""

    readability_score: float = Field(..., ge=0, le=100, description="Overall readability score for target age range")
    rhythm_score: float = Field(..., ge=0, le=100, description="Read-aloud rhythm score")
    issues: list[TextIssue] = Field(default_factory=list, description="Readability and pacing issues")
    page_turn_map: list[PageTurnEvent] = Field(default_factory=list, description="Page-turn surprise and pacing map")
    total_word_count: int = Field(..., ge=0)
    look_inside_hook_score: float | None = Field(
        None, ge=0, le=100, description="Hook strength of the first 10% (Amazon preview)"
    )


# ---------------------------------------------------------------------------
# Continuity Check
# ---------------------------------------------------------------------------


class ContinuityCheckRequest(BaseModel):
    """Check illustration prompt consistency against character sheets and scene rules."""

    book_id: UUID


class ContinuityIssue(BaseModel):
    """A single continuity issue."""

    page_number: int
    issue_type: str = Field(
        ...,
        description="e.g. 'missing-clothing', 'scale-mismatch', 'time-inconsistency', 'style-drift'",
    )
    description: str
    character_name: str | None = None
    fix_suggestion: str | None = None
    auto_fixable: bool = False


class ContinuityReport(BaseModel):
    """Continuity check results."""

    issues: list[ContinuityIssue] = Field(default_factory=list, description="All continuity issues found")
    auto_fixable_count: int = Field(0, ge=0, description="Number of issues that can be auto-fixed")
    total_pages_checked: int = Field(0, ge=0)
    total_characters_checked: int = Field(0, ge=0)


# ---------------------------------------------------------------------------
# Safety Check
# ---------------------------------------------------------------------------


class SafetyCheckRequest(BaseModel):
    """Run trademark and content sensitivity checks."""

    book_id: UUID


class TrademarkIssue(BaseModel):
    """A trademark safety issue."""

    page_number: int | None = None
    location: str = Field(..., description="Where the issue was found: 'prompt', 'text', 'title'")
    flagged_term: str = Field(..., description="The trademarked term detected")
    severity: str = Field(..., description="'warning' or 'block'")
    suggestion: str | None = None


class ContentIssue(BaseModel):
    """A content sensitivity issue."""

    page_number: int | None = None
    issue_type: str = Field(
        ...,
        description="e.g. 'violence', 'fear', 'stereotype', 'mature-theme'",
    )
    description: str
    severity: str = Field(..., description="'info', 'warning', or 'block'")


class SafetyReport(BaseModel):
    """Combined safety check result."""

    trademark_issues: list[TrademarkIssue] = Field(default_factory=list)
    content_issues: list[ContentIssue] = Field(default_factory=list)
    overall_safe: bool = Field(..., description="True if no blocking issues were found")
    font_license_ok: bool = Field(True, description="True if all fonts are commercially licensed")


# ---------------------------------------------------------------------------
# Translation (Bilingual)
# ---------------------------------------------------------------------------


class TranslateRequest(BaseModel):
    """Generate bilingual translation for a book."""

    book_id: UUID
    target_language: str = Field(..., min_length=2, max_length=50, description="Target language code or name")
    layout: BilingualLayout = Field(..., description="Layout mode for bilingual text")
    cultural_adaptation: bool = Field(True, description="Apply cultural adaptation beyond literal translation")


class TranslateResponse(BaseModel):
    """Translation result."""

    pages_translated: int = Field(..., ge=0)
    target_language: str
    layout: BilingualLayout
    language_report: LanguageReport | None = Field(None, description="Reading level validation in target language")
    issues: list[str] = Field(default_factory=list, description="Translation issues or warnings")


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


class ExportRequest(BaseModel):
    """Request to export a children's book."""

    format: ExportFormat = Field(..., description="Export format")
    dpi: int = Field(300, ge=72, le=600, description="Output resolution")
    include_bleed: bool = Field(True, description="Include bleed area")
    color_profile: str | None = Field(None, description="Color profile, e.g. 'sRGB', 'CMYK'")
    include_provenance_report: bool = Field(True, description="Include asset provenance report with export")


class ExportResponse(BaseModel):
    """Export result."""

    url: str = Field(..., description="Download URL for the exported file")
    format: ExportFormat
    file_size_bytes: int | None = None
    preflight_report: dict[str, Any] | None = Field(None, description="Summary of preflight checks run during export")


# ---------------------------------------------------------------------------
# Device Preview
# ---------------------------------------------------------------------------


class DevicePreviewRequest(BaseModel):
    """Generate device-accurate preview images."""

    book_id: UUID
    device: DeviceType = Field(..., description="Target device for preview")
    pages: list[int] | None = Field(None, description="Specific page numbers to preview; None = all pages")


class DevicePreviewResponse(BaseModel):
    """Device preview result."""

    device: DeviceType
    preview_urls: list[str] = Field(..., description="URLs of preview images per page")
    hook_score: float | None = Field(None, ge=0, le=100, description="Look Inside hook score for this device")


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


class PreflightCheck(BaseModel):
    """A single preflight check result."""

    check_name: str = Field(..., description="Name of the check performed")
    passed: bool
    severity: str = Field(..., description="'info', 'warning', or 'error'")
    message: str = Field(..., description="Human-readable result message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional check-specific details")


class PreflightRequest(BaseModel):
    """Run full preflight checks on a children's book."""

    book_id: UUID


class PreflightReport(BaseModel):
    """Full preflight check report."""

    checks: list[PreflightCheck] = Field(..., description="Individual check results")
    passed: bool = Field(..., description="True if all critical checks passed")
    issues: list[str] = Field(
        default_factory=list,
        description="Summary of issues found (warnings + errors)",
    )
    total_checks: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
