"""SQLAlchemy models for the Product Page Conversion Lab.

The ab_tests table is defined here as described in the W02 schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
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


class ListingAnalysisRecord(TenantModel):
    """Persisted listing analysis result."""
    __tablename__ = "listing_analyses"

    book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    findings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)


class GeneratedBlurb(TenantModel):
    """A generated blurb version."""
    __tablename__ = "generated_blurbs"

    book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    plain_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selling_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_reader: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False, server_default="false")


class KeywordAnalysisRecord(TenantModel):
    """Persisted keyword optimization result."""
    __tablename__ = "keyword_analyses"

    book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    current_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    recommended: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    optimal_seven: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)


class APlusPlan(TenantModel):
    """A+ content plan for a book."""
    __tablename__ = "aplus_plans"

    book_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    modules: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft", server_default="draft")
