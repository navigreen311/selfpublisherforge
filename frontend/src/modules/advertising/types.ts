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
