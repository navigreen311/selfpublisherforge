"""Pydantic schemas for the Children's Book Studio."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas_shared import PreflightCheck, TrimSize


class AgeRange(str, Enum):
    BABY = "0-2"
    TODDLER = "2-4"
    EARLY_READER = "4-6"
    READER = "6-8"
    MIDDLE_GRADE = "8-12"


class IllustrationStyle(str, Enum):
    WATERCOLOR = "watercolor"
    DIGITAL_CARTOON = "digital_cartoon"
    FLAT_VECTOR = "flat_vector"
    PENCIL_SKETCH = "pencil_sketch"
    COLLAGE = "collage"
    PIXEL_ART = "pixel_art"
    STORYBOOK_CLASSIC = "storybook_classic"
    ANIME = "anime"


class StoryMode(str, Enum):
    PROSE = "prose"
    RHYMING = "rhyming"
    REPETITIVE = "repetitive"


class CreationMode(str, Enum):
    AI_GENERATE = "ai_generate"
    UPLOAD_OWN = "upload_own"
    HYBRID = "hybrid"


class PageLayout(str, Enum):
    FULL_BLEED_IMAGE = "full_bleed_image"
    IMAGE_TOP_TEXT_BOTTOM = "image_top_text_bottom"
    IMAGE_LEFT_TEXT_RIGHT = "image_left_text_right"
    IMAGE_RIGHT_TEXT_LEFT = "image_right_text_left"
    TEXT_OVERLAY = "text_overlay"
    VIGNETTE_CENTER = "vignette_center"
    SPLIT_SPREAD = "split_spread"


class PageType(str, Enum):
    COVER = "cover"
    TITLE = "title"
    DEDICATION = "dedication"
    STORY = "story"
    BACK_COVER = "back_cover"


class BilingualLayout(str, Enum):
    SIDE_BY_SIDE = "side_by_side"
    TOP_BOTTOM = "top_bottom"
    ALTERNATE_PAGES = "alternate_pages"


class ExportFormat(str, Enum):
    PRINT_PDF = "print_pdf"
    KPF = "kpf"
    FIXED_EPUB = "fixed_epub"
    PNG = "png"


class DeviceType(str, Enum):
    KINDLE_FIRE_HD_10 = "kindle_fire_hd_10"
    KINDLE_FIRE_HD_8 = "kindle_fire_hd_8"
    KINDLE_PAPERWHITE = "kindle_paperwhite"
    IPAD = "ipad"
    IPAD_MINI = "ipad_mini"
    IPHONE = "iphone"


class FearIntensity(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"


class ChildrensBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    age_range: AgeRange
    page_count: int = Field(24, ge=8, le=64)
    trim_size: TrimSize = TrimSize.SIZE_8_5X8_5
    illustration_style: IllustrationStyle = IllustrationStyle.WATERCOLOR
    color_palette: str | None = Field(None, max_length=255)
    story_mode: StoryMode = StoryMode.PROSE
    creation_mode: CreationMode = CreationMode.AI_GENERATE
    theme_moral: str | None = Field(None, max_length=500)
    main_character: str | None = Field(None, max_length=255)
    setting: str | None = Field(None, max_length=500)
    tone: str | None = Field(None, max_length=255)
    is_bilingual: bool = False
    bilingual_language: str | None = Field(None, max_length=50)
    bilingual_layout: BilingualLayout | None = None
    fear_intensity: FearIntensity = FearIntensity.NONE
    safety_settings: dict[str, Any] | None = None


class ChildrensBookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    age_range: AgeRange | None = None
    page_count: int | None = Field(None, ge=8, le=64)
    trim_size: TrimSize | None = None
    illustration_style: IllustrationStyle | None = None
    color_palette: str | None = Field(None, max_length=255)
    story_mode: StoryMode | None = None
    creation_mode: CreationMode | None = None
    theme_moral: str | None = Field(None, max_length=500)
    main_character: str | None = Field(None, max_length=255)
    setting: str | None = Field(None, max_length=500)
    tone: str | None = Field(None, max_length=255)
    is_bilingual: bool | None = None
    bilingual_language: str | None = Field(None, max_length=50)
    bilingual_layout: BilingualLayout | None = None
    fear_intensity: FearIntensity | None = None
    safety_settings: dict[str, Any] | None = None


class ChildrensBookResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    author: str
    age_range: AgeRange
    page_count: int
    trim_size: TrimSize
    illustration_style: IllustrationStyle
    color_palette: str | None = None
    story_mode: StoryMode
    creation_mode: CreationMode
    theme_moral: str | None = None
    main_character: str | None = None
    setting: str | None = None
    tone: str | None = None
    is_bilingual: bool = False
    bilingual_language: str | None = None
    bilingual_layout: BilingualLayout | None = None
    fear_intensity: FearIntensity = FearIntensity.NONE
    safety_settings: dict[str, Any] | None = None
    status: str = "draft"
    qa_score: float | None = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ChildrensBookListResponse(BaseModel):
    items: list[ChildrensBookResponse]
    total: int


class PageCreate(BaseModel):
    page_number: int = Field(..., ge=1, le=64)
    page_type: PageType = PageType.STORY
    layout: PageLayout = PageLayout.IMAGE_TOP_TEXT_BOTTOM
    text_content: str | None = Field(None, max_length=2000)
    translated_text: str | None = Field(None, max_length=2000)
    text_font: str | None = Field(None, max_length=100)
    text_size: int | None = Field(None, ge=8, le=72)
    text_color: str | None = Field(None, max_length=20)
    text_position: dict[str, Any] | None = None
    text_plate_enabled: bool = False
    illustration_prompt: str | None = Field(None, max_length=2000)
    illustration_url: str | None = None
    illustration_model: str | None = Field(None, max_length=100)
    illustration_seed: int | None = None


class PageUpdate(BaseModel):
    page_number: int | None = Field(None, ge=1, le=64)
    page_type: PageType | None = None
    layout: PageLayout | None = None
    text_content: str | None = Field(None, max_length=2000)
    translated_text: str | None = Field(None, max_length=2000)
    text_font: str | None = Field(None, max_length=100)
    text_size: int | None = Field(None, ge=8, le=72)
    text_color: str | None = Field(None, max_length=20)
    text_position: dict[str, Any] | None = None
    text_plate_enabled: bool | None = None
    illustration_prompt: str | None = Field(None, max_length=2000)
    illustration_url: str | None = None
    illustration_model: str | None = Field(None, max_length=100)
    illustration_seed: int | None = None


class PageResponse(BaseModel):
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
    text_position: dict[str, Any] | None = None
    text_plate_enabled: bool = False
    illustration_prompt: str | None = None
    illustration_url: str | None = None
    illustration_model: str | None = None
    illustration_seed: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PageReorderItem(BaseModel):
    page_id: UUID
    new_position: int = Field(..., ge=1, le=64)


class PageReorderRequest(BaseModel):
    pages: list[PageReorderItem] = Field(..., min_length=1)


class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    species: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    reference_images: list[str] | None = None
    auto_append: bool = True
    clothing_rules: dict[str, Any] | None = None
    scale_rules: dict[str, Any] | None = None


class CharacterUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    species: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    reference_images: list[str] | None = None
    auto_append: bool | None = None
    clothing_rules: dict[str, Any] | None = None
    scale_rules: dict[str, Any] | None = None


class CharacterResponse(BaseModel):
    id: UUID
    book_id: UUID
    name: str
    species: str | None = None
    description: str | None = None
    reference_images: list[str] = Field(default_factory=list)
    auto_append: bool = True
    clothing_rules: dict[str, Any] | None = None
    scale_rules: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class GenerateStoryRequest(BaseModel):
    prompt: str | None = Field(None, max_length=2000)
    theme: str | None = Field(None, max_length=255)
    character: str | None = Field(None, max_length=255)
    setting: str | None = Field(None, max_length=500)
    tone: str | None = Field(None, max_length=255)
    story_mode: StoryMode | None = None


class GeneratedPage(BaseModel):
    page_number: int
    text_content: str
    illustration_prompt: str


class GenerateStoryResponse(BaseModel):
    pages: list[GeneratedPage]
    total_pages: int
    reading_level: str | None = None


class PacingDataPoint(BaseModel):
    page_number: int
    word_count: int
    surprise_score: float = Field(0.0, ge=0.0, le=1.0)
    tension_score: float = Field(0.0, ge=0.0, le=1.0)


class RhymeAnalysis(BaseModel):
    scheme_detected: str | None = None
    consistency_score: float = Field(0.0, ge=0.0, le=100.0)
    broken_rhymes: list[dict[str, Any]] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class TextAnalysisResponse(BaseModel):
    book_id: UUID
    reading_level: str
    reading_level_score: float = Field(..., ge=0.0, le=20.0)
    rhythm_score: float = Field(..., ge=0.0, le=100.0)
    pacing_data: list[PacingDataPoint] = Field(default_factory=list)
    rhyme_analysis: RhymeAnalysis | None = None
    vocabulary_flags: list[str] = Field(default_factory=list)
    sentence_length_avg: float | None = None


class ContinuityIssue(BaseModel):
    page_number: int
    issue_type: str
    description: str
    fix_suggestion: str | None = None


class ContinuityCheckResponse(BaseModel):
    book_id: UUID
    issues: list[ContinuityIssue] = Field(default_factory=list)
    total_issues: int = 0
    consistency_score: float = Field(0.0, ge=0.0, le=100.0)


class TrademarkIssue(BaseModel):
    page_number: int | None = None
    term: str
    category: str
    suggestion: str | None = None


class ContentIssue(BaseModel):
    page_number: int | None = None
    issue_type: str
    description: str
    severity: str = Field("warning", pattern="^(info|warning|error)$")


class SafetyCheckResponse(BaseModel):
    book_id: UUID
    trademark_issues: list[TrademarkIssue] = Field(default_factory=list)
    content_issues: list[ContentIssue] = Field(default_factory=list)
    overall_safe: bool = True


class IllustrationGenerateRequest(BaseModel):
    prompt: str | None = Field(None, max_length=2000)
    style_override: IllustrationStyle | None = None
    seed: int | None = None
    variation_count: int = Field(1, ge=1, le=4)


class IllustrationVariant(BaseModel):
    url: str
    seed: int
    model: str


class IllustrationGenerateResponse(BaseModel):
    page_id: UUID
    variants: list[IllustrationVariant] = Field(default_factory=list)
    prompt_used: str
    provenance_id: UUID | None = None


class TranslateRequest(BaseModel):
    target_language: str = Field(..., min_length=2, max_length=50)
    layout: BilingualLayout = BilingualLayout.SIDE_BY_SIDE
    age_appropriate: bool = True


class TranslatedPage(BaseModel):
    page_number: int
    original_text: str
    translated_text: str


class TranslateResponse(BaseModel):
    book_id: UUID
    target_language: str
    layout: BilingualLayout
    pages: list[TranslatedPage] = Field(default_factory=list)


class ExportRequest(BaseModel):
    format: ExportFormat


class ExportResponse(BaseModel):
    book_id: UUID
    format: ExportFormat
    url: str
    file_size_bytes: int | None = None
    preflight_results: list[PreflightCheck] | None = None


class PreflightResponse(BaseModel):
    book_id: UUID
    checks: list[PreflightCheck] = Field(default_factory=list)
    all_passed: bool = False
    total_checks: int = 0
    passed_count: int = 0
    failed_count: int = 0


class DevicePreviewRequest(BaseModel):
    device: DeviceType
    page_numbers: list[int] | None = None


class DevicePreviewPage(BaseModel):
    page_number: int
    preview_url: str
    width_px: int
    height_px: int


class DevicePreviewResponse(BaseModel):
    book_id: UUID
    device: DeviceType
    pages: list[DevicePreviewPage] = Field(default_factory=list)
