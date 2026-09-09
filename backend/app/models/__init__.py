"""SQLAlchemy model registry — import all models so Alembic can discover them."""

# Domain models (W02: Database Schema)
from app.models.agent import Agent as DomainAgent
from app.models.agent import AgentBudget as DomainAgentBudget
from app.models.agent import AgentTask as DomainAgentTask
from app.models.agent import AgentWorkflow as DomainAgentWorkflow
from app.models.agent import AuditTrail as DomainAuditTrail
from app.models.analytics import ABTestStatus, PortfolioMetric, ReportStatus
from app.models.audiobook import (
    AudiobookChapter,
    AudiobookGenerationJob,
    AudiobookProject,
    AudiobookPronunciation,
    AudiobookVoice,
)
from app.models.content import (
    Chapter,
    ChapterVersion,
    ContentAsset,
    EditorSettings,
    Manuscript,
    StyleProfile,
    WritingSession,
)
from app.models.market import CompetitorBook, CompetitorReview, MarketCategory, MarketKeyword, MarketSnapshot
from app.models.marketing import (
    ARCCampaign,
    ARCRecipient,
    EmailSequence,
    EmailTemplate,
    LaunchPhase,
    LaunchPlan,
    PhaseTask,
    SocialPost,
)
from app.models.organization import Organization
from app.models.project import Book, BookVersion, PenName, Project, Series
from app.models.publishing import ComplianceScan, Listing, PublishingAccount, UploadValidation
from app.models.publishing import PricingRule as PublishingPricingRule
from app.models.user import ApiKey, OAuthAccount, User, UserSession

# Module-specific models
from app.modules.activity.models import ActivityLog
from app.modules.advertising.models import AdCreative, CampaignPerformance, KeywordBid
from app.modules.advertising.models import Campaign as AdCampaign
from app.modules.agent_system.models import Agent, AgentBudget, AgentTask, AgentWorkflow, AuditTrail
from app.modules.analytics.models import AnalyticsEvent, PortfolioMetricSnapshot, Report, RoyaltyRecord
from app.modules.competitor_finder.models import (
    CompetitorAlert,
    CompetitorAnalysis,
    GapAnalysisResult,
    OpportunityBlueprint,
    WeaknessSignal,
)
from app.modules.cover_design.models import Cover, ExtractedProduct, KnowledgeClip
from app.modules.dictation.models import DictationCommand, DictationSession, DictationSettings
from app.modules.knowledge_vault.models import KnowledgeEntry
from app.modules.notifications.models import Notification, NotificationPreference
from app.modules.pricing_automation.models import CompetitorPrice, PricingABTest, PricingRule, Promotion
from app.modules.product_page_lab.models import ABTest
from app.modules.production_pipeline.models import Pipeline, PipelineTask, PipelineTemplate
from app.modules.publishing_ops.models import ExportJob, FormattingTemplateModel
from app.modules.review_intelligence.models import BookReview, ReputationScore, ReviewAlert, ReviewVelocitySnapshot

__all__ = [
    # Domain models
    "Organization", "User", "ApiKey", "UserSession", "OAuthAccount",
    "Project", "Book", "Series", "PenName", "BookVersion",
    "Manuscript", "Chapter", "ChapterVersion", "StyleProfile", "WritingSession",
    "EditorSettings", "ContentAsset",
    "MarketCategory", "MarketKeyword", "CompetitorBook", "CompetitorReview", "MarketSnapshot",
    "PublishingAccount", "Listing", "UploadValidation", "ComplianceScan", "PublishingPricingRule",
    "LaunchPlan", "LaunchPhase", "PhaseTask", "EmailSequence", "EmailTemplate",
    "SocialPost", "ARCCampaign", "ARCRecipient",
    "DomainAgent", "DomainAgentTask", "DomainAgentWorkflow", "DomainAgentBudget", "DomainAuditTrail",
    "PortfolioMetric", "ABTestStatus", "ReportStatus",
    # Module models
    "ActivityLog",
    "Notification", "NotificationPreference",
    "KnowledgeEntry",
    "Pipeline", "PipelineTask", "PipelineTemplate",
    "PricingRule", "CompetitorPrice", "Promotion", "PricingABTest",
    "ABTest",
    "Cover", "ExtractedProduct", "KnowledgeClip",
    "AdCampaign", "CampaignPerformance", "KeywordBid", "AdCreative",
    "Agent", "AgentTask", "AgentWorkflow", "AgentBudget", "AuditTrail",
    "AnalyticsEvent", "RoyaltyRecord", "PortfolioMetricSnapshot", "Report",
    "BookReview", "ReviewAlert", "ReviewVelocitySnapshot", "ReputationScore",
    "CompetitorAnalysis", "WeaknessSignal", "OpportunityBlueprint", "GapAnalysisResult", "CompetitorAlert",
    "ExportJob", "FormattingTemplateModel",
    "DictationSession", "DictationCommand", "DictationSettings",
    # Audiobook models
    "AudiobookVoice", "AudiobookProject", "AudiobookChapter",
    "AudiobookPronunciation", "AudiobookGenerationJob",
]
