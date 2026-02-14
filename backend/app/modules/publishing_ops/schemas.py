"""Pydantic schemas for the Publishing Operations Center."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ---------- Enums ----------

class PlatformType(str, Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram_spark"
    DRAFT2DIGITAL = "draft2digital"
    SMASHWORDS = "smashwords"
    APPLE_BOOKS = "apple_books"
    BARNES_NOBLE = "barnes_noble"
    KOBO = "kobo"
    GOOGLE_PLAY = "google_play"


class ExportFormat(str, Enum):
    EPUB = "epub"
    PDF = "pdf"


class TrimSize(str, Enum):
    SIZE_5x8 = "5x8"
    SIZE_5_25x8 = "5.25x8"
    SIZE_5_5x8_5 = "5.5x8.5"
    SIZE_6x9 = "6x9"
    SIZE_7x10 = "7x10"
    SIZE_8_5x11 = "8.5x11"


class ListingStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    LIVE = "live"
    PAUSED = "paused"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class TemplateGenre(str, Enum):
    ROMANCE = "romance"
    THRILLER = "thriller"
    NONFICTION = "nonfiction"
    CHILDRENS = "childrens"
    SCIFI = "scifi"
    FANTASY = "fantasy"
    LITERARY = "literary"
    MEMOIR = "memoir"
    BUSINESS = "business"
    CUSTOM = "custom"


# ---------- Publishing Accounts ----------

class PublishingAccountBase(BaseModel):
    platform: PlatformType
    account_name: str = Field(..., min_length=1, max_length=255)
    account_email: str | None = None


class PublishingAccountCreate(PublishingAccountBase):
    credentials: dict[str, str] = Field(
        default_factory=dict,
        description="Encrypted credentials for platform API access",
    )


class PublishingAccount(PublishingAccountBase):
    id: uuid.UUID
    org_id: uuid.UUID
    is_active: bool = True
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Export ----------

class ChapterInput(BaseModel):
    title: str
    content: str
    order: int


class ExportRequest(BaseModel):
    book_id: uuid.UUID
    format: ExportFormat
    template_id: uuid.UUID | None = None
    chapters: list[ChapterInput] = Field(default_factory=list)
    include_toc: bool = True
    include_cover: bool = True
    cover_image_url: str | None = None
    # PDF-specific
    trim_size: TrimSize = TrimSize.SIZE_6x9
    include_isbn_barcode: bool = False
    isbn: str | None = None


class ExportResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    format: ExportFormat
    status: str = "processing"
    file_url: str | None = None
    file_size_bytes: int | None = None
    page_count: int | None = None
    created_at: datetime
    message: str = "Export job queued"

    model_config = {"from_attributes": True}


# ---------- Formatting Templates ----------

class TemplateStyleSettings(BaseModel):
    font_family: str = "Georgia"
    font_size_pt: float = 11.0
    line_height: float = 1.5
    margin_top_in: float = 0.75
    margin_bottom_in: float = 0.75
    margin_inner_in: float = 1.0
    margin_outer_in: float = 0.75
    chapter_heading_font: str = "Georgia"
    chapter_heading_size_pt: float = 24.0
    paragraph_indent_em: float = 1.5
    paragraph_spacing_pt: float = 0.0
    drop_cap: bool = False
    header_text: str | None = None
    footer_text: str | None = None
    page_numbers: bool = True


class FormattingTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    genre: TemplateGenre = TemplateGenre.CUSTOM
    description: str | None = None
    trim_size: TrimSize = TrimSize.SIZE_6x9
    style_settings: TemplateStyleSettings = Field(default_factory=TemplateStyleSettings)


class FormattingTemplateCreate(FormattingTemplateBase):
    """Request body for creating a formatting template. Inherits all fields from FormattingTemplateBase."""


class FormattingTemplate(FormattingTemplateBase):
    id: uuid.UUID
    org_id: uuid.UUID | None = None
    is_builtin: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Book Metadata ----------

class PricingInfo(BaseModel):
    currency: str = "USD"
    list_price: float = 0.0
    sale_price: float | None = None


class BookMetadataBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: str | None = None
    description: str | None = None
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list, max_length=7)
    categories: list[str] = Field(default_factory=list)
    language: str = "en"
    isbn: str | None = None
    asin: str | None = None
    publisher: str | None = None
    publication_date: datetime | None = None
    pricing: PricingInfo = Field(default_factory=PricingInfo)
    series_name: str | None = None
    series_number: int | None = None
    page_count: int | None = None
    age_range: str | None = None


class BookMetadataUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    authors: list[str] | None = None
    keywords: list[str] | None = None
    categories: list[str] | None = None
    language: str | None = None
    isbn: str | None = None
    asin: str | None = None
    publisher: str | None = None
    publication_date: datetime | None = None
    pricing: PricingInfo | None = None
    series_name: str | None = None
    series_number: int | None = None
    page_count: int | None = None
    age_range: str | None = None


class BookMetadata(BookMetadataBase):
    book_id: uuid.UUID
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Listings ----------

class ListingBase(BaseModel):
    book_id: uuid.UUID
    platform: PlatformType
    platform_listing_id: str | None = None
    status: ListingStatus = ListingStatus.DRAFT
    listing_url: str | None = None


class ListingDetail(ListingBase):
    id: uuid.UUID
    account_id: uuid.UUID
    title: str | None = None
    current_price: float | None = None
    current_rank: int | None = None
    reviews_count: int | None = None
    rating: float | None = None
    last_synced_at: datetime | None = None
    sync_errors: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingSyncResponse(BaseModel):
    listing_id: uuid.UUID
    status: str = "sync_queued"
    message: str = "Listing sync has been queued"


# ---------- ISBNs ----------

class ISBNStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    USED = "used"
    RETIRED = "retired"


class ISBNFormat(str, Enum):
    ISBN_13 = "isbn_13"
    ISBN_10 = "isbn_10"


class CreateISBNRequest(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13 value")
    format: ISBNFormat = ISBNFormat.ISBN_13
    book_id: uuid.UUID | None = None
    title: str | None = Field(None, max_length=500, description="Book title associated with this ISBN")
    notes: str | None = None


class UpdateISBNRequest(BaseModel):
    isbn: str | None = Field(None, min_length=10, max_length=17)
    format: ISBNFormat | None = None
    status: ISBNStatus | None = None
    book_id: uuid.UUID | None = None
    title: str | None = Field(None, max_length=500)
    notes: str | None = None


class ISBNResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    isbn: str
    format: ISBNFormat
    status: ISBNStatus
    book_id: uuid.UUID | None = None
    title: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateBarcodeRequest(BaseModel):
    width: int = Field(default=200, ge=50, le=1000, description="Barcode width in pixels")
    height: int = Field(default=100, ge=25, le=500, description="Barcode height in pixels")
    include_text: bool = Field(default=True, description="Whether to include human-readable text below the barcode")
