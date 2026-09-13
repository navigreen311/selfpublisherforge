"""Pydantic v2 schemas for Advertising Intelligence module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ─── Enums ────────────────────────────────────────────────────────────────────


class AdPlatform(str, Enum):
    AMAZON = "amazon"
    FACEBOOK = "facebook"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"


class CampaignType(str, Enum):
    SPONSORED_PRODUCTS = "sponsored_products"
    SPONSORED_BRANDS = "sponsored_brands"
    SPONSORED_DISPLAY = "sponsored_display"
    LOCKSCREEN = "lockscreen"
    FACEBOOK_FEED = "facebook_feed"
    FACEBOOK_STORIES = "facebook_stories"


class BidStrategy(str, Enum):
    MANUAL = "manual"
    AUTO_LOW = "auto_low"
    AUTO_HIGH = "auto_high"
    RULE_BASED = "rule_based"


class MatchType(str, Enum):
    EXACT = "exact"
    PHRASE = "phrase"
    BROAD = "broad"


class CreativeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    REJECTED = "rejected"


# ─── Campaign Schemas ─────────────────────────────────────────────────────────


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    platform: AdPlatform
    campaign_type: CampaignType
    book_id: UUID | None = None
    daily_budget: float = Field(..., gt=0, le=100000)
    total_budget: float | None = Field(None, gt=0)
    bid_strategy: BidStrategy = BidStrategy.MANUAL
    target_acos: float | None = Field(None, ge=0, le=100, description="Target ACOS percentage")
    start_date: datetime | None = None
    end_date: datetime | None = None
    targeting_keywords: list[str] = []
    negative_keywords: list[str] = []


class CampaignUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: CampaignStatus | None = None
    daily_budget: float | None = Field(None, gt=0, le=100000)
    total_budget: float | None = Field(None, gt=0)
    bid_strategy: BidStrategy | None = None
    target_acos: float | None = Field(None, ge=0, le=100)
    end_date: datetime | None = None
    targeting_keywords: list[str] | None = None
    negative_keywords: list[str] | None = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    platform: AdPlatform
    campaign_type: CampaignType
    status: CampaignStatus
    book_id: UUID | None = None
    daily_budget: float
    total_budget: float | None = None
    bid_strategy: BidStrategy
    target_acos: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    targeting_keywords: list[str] = []
    negative_keywords: list[str] = []
    external_campaign_id: str | None = None
    created_at: datetime
    updated_at: datetime


# ─── Performance Schemas ──────────────────────────────────────────────────────


class AdPerformance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    date: datetime
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    sales: float = 0.0
    orders: int = 0
    acos: float = 0.0
    roas: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    conversion_rate: float = 0.0


class PerformanceSummary(BaseModel):
    total_impressions: int = 0
    total_clicks: int = 0
    total_spend: float = 0.0
    total_sales: float = 0.0
    total_orders: int = 0
    avg_acos: float = 0.0
    avg_roas: float = 0.0
    avg_ctr: float = 0.0
    avg_cpc: float = 0.0
    avg_conversion_rate: float = 0.0
    period_start: datetime | None = None
    period_end: datetime | None = None


class CampaignWithPerformance(CampaignResponse):
    performance_summary: PerformanceSummary | None = None


# ─── Keyword Bid Schemas ─────────────────────────────────────────────────────


class KeywordBidCreate(BaseModel):
    campaign_id: UUID
    keyword: str = Field(..., min_length=1, max_length=255)
    match_type: MatchType = MatchType.BROAD
    bid_amount: float = Field(..., gt=0, le=1000)
    is_negative: bool = False


class KeywordBidUpdate(BaseModel):
    bid_amount: float | None = Field(None, gt=0, le=1000)
    match_type: MatchType | None = None
    is_active: bool | None = None


class KeywordBidBulkUpdate(BaseModel):
    updates: list[dict] = Field(..., description="List of {id: UUID, bid_amount: float} objects")


class KeywordBidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    keyword: str
    match_type: MatchType
    bid_amount: float
    is_negative: bool = False
    is_active: bool = True
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    sales: float = 0.0
    acos: float = 0.0
    created_at: datetime
    updated_at: datetime


# ─── Ad Creative Schemas ──────────────────────────────────────────────────────


class AdCreativeCreate(BaseModel):
    campaign_id: UUID | None = None
    book_id: UUID | None = None
    headline: str = Field(..., min_length=1, max_length=150)
    body_text: str = Field(..., min_length=1, max_length=1000)
    call_to_action: str = "Buy Now"
    image_url: str | None = None


class AdCreativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    campaign_id: UUID | None = None
    book_id: UUID | None = None
    headline: str
    body_text: str
    call_to_action: str
    image_url: str | None = None
    status: CreativeStatus = CreativeStatus.DRAFT
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    conversions: int = 0
    created_at: datetime
    updated_at: datetime


class CreativeGenerateRequest(BaseModel):
    book_id: UUID | None = None
    book_title: str = Field(..., min_length=1, max_length=500)
    book_description: str = Field(..., min_length=1, max_length=5000)
    genre: str = ""
    target_audience: str = ""
    tone: str = "professional"
    num_variations: int = Field(3, ge=1, le=10)
    platform: AdPlatform = AdPlatform.AMAZON


class GeneratedCreative(BaseModel):
    headline: str
    body_text: str
    call_to_action: str
    reasoning: str = ""


class CreativeGenerateResponse(BaseModel):
    variations: list[GeneratedCreative]
    platform: AdPlatform
    book_title: str


# ─── Optimization Schemas ────────────────────────────────────────────────────


class OptimizationRequest(BaseModel):
    target_acos: float | None = Field(None, ge=0, le=100)
    max_bid_increase_pct: float = Field(20.0, ge=0, le=100)
    max_bid_decrease_pct: float = Field(30.0, ge=0, le=100)
    min_data_points: int = Field(7, ge=1, description="Min days of data before optimizing")


class BidAdjustment(BaseModel):
    keyword_bid_id: UUID
    keyword: str
    current_bid: float
    suggested_bid: float
    reason: str
    expected_acos_impact: float = 0.0


class OptimizationSuggestion(BaseModel):
    campaign_id: UUID
    campaign_name: str
    current_acos: float
    target_acos: float
    bid_adjustments: list[BidAdjustment] = []
    keywords_to_add: list[str] = []
    keywords_to_negate: list[str] = []
    budget_recommendation: float | None = None
    summary: str = ""


# ─── Dashboard Schemas ───────────────────────────────────────────────────────


class AdDashboard(BaseModel):
    total_active_campaigns: int = 0
    total_spend_today: float = 0.0
    total_spend_month: float = 0.0
    total_sales_month: float = 0.0
    overall_acos: float = 0.0
    overall_roas: float = 0.0
    top_campaigns: list[CampaignWithPerformance] = []
    platform_breakdown: dict[str, PerformanceSummary] = {}
    recent_optimizations: list[str] = []


# ─── Facebook Ads Schemas ────────────────────────────────────────────────────


class FacebookObjective(str, Enum):
    OUTCOME_SALES = "OUTCOME_SALES"
    OUTCOME_LEADS = "OUTCOME_LEADS"
    OUTCOME_ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    OUTCOME_AWARENESS = "OUTCOME_AWARENESS"
    OUTCOME_TRAFFIC = "OUTCOME_TRAFFIC"
    OUTCOME_APP_PROMOTION = "OUTCOME_APP_PROMOTION"


class FacebookCampaignStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


class FacebookCampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    objective: FacebookObjective = FacebookObjective.OUTCOME_SALES
    daily_budget: float = Field(0.0, ge=0, le=1000000, description="Daily budget in dollars")
    status: FacebookCampaignStatus = FacebookCampaignStatus.PAUSED


class FacebookCampaignUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: FacebookCampaignStatus | None = None
    daily_budget: float | None = Field(None, ge=0, le=1000000)


class FacebookCampaignResponse(BaseModel):
    external_campaign_id: str
    name: str | None = None
    objective: str | None = None
    status: str | None = None
    daily_budget: float | None = None
    created: bool | None = None
    updated: bool | None = None
    changes: dict | None = None


class FacebookCampaignListResponse(BaseModel):
    campaigns: list[FacebookCampaignResponse] = []
    total_count: int = 0


class FacebookCampaignMetrics(BaseModel):
    external_campaign_id: str
    start_date: str
    end_date: str
    metrics: dict = {}
    report_status: str = "completed"


# ─── Filter / Query Schemas ──────────────────────────────────────────────────


class CampaignFilter(BaseModel):
    platform: AdPlatform | None = None
    status: CampaignStatus | None = None
    campaign_type: CampaignType | None = None
    book_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class PerformanceQuery(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    granularity: str = Field("daily", pattern="^(daily|weekly|monthly)$")


# ─── Enhanced Advertising Schemas ────────────────────────────────────────────


class SearchTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    search_term: str
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    sales: float = 0.0
    orders: int = 0
    action_taken: str | None = None
    recorded_at: datetime | None = None


class DailyMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    campaign_id: UUID | None = None
    date: datetime | str
    spend: float = 0.0
    sales: float = 0.0
    impressions: int = 0
    clicks: int = 0
    orders: int = 0


class AIInsight(BaseModel):
    type: str
    message: str
    campaign_id: str | None = None
    action: str | None = None
    severity: str = "info"  # "info" | "warning" | "success"


class AIInsightsResponse(BaseModel):
    insights: list[AIInsight]


class KeywordSuggestion(BaseModel):
    keyword: str
    search_volume: int
    suggested_bid: float
    competition: str = "medium"  # "low" | "medium" | "high"


class KeywordSuggestionsResponse(BaseModel):
    keywords: list[KeywordSuggestion]


class BidRecommendation(BaseModel):
    keyword: str
    current_bid: float
    suggested_bid: float
    reason: str
    expected_acos_impact: float = 0.0


class BidOptimizationRequest(BaseModel):
    target_acos: float = 30.0
    strategy: str = "maximize_sales"  # "maximize_sales" | "minimize_acos" | "maximize_impressions"


class BidOptimizationResponse(BaseModel):
    recommendations: list[BidRecommendation]
    estimated_impact: dict = {}


class EnhancedDashboardResponse(BaseModel):
    stats: dict
    trend_data: list[DailyMetricResponse] = []
    top_campaigns: list[dict] = []
    insights: list[AIInsight] = []


class CampaignCreateRequest(BaseModel):
    platform: str
    ad_type: str = "sponsored_products"
    book_id: str | None = None
    name: str
    targeting_type: str | None = None
    match_types: list[str] | None = None
    daily_budget: float
    bidding_strategy: str | None = None
    default_bid: float | None = None
    keywords: list[dict] | None = None
    negative_keywords: list[str] | None = None
    schedule_start: str | None = None
    schedule_end: str | None = None
