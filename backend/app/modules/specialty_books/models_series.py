"""SQLAlchemy models for Series, Bundles, ISBN, Back Matter, and Distributor Preflight.

Covers blueprint sections 12.1-12.6 database tables:
- BookSeries: series branding management
- BackMatterTemplate: reusable back-matter pages
- ISBNPool: ISBN inventory management
- DistributorPreflight: per-distributor validation records
- BookBundle: combined-volume bundles / box sets
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel

# ── Enums ────────────────────────────────────────────────────────────────────


class BookType(str, enum.Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class ISBNStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    USED = "used"


class DistributorTarget(str, enum.Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram_spark"
    BN_PRESS = "bn_press"


class BackMatterTemplateType(str, enum.Enum):
    ALSO_IN_SERIES = "also_in_series"
    ABOUT_SERIES = "about_series"
    EMAIL_CTA = "email_cta"
    REVIEW_REQUEST = "review_request"
    ABOUT_AUTHOR = "about_author"


# ── Models ───────────────────────────────────────────────────────────────────


class BookSeries(TenantModel):
    """Series branding management."""

    __tablename__ = "book_series"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    book_type: Mapped[str] = mapped_column(String(20), nullable=False)
    naming_format: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Template for volume titles, e.g. '{Series Name} Vol. {N}: {Subtitle}'",
    )
    branding_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Title font, title position, author position, volume badge style, spine layout",
    )
    branding_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    volume_count: Mapped[int] = mapped_column(Integer, default=0)


class BackMatterTemplate(TenantModel):
    """Reusable back-matter page templates."""

    __tablename__ = "back_matter_templates"

    template_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qr_code_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ISBNPool(TenantModel):
    """ISBN inventory management."""

    __tablename__ = "isbn_pool"

    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    publisher_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to_book_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    assigned_to_book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    barcode_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="available")


class DistributorPreflight(TenantModel):
    """Per-distributor preflight validation record."""

    __tablename__ = "distributor_preflights"

    book_type: Mapped[str] = mapped_column(String(20), nullable=False)
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    distributor: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    checks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    exported_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class BookBundle(TenantModel):
    """Combined-volume bundle / box set."""

    __tablename__ = "book_bundles"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    book_type: Mapped[str] = mapped_column(String(20), nullable=False)
    volume_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    series_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
