"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types (mirror backend schemas)
// ---------------------------------------------------------------------------

export interface CategoryNode {
  id: string;
  name: string;
  parent_id: string | null;
  children: CategoryNode[];
  book_count: number | null;
}

export interface CategoryAnalysis {
  category_id: string;
  category_name: string;
  book_count: number;
  avg_bsr: number;
  median_bsr: number;
  avg_price: number;
  avg_reviews: number;
  avg_rating: number;
  competition_score: number;
  bsr_distribution: Record<string, number>;
  top_books: CompetitorSummary[];
}

export interface KeywordData {
  keyword: string;
  search_volume: number;
  competition: number;
  cpc: number;
  trend: "up" | "down" | "stable";
  trend_data: number[];
  relevance_score: number;
}

export interface KeywordResearchResponse {
  keywords: KeywordData[];
  marketplace: string;
  generated_at: string;
}

export interface CompetitorSummary {
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  image_url: string | null;
}

export interface BSRHistoryPoint {
  date: string;
  bsr: number;
  price: number | null;
}

export interface CompetitorDetail {
  id: string;
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  image_url: string | null;
  category: string | null;
  marketplace: string;
  bsr_history: BSRHistoryPoint[];
  tracked_since: string;
  last_updated: string | null;
}

export interface CompetitorListItem {
  id: string;
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  marketplace: string;
  tracked_since: string;
}

export interface GapAnalysisItem {
  area: string;
  description: string;
  opportunity_level: string;
}

export interface NicheAnalysisResponse {
  niche: string;
  demand_score: number;
  supply_score: number;
  opportunity_score: number;
  top_competitors: CompetitorSummary[];
  gap_analysis: GapAnalysisItem[];
  avg_monthly_revenue: number | null;
  avg_bsr: number | null;
  recommendation: string;
  analyzed_at: string;
}

export interface TrendDataPoint {
  date: string;
  value: number;
}

export interface MarketTrend {
  label: string;
  category_id: string | null;
  keyword: string | null;
  direction: "up" | "down" | "stable";
  data_points: TrendDataPoint[];
  change_pct: number;
}

export interface MarketTrendsResponse {
  trends: MarketTrend[];
  period_start: string;
  period_end: string;
}

export interface MarketSnapshot {
  id: string;
  category_id: string;
  category_name: string;
  snapshot_date: string;
  avg_bsr: number;
  avg_price: number;
  book_count: number;
  avg_reviews: number;
  competition_score: number;
}

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
