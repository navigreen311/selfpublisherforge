"""SQLAlchemy models for the Marketing & Launch Command module."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel

# Import canonical Campaign and AdCreative from the advertising module
from app.modules.advertising.models import AdCreative, Campaign  # noqa: F401

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LaunchPlanStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LaunchPhaseType(str, PyEnum):
    PRE_LAUNCH = "pre_launch"
    LAUNCH_WEEK = "launch_week"
    POST_LAUNCH = "post_launch"


class PhaseTaskStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class EmailSequenceStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EmailTemplateType(str, PyEnum):
    WELCOME = "welcome"
    LAUNCH_ANNOUNCEMENT = "launch_announcement"
    FOLLOW_UP = "follow_up"
    REVIEW_REQUEST = "review_request"
    CUSTOM = "custom"


class EmailSendStatus(str, PyEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class SocialPlatform(str, PyEnum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class SocialPostStatus(str, PyEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ARCCampaignStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SENDING = "sending"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ARCRecipientStatus(str, PyEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    REVIEWED = "reviewed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class LaunchPlan(TenantModel):
    """Top-level launch plan for a book."""

    __tablename__ = "launch_plans"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LaunchPlanStatus] = mapped_column(
        Enum(LaunchPlanStatus, name="launch_plan_status", create_constraint=False),
        default=LaunchPlanStatus.DRAFT,
        server_default="draft",
    )
    launch_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    goals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    phases_json: Mapped[dict | None] = mapped_column("phases_data", JSON, nullable=True)
    checklist: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    # Relationships
    book = relationship("Book", back_populates="launch_plans")
    phases: Mapped[list["LaunchPhase"]] = relationship(
        "LaunchPhase",
        back_populates="launch_plan",
        cascade="all, delete-orphan",
        order_by="LaunchPhase.order_index",
    )


class LaunchPhase(BaseModel):
    """A phase within a launch plan (pre-launch, launch week, post-launch)."""

    __tablename__ = "launch_phases"

    launch_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("launch_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_type: Mapped[LaunchPhaseType] = mapped_column(
        Enum(LaunchPhaseType, name="launch_phase_type", create_constraint=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    launch_plan: Mapped["LaunchPlan"] = relationship("LaunchPlan", back_populates="phases")
    tasks: Mapped[list["PhaseTask"]] = relationship(
        "PhaseTask",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="PhaseTask.order_index",
    )


class PhaseTask(BaseModel):
    """An individual task within a launch phase."""

    __tablename__ = "phase_tasks"

    phase_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("launch_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PhaseTaskStatus] = mapped_column(
        Enum(PhaseTaskStatus, name="phase_task_status", create_constraint=False),
        default=PhaseTaskStatus.PENDING,
        server_default="pending",
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    phase: Mapped["LaunchPhase"] = relationship("LaunchPhase", back_populates="tasks")


class EmailSequence(TenantModel):
    """A marketing email sequence (drip campaign)."""

    __tablename__ = "email_sequences"

    launch_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("launch_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EmailSequenceStatus] = mapped_column(
        Enum(EmailSequenceStatus, name="email_sequence_status", create_constraint=False),
        default=EmailSequenceStatus.DRAFT,
        server_default="draft",
    )
    trigger_event: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    open_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    click_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    emails_json: Mapped[dict | None] = mapped_column("emails_data", JSON, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="email_sequences",
        primaryjoin="EmailSequence.org_id == Organization.id",
        foreign_keys="[EmailSequence.org_id]",
    )
    emails: Mapped[list["EmailTemplate"]] = relationship(
        "EmailTemplate",
        back_populates="sequence",
        cascade="all, delete-orphan",
        order_by="EmailTemplate.order_index",
    )


class EmailTemplate(BaseModel):
    """An individual email within a sequence."""

    __tablename__ = "email_templates"

    sequence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("email_sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_type: Mapped[EmailTemplateType] = mapped_column(
        Enum(EmailTemplateType, name="email_template_type", create_constraint=False),
        default=EmailTemplateType.CUSTOM,
    )
    subject: Mapped[str] = mapped_column(String(1000), nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    delay_days: Mapped[int] = mapped_column(Integer, default=0)
    delay_hours: Mapped[int] = mapped_column(Integer, default=0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    personalization_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)
    send_status: Mapped[EmailSendStatus] = mapped_column(
        Enum(EmailSendStatus, name="email_send_status", create_constraint=False),
        default=EmailSendStatus.PENDING,
        server_default="pending",
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sequence: Mapped["EmailSequence"] = relationship("EmailSequence", back_populates="emails")


class ReaderPanel(TenantModel):
    """A panel of beta readers or ARC reviewers."""

    __tablename__ = "reader_panels"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    panel_size: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    recruitment_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    tests: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    feedback_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="reader_panels",
        primaryjoin="ReaderPanel.org_id == Organization.id",
        foreign_keys="[ReaderPanel.org_id]",
    )

    __table_args__ = (
        Index("ix_reader_panels_recruitment_criteria_gin", "recruitment_criteria", postgresql_using="gin"),
        Index("ix_reader_panels_feedback_summary_gin", "feedback_summary", postgresql_using="gin"),
        Index("ix_reader_panels_tests_gin", "tests", postgresql_using="gin"),
        Index("ix_reader_panels_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_reader_panels_org_id_created_at", "org_id", "created_at"),
    )


class SocialPost(TenantModel):
    """A social media post for marketing."""

    __tablename__ = "social_posts"

    launch_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("launch_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, name="social_platform", create_constraint=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SocialPostStatus] = mapped_column(
        Enum(SocialPostStatus, name="social_post_status", create_constraint=False),
        default=SocialPostStatus.DRAFT,
        server_default="draft",
    )
    engagement_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)


class ARCCampaign(TenantModel):
    """Advance Review Copy campaign."""

    __tablename__ = "arc_campaigns"

    launch_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("launch_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ARCCampaignStatus] = mapped_column(
        Enum(ARCCampaignStatus, name="arc_campaign_status", create_constraint=False),
        default=ARCCampaignStatus.DRAFT,
        server_default="draft",
    )
    book_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_copies: Mapped[int] = mapped_column(Integer, default=0)
    sent_copies: Mapped[int] = mapped_column(Integer, default=0)
    reviews_received: Mapped[int] = mapped_column(Integer, default=0)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    # Relationships
    recipients: Mapped[list["ARCRecipient"]] = relationship(
        "ARCRecipient",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class ARCRecipient(BaseModel):
    """A recipient of an ARC campaign."""

    __tablename__ = "arc_recipients"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("arc_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    email: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ARCRecipientStatus] = mapped_column(
        Enum(ARCRecipientStatus, name="arc_recipient_status", create_constraint=False),
        default=ARCRecipientStatus.PENDING,
        server_default="pending",
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    campaign: Mapped["ARCCampaign"] = relationship("ARCCampaign", back_populates="recipients")
