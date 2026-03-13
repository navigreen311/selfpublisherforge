"""Shared models for the Specialty Books module.

Defines cross-cutting tables used by Children's, Coloring, and Puzzle book types:
- AssetProvenance: per-image generation metadata for legal compliance
- FontLicense: font licensing registry
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

from app.database import BaseModel, TenantModel


class BookType(str, enum.Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


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


class AssetProvenance(TenantModel):
    """Every generated asset tracked for legal protection."""

    __tablename__ = "asset_provenance"

    book_type: Mapped[str] = mapped_column(String(20), nullable=False)
    book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    page_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    generated_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)


class FontLicense(BaseModel):
    """Font licensing registry."""

    __tablename__ = "font_licenses"

    font_name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_type: Mapped[str] = mapped_column(String(20), nullable=False)
    commercial_print: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    license_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
