"""Specialty Books models — Children's, Coloring & Puzzle Books.

Defines 25+ tables covering three book types and shared infrastructure
(asset provenance, originality, series, bundles, accessibility, etc.).
"""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel

# ═══════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════


class BookType(str, enum.Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class BookStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PageType(str, enum.Enum):
    COVER = "cover"
    FRONT_MATTER = "front_matter"
    CONTENT = "content"
    BACK_MATTER = "back_matter"


class StoryMode(str, enum.Enum):
    ORIGINAL = "original"
    RETELLING = "retelling"
    EDUCATIONAL = "educational"
    INTERACTIVE = "interactive"


class IllustrationStyle(str, enum.Enum):
    WATERCOLOR = "watercolor"
    CARTOON = "cartoon"
    REALISTIC = "realistic"
    FLAT = "flat"
    MIXED_MEDIA = "mixed_media"


class LineStyle(str, enum.Enum):
    THIN = "thin"
    MEDIUM = "medium"
    THICK = "thick"
    VARIABLE = "variable"


class PuzzleType(str, enum.Enum):
    WORD_SEARCH = "word_search"
    CROSSWORD = "crossword"
    MAZE = "maze"
    SUDOKU = "sudoku"
    SCRAMBLE = "scramble"
    CRYPTOGRAM = "cryptogram"


class DifficultyMode(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class AssetType(str, enum.Enum):
    ILLUSTRATION = "illustration"
    LINE_ART = "line_art"
    VECTOR = "vector"
    AUDIO = "audio"
    TEXT = "text"


class LicenseType(str, enum.Enum):
    OPEN = "open"
    COMMERCIAL = "commercial"
    RESTRICTED = "restricted"
    CUSTOM = "custom"


class BatchJobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ISBNStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    USED = "used"


class PreflightStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNINGS = "warnings"


class VariantType(str, enum.Enum):
    LARGE_PRINT = "large_print"
    HIGH_CONTRAST = "high_contrast"
    DYSLEXIA_FRIENDLY = "dyslexia_friendly"
    AUDIO_DESCRIBED = "audio_described"


class WordSourceType(str, enum.Enum):
    CURATED = "curated"
    IMPORTED = "imported"
    AI_GENERATED = "ai_generated"
    PUBLIC_DOMAIN = "public_domain"


class ContentType(str, enum.Enum):
    IMAGE = "image"
    TEXT = "text"
    PUZZLE_GRID = "puzzle_grid"


class TemplateType(str, enum.Enum):
    ABOUT_AUTHOR = "about_author"
    ALSO_BY = "also_by"
    CTA = "cta"
    COLORING_TIPS = "coloring_tips"
    ANSWER_KEY = "answer_key"


class Complexity(str, enum.Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    DETAILED = "detailed"
    INTRICATE = "intricate"


class ClueStyle(str, enum.Enum):
    DEFINITION = "definition"
    FILL_IN_BLANK = "fill_in_blank"
    SYNONYM = "synonym"
    AI_GENERATED = "ai_generated"


class FearInventory(str, enum.Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"


# ═══════════════════════════════════════════════════════════════════════
# CHILDREN'S BOOKS
# ═══════════════════════════════════════════════════════════════════════


class ChildrensBook(TenantModel):
    """Master record for a children's book project."""

    __tablename__ = "childrens_books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    trim_size: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)
    illustration_style: Mapped[IllustrationStyle | None] = mapped_column(
        SAEnum(IllustrationStyle, name="sp_illustration_style", create_constraint=True),
        nullable=True,
        default=None,
    )
    color_palette: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    story_mode: Mapped[StoryMode | None] = mapped_column(
        SAEnum(StoryMode, name="sp_story_mode", create_constraint=True),
        nullable=True,
        default=None,
    )
    is_bilingual: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    fear_inventory: Mapped[FearInventory | None] = mapped_column(
        SAEnum(FearInventory, name="sp_fear_inventory", create_constraint=True),
        nullable=True,
        default=None,
    )
    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="sp_book_status", create_constraint=True),
        default=BookStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    pages = relationship("app.modules.specialty_books.models.ChildrensBookPage", back_populates="book", lazy="selectin")
    characters = relationship(
        "app.modules.specialty_books.models.ChildrensBookCharacter", back_populates="book", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_childrens_books_org_status", "org_id", "status"),
        Index("ix_childrens_books_status", "status"),
        Index("ix_childrens_books_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ChildrensBookPage(TenantModel):
    """Individual page in a children's book."""

    __tablename__ = "childrens_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("childrens_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[PageType] = mapped_column(
        SAEnum(PageType, name="sp_page_type", create_constraint=True),
        default=PageType.CONTENT,
        server_default="content",
    )
    layout: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    text_font: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    text_size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    text_color: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    text_position: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    text_plate: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    illustration_seed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    book = relationship("app.modules.specialty_books.models.ChildrensBook", back_populates="pages")

    __table_args__ = (
        Index("ix_cb_pages_org_status", "org_id", "page_type"),
        Index("ix_cb_pages_book_id", "book_id"),
        Index("ix_cb_pages_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ChildrensBookCharacter(TenantModel):
    """Character consistency sheet for a children's book."""

    __tablename__ = "childrens_book_characters"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("childrens_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    species: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    reference_images: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    auto_append: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    clothing_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    scale_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    book = relationship("app.modules.specialty_books.models.ChildrensBook", back_populates="characters")

    __table_args__ = (
        Index("ix_cb_chars_org_id", "org_id"),
        Index("ix_cb_chars_book_id", "book_id"),
        Index("ix_cb_chars_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


# ═══════════════════════════════════════════════════════════════════════
# COLORING BOOKS
# ═══════════════════════════════════════════════════════════════════════


class ColoringBook(TenantModel):
    """Master record for a coloring book project."""

    __tablename__ = "coloring_books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    trim_size: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)
    line_style: Mapped[LineStyle | None] = mapped_column(
        SAEnum(LineStyle, name="sp_line_style", create_constraint=True),
        nullable=True,
        default=None,
    )
    line_weight: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    complexity: Mapped[Complexity | None] = mapped_column(
        SAEnum(Complexity, name="sp_complexity", create_constraint=True),
        nullable=True,
        default=None,
    )
    stroke_uniformity: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    single_sided: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="sp_book_status", create_constraint=True),
        default=BookStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    pages = relationship("app.modules.specialty_books.models.ColoringBookPage", back_populates="book", lazy="selectin")

    __table_args__ = (
        Index("ix_coloring_books_org_status", "org_id", "status"),
        Index("ix_coloring_books_status", "status"),
        Index("ix_coloring_books_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ColoringBookPage(TenantModel):
    """Individual page in a coloring book with QA tracking."""

    __tablename__ = "coloring_book_pages"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("coloring_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[PageType] = mapped_column(
        SAEnum(PageType, name="sp_page_type", create_constraint=True),
        default=PageType.CONTENT,
        server_default="content",
    )
    illustration_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cleaned_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    vectorized_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    illustration_model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    illustration_seed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    qa_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    book = relationship("app.modules.specialty_books.models.ColoringBook", back_populates="pages")

    __table_args__ = (
        Index("ix_clr_pages_org_id", "org_id"),
        Index("ix_clr_pages_book_id", "book_id"),
        Index("ix_clr_pages_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


# ═══════════════════════════════════════════════════════════════════════
# PUZZLE BOOKS
# ═══════════════════════════════════════════════════════════════════════


class PuzzleBook(TenantModel):
    """Master record for a puzzle book project."""

    __tablename__ = "puzzle_books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    puzzle_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    difficulty_mode: Mapped[DifficultyMode | None] = mapped_column(
        SAEnum(DifficultyMode, name="sp_difficulty_mode", create_constraint=True),
        nullable=True,
        default=None,
    )
    themes: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    seasonal_theme: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    word_difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    clue_style: Mapped[ClueStyle | None] = mapped_column(
        SAEnum(ClueStyle, name="sp_clue_style", create_constraint=True),
        nullable=True,
        default=None,
    )
    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="sp_book_status", create_constraint=True),
        default=BookStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    puzzles = relationship("app.modules.specialty_books.models.Puzzle", back_populates="book", lazy="selectin")

    __table_args__ = (
        Index("ix_puzzle_books_org_status", "org_id", "status"),
        Index("ix_puzzle_books_status", "status"),
        Index("ix_puzzle_books_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class Puzzle(TenantModel):
    """Individual puzzle with solution and QA data."""

    __tablename__ = "puzzles"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("puzzle_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    puzzle_type: Mapped[PuzzleType] = mapped_column(
        SAEnum(PuzzleType, name="sp_puzzle_type", create_constraint=True),
        nullable=False,
    )
    puzzle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    difficulty: Mapped[DifficultyMode | None] = mapped_column(
        SAEnum(DifficultyMode, name="sp_difficulty_mode", create_constraint=True),
        nullable=True,
        default=None,
    )
    difficulty_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    grid_size: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    grid_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    word_list: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    clues: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    solution_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    book = relationship("app.modules.specialty_books.models.PuzzleBook", back_populates="puzzles")

    __table_args__ = (
        Index("ix_puzzles_org_id", "org_id"),
        Index("ix_puzzles_book_id", "book_id"),
        Index("ix_puzzles_type", "puzzle_type"),
        Index("ix_puzzles_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


# ═══════════════════════════════════════════════════════════════════════
# SHARED TABLES
# ═══════════════════════════════════════════════════════════════════════


class AssetProvenance(TenantModel):
    """Every generated asset tracked for legal protection."""

    __tablename__ = "asset_provenance"

    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    page_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, name="sp_asset_type", create_constraint=True),
        nullable=False,
    )
    model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    generated_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    __table_args__ = (
        Index("ix_asset_prov_org_book_type", "org_id", "book_type"),
        Index("ix_asset_prov_book_id", "book_id"),
        Index("ix_asset_prov_prompt_hash", "prompt_hash"),
        Index("ix_asset_prov_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class FontLicense(BaseModel):
    """Font licensing registry."""

    __tablename__ = "font_licenses"

    font_name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_type: Mapped[LicenseType] = mapped_column(
        SAEnum(LicenseType, name="sp_license_type", create_constraint=True),
        nullable=False,
    )
    commercial_print: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    license_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    __table_args__ = (
        Index("ix_font_licenses_name", "font_name"),
        Index("ix_font_licenses_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class BatchJob(TenantModel):
    """Batch factory job tracking."""

    __tablename__ = "batch_jobs"

    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    batch_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    budget_limit_cents: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    spent_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[BatchJobStatus] = mapped_column(
        SAEnum(BatchJobStatus, name="sp_batch_job_status", create_constraint=True),
        default=BatchJobStatus.QUEUED,
        server_default="queued",
    )
    volumes_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    volumes_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pages_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pages_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    __table_args__ = (
        Index("ix_batch_jobs_org_status", "org_id", "status"),
        Index("ix_batch_jobs_status", "status"),
        Index("ix_batch_jobs_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ContentFingerprint(TenantModel):
    """Originality fingerprinting for content."""

    __tablename__ = "content_fingerprints"

    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    page_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="sp_content_type", create_constraint=True),
        nullable=False,
    )
    phash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    ngram_fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    jaccard_vector: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    __table_args__ = (
        Index("ix_content_fp_org_book_type", "org_id", "book_type"),
        Index("ix_content_fp_book_id", "book_id"),
        Index("ix_content_fp_phash", "phash"),
        Index("ix_content_fp_data_hash", "data_hash"),
        Index("ix_content_fp_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class OriginalityReport(TenantModel):
    """KDP compliance / originality reports."""

    __tablename__ = "originality_reports"

    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    component_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    cross_book_similarities: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    spam_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    __table_args__ = (
        Index("ix_orig_reports_org_book_type", "org_id", "book_type"),
        Index("ix_orig_reports_book_id", "book_id"),
        Index("ix_orig_reports_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class BookSeries(TenantModel):
    """Series branding management."""

    __tablename__ = "book_series"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    naming_format: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    branding_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    branding_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    volume_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (
        Index("ix_book_series_org_type", "org_id", "book_type"),
        Index("ix_book_series_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class BackMatterTemplate(TenantModel):
    """Reusable back matter pages."""

    __tablename__ = "back_matter_templates"

    template_type: Mapped[TemplateType] = mapped_column(
        SAEnum(TemplateType, name="sp_template_type", create_constraint=True),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cta_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    qr_code_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    __table_args__ = (
        Index("ix_back_matter_org_type", "org_id", "template_type"),
        Index("ix_back_matter_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ISBNPool(TenantModel):
    """ISBN inventory management."""

    __tablename__ = "isbn_pool"

    isbn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    publisher_name: Mapped[str | None] = mapped_column(String(300), nullable=True, default=None)
    assigned_to_book_type: Mapped[BookType | None] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=True,
        default=None,
    )
    assigned_to_book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    barcode_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[ISBNStatus] = mapped_column(
        SAEnum(ISBNStatus, name="sp_isbn_status", create_constraint=True),
        default=ISBNStatus.AVAILABLE,
        server_default="available",
    )

    __table_args__ = (
        Index("ix_isbn_pool_org_status", "org_id", "status"),
        Index("ix_isbn_pool_isbn", "isbn"),
        Index("ix_isbn_pool_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class DistributorPreflight(TenantModel):
    """Per-distributor validation."""

    __tablename__ = "distributor_preflights"

    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    distributor: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PreflightStatus] = mapped_column(
        SAEnum(PreflightStatus, name="sp_preflight_status", create_constraint=True),
        default=PreflightStatus.PENDING,
        server_default="pending",
    )
    checks: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    exported_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    __table_args__ = (
        Index("ix_dist_preflight_org_status", "org_id", "status"),
        Index("ix_dist_preflight_book_id", "book_id"),
        Index("ix_dist_preflight_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class BookBundle(TenantModel):
    """Combined volume bundles."""

    __tablename__ = "book_bundles"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    volume_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("book_series.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Relationships
    series = relationship("app.modules.specialty_books.models.BookSeries", foreign_keys=[series_id])

    __table_args__ = (
        Index("ix_book_bundles_org_type", "org_id", "book_type"),
        Index("ix_book_bundles_series_id", "series_id"),
        Index("ix_book_bundles_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AccessibilityVariant(TenantModel):
    """Tracks accessible editions derived from source books."""

    __tablename__ = "accessibility_variants"

    source_book_type: Mapped[BookType] = mapped_column(
        SAEnum(BookType, name="sp_book_type", create_constraint=True),
        nullable=False,
    )
    source_book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    variant_type: Mapped[VariantType] = mapped_column(
        SAEnum(VariantType, name="sp_variant_type", create_constraint=True),
        nullable=False,
    )
    variant_book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    __table_args__ = (
        Index("ix_access_var_org_type", "org_id", "source_book_type"),
        Index("ix_access_var_source_book", "source_book_id"),
        Index("ix_access_var_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class WordListSource(TenantModel):
    """Word list provenance for puzzle generation."""

    __tablename__ = "word_list_sources"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[WordSourceType] = mapped_column(
        SAEnum(WordSourceType, name="sp_word_source_type", create_constraint=True),
        nullable=False,
    )
    license: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    dictionary: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    __table_args__ = (
        Index("ix_word_list_org_type", "org_id", "source_type"),
        Index("ix_word_list_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
