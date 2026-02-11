"""SQLAlchemy models for the Product Page Conversion Lab.

The ab_tests table is defined here as described in the W02 schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class ABTest(TenantModel):
    """A/B test for comparing blurb variants.

    Tracks impressions and clicks for two blurb variants to determine
    which converts better.
    """

    __tablename__ = "ab_tests"

    book_id: Mapped[uuid.UUID] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="draft")

    variant_a_content: Mapped[str] = mapped_column(Text)
    variant_b_content: Mapped[str] = mapped_column(Text)

    variant_a_impressions: Mapped[int] = mapped_column(Integer, default=0)
    variant_a_clicks: Mapped[int] = mapped_column(Integer, default=0)
    variant_b_impressions: Mapped[int] = mapped_column(Integer, default=0)
    variant_b_clicks: Mapped[int] = mapped_column(Integer, default=0)

    duration_days: Mapped[int] = mapped_column(Integer, default=7)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
