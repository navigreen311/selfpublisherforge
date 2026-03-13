"""SQLAlchemy models for Accessibility Variants.

Covers blueprint section 13.4 shared table:
- AccessibilityVariant: tracks accessible editions
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class BookType(str, enum.Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class AccessibilityVariant(TenantModel):
    """Tracks accessible edition variants of specialty books."""

    __tablename__ = "accessibility_variants"

    source_book_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    variant_type: Mapped[str] = mapped_column(String(30), nullable=False)
    variant_book_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
