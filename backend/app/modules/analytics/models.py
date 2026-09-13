"""SQLAlchemy models for the Analytics & BI module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class AnalyticsEvent(TenantModel):
    """Raw analytics events captured from user actions, system events, etc."""

    __tablename__ = "analytics_events"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_source: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="analytics_events",
        primaryjoin="AnalyticsEvent.org_id == Organization.id",
        foreign_keys="[AnalyticsEvent.org_id]",
    )

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_analytics_events_data_gin", "data", postgresql_using="gin"),
        Index("ix_analytics_events_entity_id", "entity_id"),
        Index("ix_analytics_events_entity_type", "entity_type"),
        Index("ix_analytics_events_org_id_created_at", "org_id", "created_at"),
        Index("ix_analytics_events_org_id_event_type", "org_id", "event_type"),
        Index("ix_analytics_events_timestamp_brin", "timestamp", postgresql_using="brin"),
        Index("ix_analytics_events_org_occurred", "org_id", "occurred_at"),
        Index("ix_analytics_events_type_occurred", "event_type", "occurred_at"),
        {"extend_existing": True},
    )


class RoyaltyRecord(TenantModel):
    """Royalty records imported from publishing platforms (KDP, IngramSpark, D2D, etc.)."""

    __tablename__ = "royalty_records"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)

    book_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(100), nullable=False, default="US")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    asin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    format_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ebook")
    units_sold: Mapped[int] = mapped_column(nullable=False, default=0)
    units_refunded: Mapped[int] = mapped_column(nullable=False, default=0)
    net_units: Mapped[int] = mapped_column(nullable=False, default=0)
    list_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    royalty_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.70"))
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    book = relationship(
        "Book",
        back_populates="royalty_records",
        primaryjoin="RoyaltyRecord.book_id == Book.id",
        foreign_keys="[RoyaltyRecord.book_id]",
    )

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    royalty: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("ix_royalty_records_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_royalty_records_period_end", "period_end"),
        Index("ix_royalty_records_org_period", "org_id", "period_start"),
        Index("ix_royalty_records_platform_period", "platform", "period_start"),
        {"extend_existing": True},
    )


class PortfolioMetricSnapshot(TenantModel):
    """Point-in-time snapshots of portfolio-level metrics (computed daily)."""

    __tablename__ = "portfolio_metrics"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    total_books: Mapped[int] = mapped_column(nullable=False, default=0)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_units_sold: Mapped[int] = mapped_column(nullable=False, default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    avg_roi: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0.00"))
    platform_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    format_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    top_books: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    metrics_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="portfolio_metrics",
        primaryjoin="PortfolioMetricSnapshot.org_id == Organization.id",
        foreign_keys="[PortfolioMetricSnapshot.org_id]",
    )

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    roi_by_book: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    projections: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    __table_args__ = (
        Index("ix_portfolio_metrics_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_portfolio_metrics_org_id_created_at", "org_id", "created_at"),
        Index("ix_portfolio_metrics_projections_gin", "projections", postgresql_using="gin"),
        Index("ix_portfolio_metrics_roi_by_book_gin", "roi_by_book", postgresql_using="gin"),
        Index("ix_portfolio_metrics_org_date", "org_id", "snapshot_date"),
        {"extend_existing": True},
    )


class Report(TenantModel):
    """Generated reports (PDF, XLSX) stored for download."""

    __tablename__ = "reports"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    output_format: Mapped[str] = mapped_column(String(10), nullable=False, default="pdf")
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="reports",
        primaryjoin="Report.org_id == Organization.id",
        foreign_keys="[Report.org_id]",
    )

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    generated_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    book_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    sections: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    __table_args__ = (
        Index("ix_reports_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_reports_org_id_created_at", "org_id", "created_at"),
        Index("ix_reports_parameters_gin", "parameters", postgresql_using="gin"),
        Index("ix_reports_status", "status"),
        Index("ix_reports_org_type", "org_id", "report_type"),
        {"extend_existing": True},
    )


class SalesData(TenantModel):
    """Daily sales data per book/marketplace/format."""

    __tablename__ = "sales_data"

    book_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(10), nullable=False, default="US")
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    units: Mapped[int] = mapped_column(nullable=False, default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    royalties: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    kenp_read: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "org_id", "book_id", "date", "marketplace", "format", name="uq_sales_data_org_book_date_mp_fmt"
        ),
        Index("idx_sales_data_book", "book_id"),
        Index("idx_sales_data_org_date", "org_id", "date"),
        Index("ix_sales_data_org_date", "org_id", "date"),
        Index("ix_sales_data_book_date", "book_id", "date"),
        {"extend_existing": True},
    )


class BSRTracking(TenantModel):
    """BSR rank tracking over time for books."""

    __tablename__ = "bsr_tracking"

    book_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(10), nullable=False, default="US")
    bsr: Mapped[int | None] = mapped_column(nullable=True)
    category_rank: Mapped[int | None] = mapped_column(nullable=True)
    category_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_bsr_tracking_book", "book_id"),
        Index("ix_bsr_tracking_book_recorded", "book_id", "recorded_at"),
        {"extend_existing": True},
    )
