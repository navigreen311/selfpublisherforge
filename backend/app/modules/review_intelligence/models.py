"""SQLAlchemy models for Review Intelligence module."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class BookReview(TenantModel):
    """Tracks individual reviews for books owned by the org or competitors."""

    __tablename__ = "book_reviews"

    book_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    source: Mapped[str] = mapped_column(String(50))  # amazon, goodreads, bookbub, etc.
    source_review_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    star_rating: Mapped[float] = mapped_column(Float)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    is_competitor: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Sentiment analysis results
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)  # positive, negative, neutral, mixed
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    themes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_book_reviews_book_source", "book_id", "source"),
        Index("ix_book_reviews_org_book", "org_id", "book_id"),
        Index("ix_book_reviews_review_date", "review_date"),
        Index(
            "ix_book_reviews_source_id",
            "source",
            "source_review_id",
            unique=True,
            postgresql_where=text("source_review_id IS NOT NULL"),
        ),
    )


class ReviewAlert(TenantModel):
    """Alerts triggered by review monitoring rules."""

    __tablename__ = "review_alerts"

    book_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    alert_type: Mapped[str] = mapped_column(
        String(50)
    )  # negative_spike, velocity_drop, rating_decline, competitor_surge
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_review_alerts_org_active", "org_id", "is_acknowledged"),
        Index("ix_review_alerts_book_type", "book_id", "alert_type"),
    )


class ReviewVelocitySnapshot(TenantModel):
    """Periodic snapshots of review velocity for trend tracking."""

    __tablename__ = "review_velocity_snapshots"

    book_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    period: Mapped[str] = mapped_column(String(20))  # daily, weekly, monthly
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index(
            "ix_velocity_book_period",
            "book_id",
            "period",
            "period_start",
            unique=True,
        ),
    )


class ReputationScore(TenantModel):
    """Computed reputation scores for books."""

    __tablename__ = "reputation_scores"

    book_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, index=True)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_ratio: Mapped[float] = mapped_column(Float, default=0.0)  # positive / total
    velocity_trend: Mapped[str] = mapped_column(String(20), default="stable")  # rising, stable, declining
    health_grade: Mapped[str] = mapped_column(String(2), default="C")  # A+, A, B+, B, C+, C, D, F
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
