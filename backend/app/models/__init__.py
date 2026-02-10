"""
SQLAlchemy models for SelfPublisherForge.

All models are imported here so that Alembic can discover them
when generating migrations via Base.metadata.
"""

from app.models.organization import Organization, PlanTier, SubscriptionStatus
from app.models.user import User, ApiKey, UserSession, UserRole
from app.models.project import (
    Project,
    Book,
    Series,
    PenName,
    BookVersion,
    ProjectType,
    ProjectStatus,
    BookFormat,
    BookStatus,
    SeriesStatus,
)
from app.models.content import (
    Manuscript,
    Chapter,
    StyleProfile,
    WritingSession,
    ContentAsset,
    ContentType,
    ManuscriptStatus,
    ChapterStatus,
    AssetType,
)
from app.models.market import (
    MarketCategory,
    MarketKeyword,
    CompetitorBook,
    CompetitorReview,
    MarketSnapshot,
)
from app.models.publishing import (
    PublishingAccount,
    Listing,
    UploadValidation,
    ComplianceScan,
    PricingRule,
    PublishingPlatform,
    PublishingAccountStatus,
    ListingStatus,
    ValidationType,
    ScanType,
    RiskLevel,
)
from app.models.marketing import (
    Campaign,
    AdCreative,
    LaunchPlan,
    EmailSequence,
    ReaderPanel,
    CampaignPlatform,
    CampaignStatus,
    AdCreativeType,
    LaunchPlanStatus,
)
from app.models.agent import (
    Agent,
    AgentTask,
    AgentWorkflow,
    AgentBudget,
    AuditTrail,
    AgentType,
    PermissionLevel,
    AgentTaskStatus,
    BudgetType,
    ActorType,
)
from app.models.analytics import (
    AnalyticsEvent,
    RoyaltyRecord,
    PortfolioMetric,
    ABTest,
    Report,
    ABTestStatus,
    ReportStatus,
)

__all__ = [
    # Organization
    "Organization",
    "PlanTier",
    "SubscriptionStatus",
    # User
    "User",
    "ApiKey",
    "UserSession",
    "UserRole",
    # Project
    "Project",
    "Book",
    "Series",
    "PenName",
    "BookVersion",
    "ProjectType",
    "ProjectStatus",
    "BookFormat",
    "BookStatus",
    "SeriesStatus",
    # Content
    "Manuscript",
    "Chapter",
    "StyleProfile",
    "WritingSession",
    "ContentAsset",
    "ContentType",
    "ManuscriptStatus",
    "ChapterStatus",
    "AssetType",
    # Market
    "MarketCategory",
    "MarketKeyword",
    "CompetitorBook",
    "CompetitorReview",
    "MarketSnapshot",
    # Publishing
    "PublishingAccount",
    "Listing",
    "UploadValidation",
    "ComplianceScan",
    "PricingRule",
    "PublishingPlatform",
    "PublishingAccountStatus",
    "ListingStatus",
    "ValidationType",
    "ScanType",
    "RiskLevel",
    # Marketing
    "Campaign",
    "AdCreative",
    "LaunchPlan",
    "EmailSequence",
    "ReaderPanel",
    "CampaignPlatform",
    "CampaignStatus",
    "AdCreativeType",
    "LaunchPlanStatus",
    # Agent
    "Agent",
    "AgentTask",
    "AgentWorkflow",
    "AgentBudget",
    "AuditTrail",
    "AgentType",
    "PermissionLevel",
    "AgentTaskStatus",
    "BudgetType",
    "ActorType",
    # Analytics
    "AnalyticsEvent",
    "RoyaltyRecord",
    "PortfolioMetric",
    "ABTest",
    "Report",
    "ABTestStatus",
    "ReportStatus",
]
