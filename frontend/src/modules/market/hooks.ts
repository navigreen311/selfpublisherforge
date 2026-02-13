"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CategoryNode,
  CategoryAnalysis,
  KeywordData,
  KeywordResearchResponse,
  CompetitorSummary,
  BSRHistoryPoint,
  CompetitorDetail,
  CompetitorListItem,
  GapAnalysisItem,
  NicheAnalysisResponse,
  TrendDataPoint,
  MarketTrend,
  MarketTrendsResponse,
  MarketSnapshot,
} from "./types";

export type * from "./types";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

const KEYS = {
  categories: (rootId?: string) => ["market", "categories", rootId] as const,
  categoryAnalysis: (id: string) => ["market", "category-analysis", id] as const,
  keywordResearch: ["market", "keyword-research"] as const,
  keywordSuggestions: (genre: string) => ["market", "keyword-suggestions", genre] as const,
  nicheAnalysis: ["market", "niche-analysis"] as const,
  competitors: ["market", "competitors"] as const,
  competitor: (id: string) => ["market", "competitor", id] as const,
  trends: (catId?: string, kw?: string) => ["market", "trends", catId, kw] as const,
  snapshots: (catId?: string) => ["market", "snapshots", catId] as const,
};

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useCategories(rootId?: string) {
  return useQuery<CategoryNode[]>({
    queryKey: KEYS.categories(rootId),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (rootId) params.root_id = rootId;
      const { data } = await api.get("/api/v1/market/categories", { params });
      return data;
    },
  });
}

export function useCategoryAnalysis(categoryId: string) {
  return useQuery<CategoryAnalysis>({
    queryKey: KEYS.categoryAnalysis(categoryId),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/market/categories/${categoryId}/analysis`);
      return data;
    },
    enabled: !!categoryId,
  });
}

export function useKeywordResearch() {
  return useMutation<KeywordResearchResponse, Error, { keywords: string[]; marketplace?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post("/api/v1/market/keywords/research", body);
      return data;
    },
  });
}

export function useKeywordSuggestions(genre: string, niche?: string, limit = 20) {
  return useQuery<KeywordData[]>({
    queryKey: KEYS.keywordSuggestions(genre),
    queryFn: async () => {
      const params: Record<string, string | number> = { genre, limit };
      if (niche) params.niche = niche;
      const { data } = await api.get("/api/v1/market/keywords/suggestions", { params });
      return data;
    },
    enabled: !!genre,
  });
}

export function useNicheAnalysis() {
  return useMutation<NicheAnalysisResponse, Error, { niche: string; category_id?: string; marketplace?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post("/api/v1/market/analyze-niche", body);
      return data;
    },
  });
}

export function useCompetitors(marketplace = "US") {
  return useQuery<CompetitorListItem[]>({
    queryKey: KEYS.competitors,
    queryFn: async () => {
      const { data } = await api.get("/api/v1/market/competitors", { params: { marketplace } });
      return data;
    },
  });
}

export function useTrackCompetitor() {
  const qc = useQueryClient();
  return useMutation<CompetitorDetail, Error, { asin: string; marketplace?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post("/api/v1/market/competitors/track", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.competitors });
    },
  });
}

export function useCompetitorDetail(competitorId: string) {
  return useQuery<CompetitorDetail>({
    queryKey: KEYS.competitor(competitorId),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/market/competitors/${competitorId}`);
      return data;
    },
    enabled: !!competitorId,
  });
}

export function useMarketTrends(categoryId?: string, keyword?: string, days = 30) {
  return useQuery<MarketTrendsResponse>({
    queryKey: KEYS.trends(categoryId, keyword),
    queryFn: async () => {
      const params: Record<string, string | number> = { days };
      if (categoryId) params.category_id = categoryId;
      if (keyword) params.keyword = keyword;
      const { data } = await api.get("/api/v1/market/trends", { params });
      return data;
    },
  });
}

export function useMarketSnapshots(categoryId?: string, limit = 30) {
  return useQuery<MarketSnapshot[]>({
    queryKey: KEYS.snapshots(categoryId),
    queryFn: async () => {
      const params: Record<string, string | number> = { limit };
      if (categoryId) params.category_id = categoryId;
      const { data } = await api.get("/api/v1/market/snapshots", { params });
      return data;
    },
  });
}
