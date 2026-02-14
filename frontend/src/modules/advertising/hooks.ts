/**
 * React Query hooks for Advertising Intelligence module.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  Campaign,
  AdPerformance,
  OptimizationSuggestion,
  KeywordBid,
  AdCreative,
  GeneratedCreative,
  AdDashboard,
  PaginatedResponse,
  EnhancedDashboard,
  AIInsight,
  KeywordSuggestion,
  BidOptimizationRequest,
  BidOptimizationResponse,
  AdSearchTerm,
  AdDailyMetric,
} from "./types";

export type * from "./types";

const QUERY_KEYS = {
  campaigns: ["ads", "campaigns"] as const,
  campaign: (id: string) => ["ads", "campaigns", id] as const,
  campaignPerformance: (id: string) => ["ads", "campaigns", id, "performance"] as const,
  keywordBids: (campaignId?: string) => ["ads", "keyword-bids", campaignId] as const,
  creatives: (campaignId?: string) => ["ads", "creatives", campaignId] as const,
  dashboard: ["ads", "dashboard"] as const,
};

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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
      book_id?: string;
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
    onError: (error) => {
      toast.error(extractApiError(error));
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

// ─── Enhanced Dashboard & AI Hooks ──────────────────────────────────────────

export function useEnhancedDashboard(period: string = "30d") {
  return useQuery({
    queryKey: ["advertising", "dashboard", "enhanced", period],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ads/dashboard/enhanced", { params: { period } });
      return data.data as EnhancedDashboard;
    },
  });
}

export function useAIInsights() {
  return useQuery({
    queryKey: ["advertising", "ai", "insights"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/ads/ai/insights");
      return data.data as AIInsight[];
    },
  });
}

export function useSuggestKeywords() {
  return useMutation({
    mutationFn: async (bookId: string) => {
      const { data } = await api.post("/api/v1/ads/ai/suggest-keywords", { book_id: bookId });
      return data.data as KeywordSuggestion[];
    },
    onError: (error: any) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useOptimizeBids(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: BidOptimizationRequest) => {
      const { data } = await api.post(`/api/v1/ads/campaigns/${campaignId}/optimize-bids`, request);
      return data.data as BidOptimizationResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advertising"] });
    },
    onError: (error: any) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Search Terms Hooks ─────────────────────────────────────────────────────

export function useSearchTerms(campaignId: string) {
  return useQuery({
    queryKey: ["advertising", "campaigns", campaignId, "search-terms"],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/ads/campaigns/${campaignId}/search-terms`);
      return data.data as AdSearchTerm[];
    },
    enabled: !!campaignId,
  });
}

export function useAddSearchTermAsKeyword(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (searchTermId: string) => {
      const { data } = await api.post(`/api/v1/ads/campaigns/${campaignId}/search-terms/${searchTermId}/add-as-keyword`);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advertising", "campaigns", campaignId] });
      toast.success("Keyword added from search term");
    },
    onError: (error: any) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useNegateSearchTerm(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (searchTermId: string) => {
      const { data } = await api.post(`/api/v1/ads/campaigns/${campaignId}/search-terms/${searchTermId}/negate`);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advertising", "campaigns", campaignId] });
      toast.success("Search term negated");
    },
    onError: (error: any) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Campaign Daily Metrics & Controls ──────────────────────────────────────

export function useCampaignDailyMetrics(campaignId: string, period: string = "30d") {
  return useQuery({
    queryKey: ["advertising", "campaigns", campaignId, "daily-metrics", period],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/ads/campaigns/${campaignId}/daily-metrics`, { params: { period } });
      return data.data as AdDailyMetric[];
    },
    enabled: !!campaignId,
  });
}

export function usePauseCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (campaignId: string) => {
      const { data } = await api.post(`/api/v1/ads/campaigns/${campaignId}/pause`);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advertising"] });
      toast.success("Campaign paused");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

export function useResumeCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (campaignId: string) => {
      const { data } = await api.post(`/api/v1/ads/campaigns/${campaignId}/resume`);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advertising"] });
      toast.success("Campaign resumed");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}
