"""SQLAlchemy models for the Competitor Weakness Finder module.

The competitor_books and competitor_reviews tables are owned by W02 (app.models.market).
This module imports those models and owns the analysis result tables.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel

# Re-export the canonical models so existing imports from this module keep working
from app.models.market import CompetitorBook, CompetitorReview


class CompetitorAnalysis(TenantModel):
    """Stores the results of a deep competitor analysis."""

    __tablename__ = "competitor_analyses"

    book_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("competitor_books.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, processing, completed, failed
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weakness_count: Mapped[int] = mapped_column(Integer, default=0)
    strength_count: Mapped[int] = mapped_column(Integer, default=0)
    review_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positioning_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    book: Mapped["CompetitorBook"] = relationship(back_populates="analyses")
    weaknesses: Mapped[list["WeaknessSignal"]] = relationship(back_populates="analysis", lazy="selectin")
    opportunity: Mapped["OpportunityBlueprint | None"] = relationship(
        back_populates="analysis", uselist=False, lazy="selectin"
    )


class WeaknessSignal(BaseModel):
    """A single detected weakness signal from review analysis."""

    __tablename__ = "weakness_signals"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("competitor_analyses.id"), index=True
    )
    category: Mapped[str] = mapped_column(
        String(50)
    )  # content_quality, format_layout, missing_features, pricing, coverage_gaps
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, critical
    signal_text: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)  # review excerpts as evidence
    frequency: Mapped[int] = mapped_column(Integer, default=1)  # how many reviews mention this
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    actionable: Mapped[bool] = mapped_column(Boolean, default=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped["CompetitorAnalysis"] = relationship(back_populates="weaknesses")


class OpportunityBlueprint(BaseModel):
    """AI-generated blueprint for how to beat a competitor book."""

    __tablename__ = "opportunity_blueprints"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("competitor_analyses.id"),
        unique=True,
        index=True,
    )
    title_suggestions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    content_strategy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    format_recommendations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    pricing_strategy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    differentiators: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    full_blueprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    analysis: Mapped["CompetitorAnalysis"] = relationship(back_populates="opportunity")


class GapAnalysisResult(TenantModel):
    """Results of a niche-level gap analysis (cover, title, content gaps)."""

    __tablename__ = "gap_analysis_results"

    niche: Mapped[str] = mapped_column(String(300), index=True)
    category: Mapped[str | None] = mapped_column(String(300), nullable=True)
    books_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    cover_gaps: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    title_gaps: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    content_gaps: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")


class CompetitorAlert(TenantModel):
    """Alerts for competitor changes (price, BSR, new books)."""

    __tablename__ = "competitor_alerts"

    book_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("competitor_books.id"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(50))  # price_change, bsr_shift, new_book, review_spike
    severity: Mapped[str] = mapped_column(String(20), default="info")
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
