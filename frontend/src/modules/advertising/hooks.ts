/**
 * React Query hooks for Advertising Intelligence module.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

const QUERY_KEYS = {
  campaigns: ["ads", "campaigns"] as const,
  campaign: (id: string) => ["ads", "campaigns", id] as const,
  campaignPerformance: (id: string) => ["ads", "campaigns", id, "performance"] as const,
  keywordBids: (campaignId?: string) => ["ads", "keyword-bids", campaignId] as const,
  creatives: (campaignId?: string) => ["ads", "creatives", campaignId] as const,
  dashboard: ["ads", "dashboard"] as const,
};

// ─── Types ───────────────────────────────────────────────────────────────────

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

// ─── Campaign Hooks ──────────────────────────────────────────────────────────

export function useCampaigns(params?: {
  platform?: string;
  status?: string;
  cursor?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.campaigns, params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Campaign>>(
        "/api/v1/ads/campaigns",
        { params }
      );
      return data;
    },
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.campaign(id),
    queryFn: async () => {
      const { data } = await api.get<Campaign>(`/api/v1/ads/campaigns/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (campaignData: {
      name: string;
      platform: string;
      campaign_type: string;
      daily_budget: number;
      bid_strategy?: string;
      target_acos?: number;
      targeting_keywords?: string[];
      negative_keywords?: string[];
    }) => {
      const { data } = await api.post<Campaign>(
        "/api/v1/ads/campaigns",
        campaignData
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.campaigns });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
    },
  });
}

export function useUpdateCampaign(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (updates: Partial<Campaign>) => {
      const { data } = await api.patch<Campaign>(
        `/api/v1/ads/campaigns/${id}`,
        updates
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.campaign(id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.campaigns });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
    },
  });
}

// ─── Performance Hooks ───────────────────────────────────────────────────────

export function useCampaignPerformance(
  campaignId: string,
  params?: { date_from?: string; date_to?: string; granularity?: string }
) {
  return useQuery({
    queryKey: [...QUERY_KEYS.campaignPerformance(campaignId), params],
    queryFn: async () => {
      const { data } = await api.get<AdPerformance[]>(
        `/api/v1/ads/campaigns/${campaignId}/performance`,
        { params }
      );
      return data;
    },
    enabled: !!campaignId,
  });
}

// ─── Optimization Hooks ─────────────────────────────────────────────────────

export function useOptimizeCampaign(campaignId: string) {
  return useMutation({
    mutationFn: async (params?: {
      target_acos?: number;
      max_bid_increase_pct?: number;
      max_bid_decrease_pct?: number;
      min_data_points?: number;
    }) => {
      const { data } = await api.post<OptimizationSuggestion>(
        `/api/v1/ads/campaigns/${campaignId}/optimize`,
        params || {}
      );
      return data;
    },
  });
}

// ─── Keyword Bid Hooks ──────────────────────────────────────────────────────

export function useKeywordBids(campaignId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.keywordBids(campaignId),
    queryFn: async () => {
      const params = campaignId ? { campaign_id: campaignId } : {};
      const { data } = await api.get<KeywordBid[]>(
        "/api/v1/ads/keyword-bids",
        { params }
      );
      return data;
    },
  });
}

export function useUpdateKeywordBids() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (updates: Array<{ id: string; bid_amount: number }>) => {
      const { data } = await api.patch<KeywordBid[]>(
        "/api/v1/ads/keyword-bids",
        { updates }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ads", "keyword-bids"] });
    },
  });
}

// ─── Creative Hooks ─────────────────────────────────────────────────────────

export function useCreatives(campaignId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.creatives(campaignId),
    queryFn: async () => {
      const params = campaignId ? { campaign_id: campaignId } : {};
      const { data } = await api.get<AdCreative[]>(
        "/api/v1/ads/creatives",
        { params }
      );
      return data;
    },
  });
}

export function useGenerateCreatives() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: {
      book_title: string;
      book_description: string;
      genre?: string;
      target_audience?: string;
      tone?: string;
      num_variations?: number;
      platform?: string;
    }) => {
      const { data } = await api.post<{
        variations: GeneratedCreative[];
        platform: string;
        book_title: string;
      }>("/api/v1/ads/creatives/generate", request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ads", "creatives"] });
    },
  });
}

// ─── Dashboard Hook ─────────────────────────────────────────────────────────

export function useAdDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard,
    queryFn: async () => {
      const { data } = await api.get<AdDashboard>("/api/v1/ads/dashboard");
      return data;
    },
  });
}
