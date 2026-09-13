"""SQLAlchemy models for shared Specialty Books tables."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseModel, TenantModel
from app.modules.specialty.models.enums import (
    AssetType,
    BatchStatus,
    BookType,
    DistributorName,
    ISBNStatus,
    LicenseType,
    PreflightStatus,
    TemplateType,
    VariantType,
    WordListSourceType,
)


class AssetProvenance(TenantModel):
    """Every generated asset tracked for legal protection."""

    __tablename__ = "asset_provenance"

    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    page_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    asset_type: Mapped[str] = mapped_column(
        Enum(AssetType, name="specialty_asset_type", native_enum=True),
        nullable=False,
    )
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FontLicense(BaseModel):
    """Font licensing registry."""

    __tablename__ = "font_licenses"

    font_name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_type: Mapped[str] = mapped_column(
        Enum(LicenseType, name="license_type", native_enum=True),
        nullable=False,
    )
    commercial_print: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    license_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class BatchJob(TenantModel):
    """Batch factory job tracking."""

    __tablename__ = "batch_jobs"

    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    batch_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    budget_limit_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spent_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        Enum(BatchStatus, name="batch_status", native_enum=True),
        nullable=False,
        default=BatchStatus.pending,
        server_default="pending",
    )
    volumes_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    volumes_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    pages_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class ContentFingerprint(TenantModel):
    """Originality fingerprinting for KDP compliance."""

    __tablename__ = "content_fingerprints"

    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    page_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    phash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ngram_fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True)
    jaccard_vector: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class OriginalityReport(TenantModel):
    """KDP compliance / originality reports."""

    __tablename__ = "originality_reports"

    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    component_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    cross_book_similarities: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    spam_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class BookSeries(TenantModel):
    """Series branding management."""

    __tablename__ = "book_series"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    naming_format: Mapped[str | None] = mapped_column(String(200), nullable=True)
    branding_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    branding_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    volume_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class BackMatterTemplate(TenantModel):
    """Reusable back matter pages."""

    __tablename__ = "back_matter_templates"

    template_type: Mapped[str] = mapped_column(
        Enum(TemplateType, name="template_type", native_enum=True),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_code_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class ISBNPool(TenantModel):
    """ISBN inventory management."""

    __tablename__ = "isbn_pool"

    isbn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    publisher_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    assigned_to_book_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    assigned_to_book_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    barcode_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ISBNStatus, name="isbn_status", native_enum=True),
        nullable=False,
        default=ISBNStatus.available,
        server_default="available",
    )


class DistributorPreflight(BaseModel):
    """Per-distributor validation results."""

    __tablename__ = "distributor_preflights"

    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    distributor: Mapped[str] = mapped_column(
        Enum(DistributorName, name="distributor_name", native_enum=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(PreflightStatus, name="preflight_status", native_enum=True),
        nullable=False,
        default=PreflightStatus.pending,
        server_default="pending",
    )
    checks: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    issues: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    exported_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class BookBundle(TenantModel):
    """Combined volume bundles / box sets."""

    __tablename__ = "book_bundles"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    volume_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("book_series.id", ondelete="SET NULL"),
        nullable=True,
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AccessibilityVariant(BaseModel):
    """Tracks accessible editions of books."""

    __tablename__ = "accessibility_variants"

    source_book_type: Mapped[str] = mapped_column(
        Enum(BookType, name="book_type", native_enum=True, create_type=False),
        nullable=False,
    )
    source_book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    variant_type: Mapped[str] = mapped_column(
        Enum(VariantType, name="variant_type", native_enum=True),
        nullable=False,
    )
    variant_book_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class WordListSource(TenantModel):
    """Word list provenance for puzzle books."""

    __tablename__ = "word_list_sources"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(
        Enum(WordListSourceType, name="word_list_source_type", native_enum=True),
        nullable=False,
    )
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dictionary: Mapped[str | None] = mapped_column(String(100), nullable=True)
