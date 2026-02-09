"""All platform-wide enumerations shared across backend services and workers.

These are the *canonical* enum definitions.  Backend Pydantic schemas and
SQLAlchemy models should import from here to guarantee consistency.

NOTE: ``PlanTier``, ``UserRole``, and ``StatusEnum`` are also declared in
``backend/app/schemas/common.py`` for historic reasons.  The values MUST
stay in sync; tests verify this.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Identity & Access
# ---------------------------------------------------------------------------

class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    WRITER = "writer"
    VIEWER = "viewer"


# ---------------------------------------------------------------------------
# Generic status
# ---------------------------------------------------------------------------

class StatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ---------------------------------------------------------------------------
# Books / Projects
# ---------------------------------------------------------------------------

class BookFormat(str, Enum):
    EBOOK = "ebook"
    PRINT = "print"
    AUDIO = "audio"


class BookStatus(str, Enum):
    DRAFT = "draft"
    WRITING = "writing"
    EDITING = "editing"
    FORMATTING = "formatting"
    PUBLISHED = "published"


class ProjectType(str, Enum):
    BOOK = "book"
    SERIES = "series"
    COURSE = "course"


# ---------------------------------------------------------------------------
# Publishing / Distribution
# ---------------------------------------------------------------------------

class PublishingPlatform(str, Enum):
    KDP = "kdp"
    INGRAMSPARK = "ingramspark"
    DRAFT2DIGITAL = "draft2digital"
    SMASHWORDS = "smashwords"
    ACX = "acx"


class ListingStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    LIVE = "live"
    SUSPENDED = "suspended"
    REMOVED = "removed"


# ---------------------------------------------------------------------------
# Marketing / Campaigns
# ---------------------------------------------------------------------------

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignChannel(str, Enum):
    EMAIL = "email"
    SOCIAL = "social"
    ADS = "ads"
    CROSS_PROMO = "cross_promo"


class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


# ---------------------------------------------------------------------------
# AI / Agents
# ---------------------------------------------------------------------------

class AgentType(str, Enum):
    WRITING = "writing"
    EDITING = "editing"
    RESEARCH = "research"
    MARKETING = "marketing"
    COVER_DESIGN = "cover_design"
    FORMATTING = "formatting"
    ANALYTICS = "analytics"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Analytics / Reporting
# ---------------------------------------------------------------------------

class ReportType(str, Enum):
    SALES = "sales"
    ROYALTIES = "royalties"
    MARKETING = "marketing"
    AGENT_PERFORMANCE = "agent_performance"
    CUSTOM = "custom"


class UsageMetric(str, Enum):
    AI_TOKENS = "ai_tokens"
    STORAGE_BYTES = "storage_bytes"
    API_CALLS = "api_calls"
    AGENT_TASKS = "agent_tasks"


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class DigestFrequency(str, Enum):
    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"
    NONE = "none"


# ---------------------------------------------------------------------------
# Billing / Subscription
# ---------------------------------------------------------------------------

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


# ---------------------------------------------------------------------------
# Content / Templates
# ---------------------------------------------------------------------------

class ContentTemplateType(str, Enum):
    BOOK_OUTLINE = "book_outline"
    CHAPTER = "chapter"
    BLURB = "blurb"
    COVER_BRIEF = "cover_brief"
    AD_COPY = "ad_copy"
    EMAIL = "email"
    SOCIAL_POST = "social_post"
    KEYWORDS = "keywords"


# ---------------------------------------------------------------------------
# Sort / Filter
# ---------------------------------------------------------------------------

class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"
