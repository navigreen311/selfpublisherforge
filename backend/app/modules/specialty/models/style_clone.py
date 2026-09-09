"""SQLAlchemy models for Art Style Cloning."""
from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class StyleCloneProfile(TenantModel):
    """A cloned art style profile derived from reference images."""

    __tablename__ = "style_clone_profiles"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference images used to create the style
    reference_image_urls: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reference_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Analyzed style attributes
    style_attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # e.g., {"line_weight": "medium", "color_saturation": "high", "shading": "cross-hatch",
    #        "perspective": "flat", "palette": ["#FF5733", "#33FF57"], "texture": "smooth"}

    # The generated style prompt/embedding
    style_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    style_embedding: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Test generation results
    test_image_urls: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Drift detection
    drift_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_drift_check: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Which book type this is primarily for (optional)
    book_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Usage stats
    times_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
