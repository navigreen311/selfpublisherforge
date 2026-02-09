"""Campaign, AdCreative, LaunchPlan, EmailSequence, and ReaderPanel models."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class CampaignPlatform(str, enum.Enum):
    AMAZON_ADS = "amazon_ads"
    FACEBOOK = "facebook"
    BOOKBUB = "bookbub"
    GOOGLE = "google"
    TIKTOK = "tiktok"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AdCreativeType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    CAROUSEL = "carousel"


class LaunchPlanStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Campaign(TenantModel):
    __tablename__ = "campaigns"

    book_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    platform: Mapped[CampaignPlatform] = mapped_column(
        SAEnum(CampaignPlatform, name="campaign_platform", create_constraint=True),
        nullable=False,
    )
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status", create_constraint=True),
        default=CampaignStatus.DRAFT,
        server_default="draft",
    )
    budget: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    spend: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization", back_populates="campaigns",
        primaryjoin="Campaign.org_id == Organization.id",
        foreign_keys="[Campaign.org_id]",
    )
    book = relationship("Book", back_populates="campaigns")
    ad_creatives = relationship("AdCreative", back_populates="campaign", lazy="selectin")

    __table_args__ = (
        Index("ix_campaigns_platform", "platform"),
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_results_gin", "results", postgresql_using="gin"),
        Index("ix_campaigns_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_campaigns_org_id_created_at", "org_id", "created_at"),
    )


class AdCreative(BaseModel):
    __tablename__ = "ad_creatives"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[AdCreativeType] = mapped_column(
        SAEnum(AdCreativeType, name="ad_creative_type", create_constraint=True),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    performance: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    campaign = relationship("Campaign", back_populates="ad_creatives")

    __table_args__ = (
        Index("ix_ad_creatives_type", "type"),
        Index("ix_ad_creatives_active", "active"),
        Index("ix_ad_creatives_performance_gin", "performance", postgresql_using="gin"),
        Index("ix_ad_creatives_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class LaunchPlan(BaseModel):
    __tablename__ = "launch_plans"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    phases: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    status: Mapped[LaunchPlanStatus] = mapped_column(
        SAEnum(LaunchPlanStatus, name="launch_plan_status", create_constraint=True),
        default=LaunchPlanStatus.PLANNING,
        server_default="planning",
    )
    checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    book = relationship("Book", back_populates="launch_plans")

    __table_args__ = (
        Index("ix_launch_plans_status", "status"),
        Index("ix_launch_plans_launch_date", "launch_date"),
        Index("ix_launch_plans_phases_gin", "phases", postgresql_using="gin"),
        Index("ix_launch_plans_checklist_gin", "checklist", postgresql_using="gin"),
        Index("ix_launch_plans_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class EmailSequence(TenantModel):
    __tablename__ = "email_sequences"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    emails: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    performance: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization", back_populates="email_sequences",
        primaryjoin="EmailSequence.org_id == Organization.id",
        foreign_keys="[EmailSequence.org_id]",
    )

    __table_args__ = (
        Index("ix_email_sequences_trigger", "trigger"),
        Index("ix_email_sequences_emails_gin", "emails", postgresql_using="gin"),
        Index("ix_email_sequences_performance_gin", "performance", postgresql_using="gin"),
        Index("ix_email_sequences_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_email_sequences_org_id_created_at", "org_id", "created_at"),
    )


class ReaderPanel(TenantModel):
    __tablename__ = "reader_panels"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    panel_size: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    recruitment_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    tests: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization", back_populates="reader_panels",
        primaryjoin="ReaderPanel.org_id == Organization.id",
        foreign_keys="[ReaderPanel.org_id]",
    )

    __table_args__ = (
        Index("ix_reader_panels_recruitment_criteria_gin", "recruitment_criteria", postgresql_using="gin"),
        Index("ix_reader_panels_tests_gin", "tests", postgresql_using="gin"),
        Index("ix_reader_panels_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_reader_panels_org_id_created_at", "org_id", "created_at"),
    )
