"""SQLAlchemy models for Advertising Intelligence module."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class Campaign(TenantModel):
    """Ad campaign across platforms (Amazon, Facebook)."""

    __tablename__ = "campaigns"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("books.id", ondelete="SET NULL"), nullable=True
    )
    daily_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    bid_strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    target_acos: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    targeting_keywords: Mapped[list] = mapped_column(JSON, default=list)
    negative_keywords: Mapped[list] = mapped_column(JSON, default=list)
    external_campaign_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    book = relationship(
        "Book",
        back_populates="campaigns",
        primaryjoin="Campaign.book_id == Book.id",
        foreign_keys="[Campaign.book_id]",
    )
    keyword_bids: Mapped[list["KeywordBid"]] = relationship("KeywordBid", back_populates="campaign", lazy="selectin")
    performance_records: Mapped[list["CampaignPerformance"]] = relationship(
        "CampaignPerformance", back_populates="campaign", lazy="selectin"
    )
    creatives: Mapped[list["AdCreative"]] = relationship("AdCreative", back_populates="campaign", lazy="selectin")
    organization = relationship(
        "Organization",
        back_populates="campaigns",
        primaryjoin="Campaign.org_id == Organization.id",
        foreign_keys="[Campaign.org_id]",
    )

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    spend: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    targeting_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    match_types: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    bidding_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    default_bid: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    schedule_start: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    schedule_end: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    ad_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    total_spend: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    total_sales: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    total_impressions: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    total_clicks: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    total_orders: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    __table_args__ = (
        Index("ix_campaigns_book_id", "book_id"),
        Index("ix_campaigns_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_campaigns_org_id_created_at", "org_id", "created_at"),
        Index("ix_campaigns_org_id_platform", "org_id", "platform"),
        Index("ix_campaigns_org_id_status", "org_id", "status"),
        Index("ix_campaigns_results_gin", "results", postgresql_using="gin"),
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_org_platform", "org_id", "platform"),
        Index("ix_campaigns_org_status", "org_id", "status"),
    )


class CampaignPerformance(BaseModel):
    """Daily performance metrics for a campaign."""

    __tablename__ = "campaign_performance"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[float] = mapped_column(Float, default=0.0)
    sales: Mapped[float] = mapped_column(Float, default=0.0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    acos: Mapped[float] = mapped_column(Float, default=0.0)
    roas: Mapped[float] = mapped_column(Float, default=0.0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    cpc: Mapped[float] = mapped_column(Float, default=0.0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="performance_records")

    __table_args__ = (Index("ix_perf_campaign_date", "campaign_id", "date"),)


class KeywordBid(BaseModel):
    """Keyword-level bid for a campaign."""

    __tablename__ = "keyword_bids"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, default="broad")
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_negative: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Performance metrics (denormalized for quick access)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[float] = mapped_column(Float, default=0.0)
    sales: Mapped[float] = mapped_column(Float, default=0.0)
    acos: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="keyword_bids")

    __table_args__ = (Index("ix_keyword_bids_campaign_keyword", "campaign_id", "keyword"),)


class AdCreative(TenantModel):
    """Ad creative (headline, body, CTA) associated with a campaign."""

    __tablename__ = "ad_creatives"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    book_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    headline: Mapped[str] = mapped_column(String(150), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    call_to_action: Mapped[str] = mapped_column(String(50), default="Buy Now")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    # Performance metrics (denormalized)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    campaign: Mapped["Campaign | None"] = relationship("Campaign", back_populates="creatives")

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    type: Mapped[str | None] = mapped_column(
        ENUM(name="ad_creative_type", create_type=False), nullable=True, default=None
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    performance: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        Index("ix_ad_creatives_org_campaign", "org_id", "campaign_id"),
        Index("ix_ad_creatives_active", "active"),
        Index("ix_ad_creatives_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_ad_creatives_performance_gin", "performance", postgresql_using="gin"),
        Index("ix_ad_creatives_type", "type"),
    )


class AdSearchTerm(BaseModel):
    """Search term report data for a campaign."""

    __tablename__ = "ad_search_terms"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    search_term: Mapped[str] = mapped_column(String(500), nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    sales: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign")

    __table_args__ = (Index("idx_ad_search_terms_campaign", "campaign_id"),)


class AdDailyMetric(BaseModel):
    """Aggregated daily metrics for a campaign."""

    __tablename__ = "ad_daily_metrics"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    spend: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    sales: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign")

    __table_args__ = (
        UniqueConstraint("campaign_id", "date", name="uq_ad_daily_metrics_campaign_date"),
        Index("ix_daily_metrics_campaign_date", "campaign_id", "date", unique=True),
        Index("idx_ad_daily_metrics_campaign_date", "campaign_id", "date"),
    )
