"""AnalyticsEvent, RoyaltyRecord, PortfolioMetric, ABTest, and Report models."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class ABTestStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyticsEvent(BaseModel):
    __tablename__ = "analytics_events"

    org_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="analytics_events",
        primaryjoin="AnalyticsEvent.org_id == Organization.id",
        foreign_keys="[AnalyticsEvent.org_id]",
    )

    __table_args__ = (
        Index("ix_analytics_events_entity_type", "entity_type"),
        Index("ix_analytics_events_entity_id", "entity_id"),
        Index("ix_analytics_events_data_gin", "data", postgresql_using="gin"),
        Index("ix_analytics_events_timestamp_brin", "timestamp", postgresql_using="brin"),
        Index("ix_analytics_events_org_id_created_at", "org_id", "created_at"),
    )


class RoyaltyRecord(BaseModel):
    __tablename__ = "royalty_records"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    units_sold: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    revenue: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    royalty: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")

    # Relationships
    book = relationship("Book", back_populates="royalty_records")

    __table_args__ = (
        Index("ix_royalty_records_platform", "platform"),
        Index("ix_royalty_records_period_start", "period_start"),
        Index("ix_royalty_records_period_end", "period_end"),
        Index("ix_royalty_records_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class PortfolioMetric(TenantModel):
    __tablename__ = "portfolio_metrics"

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_books: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_revenue: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0"
    )
    roi_by_book: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    projections: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization", back_populates="portfolio_metrics",
        primaryjoin="PortfolioMetric.org_id == Organization.id",
        foreign_keys="[PortfolioMetric.org_id]",
    )

    __table_args__ = (
        Index("ix_portfolio_metrics_snapshot_date", "snapshot_date"),
        Index("ix_portfolio_metrics_roi_by_book_gin", "roi_by_book", postgresql_using="gin"),
        Index("ix_portfolio_metrics_projections_gin", "projections", postgresql_using="gin"),
        Index("ix_portfolio_metrics_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_portfolio_metrics_org_id_created_at", "org_id", "created_at"),
    )


class ABTest(BaseModel):
    __tablename__ = "ab_tests"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    variants: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    traffic_split: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    status: Mapped[ABTestStatus] = mapped_column(
        SAEnum(ABTestStatus, name="ab_test_status", create_constraint=True),
        default=ABTestStatus.DRAFT,
        server_default="draft",
    )
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    winner_id: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    __table_args__ = (
        Index("ix_ab_tests_entity_type", "entity_type"),
        Index("ix_ab_tests_status", "status"),
        Index("ix_ab_tests_variants_gin", "variants", postgresql_using="gin"),
        Index("ix_ab_tests_results_gin", "results", postgresql_using="gin"),
        Index("ix_ab_tests_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class Report(TenantModel):
    __tablename__ = "reports"

    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    generated_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status", create_constraint=True),
        default=ReportStatus.PENDING,
        server_default="pending",
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="reports",
        primaryjoin="Report.org_id == Organization.id",
        foreign_keys="[Report.org_id]",
    )

    __table_args__ = (
        Index("ix_reports_report_type", "report_type"),
        Index("ix_reports_status", "status"),
        Index("ix_reports_parameters_gin", "parameters", postgresql_using="gin"),
        Index("ix_reports_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_reports_org_id_created_at", "org_id", "created_at"),
    )
