"""Organization model."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Index, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel


class PlanTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan_tier: Mapped[PlanTier] = mapped_column(
        SAEnum(PlanTier, name="plan_tier", create_constraint=True),
        default=PlanTier.FREE,
        server_default="free",
    )
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", create_constraint=True),
        default=SubscriptionStatus.ACTIVE,
        server_default="active",
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships - User/ApiKey have explicit FK to organizations.id
    users = relationship("User", back_populates="organization", lazy="selectin")
    api_keys = relationship("ApiKey", back_populates="organization", lazy="selectin")

    # Relationships - TenantModel subclasses use org_id without FK constraint.
    # We must supply explicit primaryjoin + foreign_keys.
    projects = relationship(
        "Project", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(Project.org_id)",
    )
    series = relationship(
        "Series", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(Series.org_id)",
    )
    pen_names = relationship(
        "PenName", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(PenName.org_id)",
    )
    style_profiles = relationship(
        "StyleProfile", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(StyleProfile.org_id)",
    )
    content_assets = relationship(
        "ContentAsset", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(ContentAsset.org_id)",
    )
    publishing_accounts = relationship(
        "PublishingAccount", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(PublishingAccount.org_id)",
    )
    campaigns = relationship(
        "Campaign", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(Campaign.org_id)",
    )
    email_sequences = relationship(
        "EmailSequence", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(EmailSequence.org_id)",
    )
    reader_panels = relationship(
        "ReaderPanel", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(ReaderPanel.org_id)",
    )
    agents = relationship(
        "Agent", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(Agent.org_id)",
    )
    agent_workflows = relationship(
        "AgentWorkflow", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(AgentWorkflow.org_id)",
    )
    agent_budgets = relationship(
        "AgentBudget", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(AgentBudget.org_id)",
    )
    audit_trails = relationship(
        "AuditTrail", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(AuditTrail.org_id)",
    )
    analytics_events = relationship(
        "AnalyticsEvent", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(AnalyticsEvent.org_id)",
    )
    portfolio_metrics = relationship(
        "PortfolioMetric", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(PortfolioMetric.org_id)",
    )
    reports = relationship(
        "Report", back_populates="organization", lazy="selectin",
        primaryjoin="Organization.id == foreign(Report.org_id)",
    )

    __table_args__ = (
        Index("ix_organizations_plan_tier", "plan_tier"),
        Index("ix_organizations_subscription_status", "subscription_status"),
        Index("ix_organizations_settings_gin", "settings", postgresql_using="gin"),
        Index("ix_organizations_limits_gin", "limits", postgresql_using="gin"),
        Index("ix_organizations_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
