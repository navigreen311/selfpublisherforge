/**
 * Type definitions for the Advertising Intelligence module.
 */

export interface Campaign {
  id: string;
  org_id: string;
  name: string;
  platform: "amazon" | "facebook";
  campaign_type: string;
  status: "draft" | "active" | "paused" | "ended" | "archived";
  book_id?: string;
  daily_budget: number;
  total_budget?: number;
  bid_strategy: string;
  target_acos?: number;
  start_date?: string;
  end_date?: string;
  targeting_keywords: string[];
  negative_keywords: string[];
  external_campaign_id?: string;
  created_at: string;
  updated_at: string;
  performance_summary?: PerformanceSummary;
}

export interface PerformanceSummary {
  total_impressions: number;
  total_clicks: number;
  total_spend: number;
  total_sales: number;
  total_orders: number;
  avg_acos: number;
  avg_roas: number;
  avg_ctr: number;
  avg_cpc: number;
  avg_conversion_rate: number;
  period_start?: string;
  period_end?: string;
}

export interface AdPerformance {
  id: string;
  campaign_id: string;
  date: string;
  impressions: number;
  clicks: number;
  spend: number;
  sales: number;
  orders: number;
  acos: number;
  roas: number;
  ctr: number;
  cpc: number;
  conversion_rate: number;
}

export interface KeywordBid {
  id: string;
  campaign_id: string;
  keyword: string;
  match_type: "exact" | "phrase" | "broad";
  bid_amount: number;
  is_negative: boolean;
  is_active: boolean;
  impressions: number;
  clicks: number;
  spend: number;
  sales: number;
  acos: number;
  created_at: string;
  updated_at: string;
}

export interface AdCreative {
  id: string;
  org_id: string;
  campaign_id?: string;
  book_id?: string;
  headline: string;
  body_text: string;
  call_to_action: string;
  image_url?: string;
  status: string;
  impressions: number;
  clicks: number;
  ctr: number;
  conversions: number;
  created_at: string;
  updated_at: string;
}

export interface OptimizationSuggestion {
  campaign_id: string;
  campaign_name: string;
  current_acos: number;
  target_acos: number;
  bid_adjustments: Array<{
    keyword_bid_id: string;
    keyword: string;
    current_bid: number;
    suggested_bid: number;
    reason: string;
    expected_acos_impact: number;
  }>;
  keywords_to_add: string[];
  keywords_to_negate: string[];
  budget_recommendation?: number;
  summary: string;
}

export interface AdDashboard {
  total_active_campaigns: number;
  total_spend_today: number;
  total_spend_month: number;
  total_sales_month: number;
  overall_acos: number;
  overall_roas: number;
  top_campaigns: Campaign[];
  platform_breakdown: Record<string, PerformanceSummary>;
  recent_optimizations: string[];
}

export interface GeneratedCreative {
  headline: string;
  body_text: string;
  call_to_action: string;
  reasoning: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor?: string;
  has_more: boolean;
  total_count?: number;
}

// --- New types for enhanced features ---

export interface AdSearchTerm {
  id: string;
  campaign_id: string;
  search_term: string;
  impressions: number;
  clicks: number;
  spend: number;
  sales: number;
  orders: number;
  action_taken?: string;
  recorded_at: string;
}

export interface AdDailyMetric {
  date: string;
  spend: number;
  sales: number;
  impressions: number;
  clicks: number;
  orders: number;
}

export interface AIInsight {
  type: "budget" | "keyword" | "performance" | "warning" | "opportunity";
  message: string;
  campaign_id?: string;
  action?: string;
  severity: "info" | "warning" | "success";
}

export interface KeywordSuggestion {
  keyword: string;
  search_volume: number;
  suggested_bid: number;
  competition: "low" | "medium" | "high";
}

export interface BidRecommendation {
  keyword: string;
  current_bid: number;
  suggested_bid: number;
  reason: string;
  expected_acos_impact: number;
}

export interface BidOptimizationRequest {
  target_acos: number;
  strategy: "maximize_sales" | "minimize_acos" | "maximize_impressions";
}

export interface BidOptimizationResponse {
  recommendations: BidRecommendation[];
  estimated_impact: {
    current_acos: number;
    projected_acos: number;
    projected_sales_change: string;
  };
}

export interface EnhancedDashboard {
  stats: {
    active_campaigns: number;
    total_spend_today: number;
    total_spend_period: number;
    total_sales_period: number;
    overall_acos: number;
    overall_roas: number;
    total_impressions: number;
    total_clicks: number;
  };
  trend_data: AdDailyMetric[];
  top_campaigns: Array<{
    campaign_id: string;
    name: string;
    spend: number;
    sales: number;
    acos: number;
    impressions: number;
    clicks: number;
    ctr: number;
  }>;
  insights: AIInsight[];
}

export interface CampaignCreatePayload {
  platform: "amazon" | "facebook" | "bookbub";
  ad_type: string;
  book_id?: string;
  name: string;
  targeting_type?: "automatic" | "manual" | "asin";
  match_types?: string[];
  daily_budget: number;
  bidding_strategy?: string;
  default_bid?: number;
  keywords?: Array<{ keyword: string; match_type: string; bid: number }>;
  negative_keywords?: string[];
  schedule_start?: string;
  schedule_end?: string;
}
