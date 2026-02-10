"""SQLAlchemy model registry — import all models so Alembic can discover them."""

# Domain models (W02: Database Schema)
from app.models.organization import Organization
from app.models.user import User, ApiKey, UserSession
from app.models.project import Project, Book, Series, PenName, BookVersion
from app.models.content import Manuscript, Chapter, StyleProfile, WritingSession, ContentAsset
from app.models.market import MarketCategory, MarketKeyword, CompetitorBook, CompetitorReview, MarketSnapshot
from app.models.publishing import PublishingAccount, Listing, UploadValidation, ComplianceScan, PricingRule as PublishingPricingRule
from app.models.marketing import Campaign as MarketingCampaign, AdCreative as MarketingAdCreative, LaunchPlan as MarketingLaunchPlan, EmailSequence as MarketingEmailSequence, ReaderPanel
from app.models.agent import Agent as DomainAgent, AgentTask as DomainAgentTask, AgentWorkflow as DomainAgentWorkflow, AgentBudget as DomainAgentBudget, AuditTrail as DomainAuditTrail
from app.models.analytics import AnalyticsEvent as DomainAnalyticsEvent, RoyaltyRecord as DomainRoyaltyRecord, PortfolioMetric, ABTest as DomainABTest, Report as DomainReport

# Module-specific models
from app.modules.notifications.models import Notification, NotificationPreference
from app.modules.knowledge_vault.models import KnowledgeEntry
from app.modules.production_pipeline.models import Pipeline, PipelineTask, PipelineTemplate
from app.modules.pricing_automation.models import PricingRule, CompetitorPrice, Promotion, PricingABTest
from app.modules.product_page_lab.models import ABTest
from app.modules.cover_design.models import Cover, ExtractedProduct, KnowledgeClip
from app.modules.advertising.models import Campaign as AdCampaign, CampaignPerformance, KeywordBid, AdCreative
from app.modules.agent_system.models import Agent, AgentTask, AgentWorkflow, AgentBudget, AuditTrail
from app.modules.analytics.models import AnalyticsEvent, RoyaltyRecord, PortfolioMetricSnapshot, Report
from app.modules.review_intelligence.models import BookReview, ReviewAlert, ReviewVelocitySnapshot, ReputationScore
from app.modules.competitor_finder.models import CompetitorAnalysis, WeaknessSignal, OpportunityBlueprint, GapAnalysisResult, CompetitorAlert

__all__ = [
    # Domain models
    "Organization", "User", "ApiKey", "UserSession",
    "Project", "Book", "Series", "PenName", "BookVersion",
    "Manuscript", "Chapter", "StyleProfile", "WritingSession", "ContentAsset",
    "MarketCategory", "MarketKeyword", "CompetitorBook", "CompetitorReview", "MarketSnapshot",
    "PublishingAccount", "Listing", "UploadValidation", "ComplianceScan", "PublishingPricingRule",
    "MarketingCampaign", "MarketingAdCreative", "MarketingLaunchPlan", "MarketingEmailSequence", "ReaderPanel",
    "DomainAgent", "DomainAgentTask", "DomainAgentWorkflow", "DomainAgentBudget", "DomainAuditTrail",
    "DomainAnalyticsEvent", "DomainRoyaltyRecord", "PortfolioMetric", "DomainABTest", "DomainReport",
    # Module models
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
]
