"""SQLAlchemy models for the Pricing Automation module."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class PricingStrategyType(str, PyEnum):
    COMPETITIVE_MATCH = "competitive_match"
    VALUE_BASED = "value_based"
    PENETRATION = "penetration"
    DYNAMIC = "dynamic"
    PROMOTIONAL = "promotional"


class RuleStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class PromotionStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTestStatus(str, PyEnum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookFormat(str, PyEnum):
    EBOOK = "ebook"
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    AUDIOBOOK = "audiobook"


class PricingRule(TenantModel):
    """Defines an automated pricing rule for a book or set of books."""

    __tablename__ = "pricing_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=True, index=True
    )
    strategy: Mapped[PricingStrategyType] = mapped_column(
        Enum(PricingStrategyType, name="pricing_strategy_type"), nullable=False
    )
    status: Mapped[RuleStatus] = mapped_column(
        Enum(RuleStatus, name="rule_status"),
        nullable=False,
        default=RuleStatus.DRAFT,
        server_default="draft",
    )
    book_format: Mapped[BookFormat] = mapped_column(
        Enum(BookFormat, name="book_format"),
        nullable=False,
        default=BookFormat.EBOOK,
        server_default="ebook",
    )
    min_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.99)
    max_price: Mapped[float] = mapped_column(Float, nullable=False, default=9.99)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_auto_apply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    book = relationship(
        "Book",
        back_populates="pricing_rules",
        primaryjoin="PricingRule.book_id == Book.id",
        foreign_keys="[PricingRule.book_id]",
    )
    promotions: Mapped[list[Promotion]] = relationship("Promotion", back_populates="pricing_rule", lazy="selectin")
    ab_tests: Mapped[list[PricingABTest]] = relationship(
        "PricingABTest", back_populates="pricing_rule", lazy="selectin"
    )
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, default=None)
    last_adjusted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    __table_args__ = (
        Index("ix_pricing_rules_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_pricing_rules_rules_gin", "rules", postgresql_using="gin"),
        Index("ix_pricing_rules_strategy", "strategy"),
    )


class CompetitorPrice(TenantModel):
    """Tracks competitor pricing data for a book's category/niche."""

    __tablename__ = "competitor_prices"

    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    competitor_asin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    competitor_title: Mapped[str] = mapped_column(String(500), nullable=False)
    competitor_author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    book_format: Mapped[BookFormat] = mapped_column(
        Enum(BookFormat, name="book_format", create_type=False),
        nullable=False,
        default=BookFormat.EBOOK,
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    bsr_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Promotion(TenantModel):
    """Scheduled promotional pricing event."""

    __tablename__ = "pricing_promotions"

    pricing_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_price: Mapped[float] = mapped_column(Float, nullable=False)
    promo_price: Mapped[float] = mapped_column(Float, nullable=False)
    book_format: Mapped[BookFormat] = mapped_column(
        Enum(BookFormat, name="book_format", create_type=False),
        nullable=False,
        default=BookFormat.EBOOK,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PromotionStatus] = mapped_column(
        Enum(PromotionStatus, name="promotion_status"),
        nullable=False,
        default=PromotionStatus.SCHEDULED,
        server_default="scheduled",
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="amazon")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performance_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    pricing_rule: Mapped[PricingRule | None] = relationship("PricingRule", back_populates="promotions")


class PricingABTest(TenantModel):
    """Pricing A/B test configuration and results."""

    __tablename__ = "pricing_ab_tests"

    pricing_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_a: Mapped[float] = mapped_column(Float, nullable=False)
    price_b: Mapped[float] = mapped_column(Float, nullable=False)
    book_format: Mapped[BookFormat] = mapped_column(
        Enum(BookFormat, name="book_format", create_type=False),
        nullable=False,
        default=BookFormat.EBOOK,
    )
    status: Mapped[ABTestStatus] = mapped_column(
        Enum(ABTestStatus, name="ab_test_status"),
        nullable=False,
        default=ABTestStatus.DRAFT,
        server_default="draft",
    )
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    winner: Mapped[str | None] = mapped_column(String(1), nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    pricing_rule: Mapped[PricingRule | None] = relationship("PricingRule", back_populates="ab_tests")


class PricingStrategy(TenantModel):
    """Configured pricing strategy with associated books."""

    __tablename__ = "pricing_strategies"

    type = mapped_column(String(50), nullable=False)
    name = mapped_column(String(255), nullable=True)
    book_ids = mapped_column(JSONB, nullable=False, default=list)
    config = mapped_column(JSONB, nullable=False, default=dict)
    status = mapped_column(String(50), nullable=False, default="active")
    last_run_at = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("idx_pricing_strategies_org", "org_id"),)


class ScheduledPriceChange(TenantModel):
    """Scheduled future price change."""

    __tablename__ = "scheduled_price_changes"

    book_id = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    current_price = mapped_column(Numeric(10, 2), nullable=True)
    new_price = mapped_column(Numeric(10, 2), nullable=False)
    reason = mapped_column(String(255), nullable=True)
    execute_at = mapped_column(DateTime(timezone=True), nullable=False)
    revert_price = mapped_column(Numeric(10, 2), nullable=True)
    revert_at = mapped_column(DateTime(timezone=True), nullable=True)
    status = mapped_column(String(50), nullable=False, default="pending")
    executed_at = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("idx_scheduled_changes_execute", "execute_at"),)


class PriceChangeHistory(TenantModel):
    """Historical record of price changes."""

    __tablename__ = "price_change_history"

    book_id = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    old_price = mapped_column(Numeric(10, 2), nullable=True)
    new_price = mapped_column(Numeric(10, 2), nullable=False)
    reason = mapped_column(String(255), nullable=True)
    source = mapped_column(String(50), nullable=False, default="manual")
    revenue_impact_pct = mapped_column(Float, nullable=True)

    __table_args__ = (Index("idx_price_history_book", "book_id"),)
