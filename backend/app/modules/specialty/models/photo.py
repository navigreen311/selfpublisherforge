"""SQLAlchemy models for Photo References."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel
from app.modules.specialty.models.enums import PhotoUsageType


class PhotoReference(TenantModel):
    """User-uploaded photo reference for AI image generation."""

    __tablename__ = "photo_references"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    usage_type: Mapped[str] = mapped_column(
        Enum(PhotoUsageType, name="photo_usage_type", native_enum=True),
        nullable=False,
        default=PhotoUsageType.style_reference,
    )

    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Which book type and book ID this is associated with (polymorphic)
    book_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
