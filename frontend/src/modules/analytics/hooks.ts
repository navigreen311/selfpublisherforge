"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  KPICard,
  RevenueDataPoint,
  RoyaltyRecord,
  DashboardData,
  RevenueResponse,
  PortfolioMetrics,
  ReportResponse,
  TrendData,
  PaginatedResponse,
  RoyaltyImportResponse,
  ReportRequest,
  RoyaltyImportRequest,
  BookSummary,
  PortfolioOverview,
  GreenlightRequest,
  GreenlightResult,
  AudiencePersona,
  AlsoBoughtIntelligence,
  SeasonalEvent,
  NicheSeasonality,
  EnhancedDashboardData,
  SalesResponse,
  BookPerformanceData,
  EnhancedReportRequest,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/analytics";

// ---------- Query Keys ----------

export const analyticsKeys = {
  all: ["analytics"] as const,
  dashboard: (startDate?: string, endDate?: string) =>
    [...analyticsKeys.all, "dashboard", startDate, endDate] as const,
  revenue: (params?: Record<string, unknown>) =>
    [...analyticsKeys.all, "revenue", params] as const,
  royalties: (cursor?: string, platform?: string) =>
    [...analyticsKeys.all, "royalties", cursor, platform] as const,
  portfolio: () => [...analyticsKeys.all, "portfolio"] as const,
  reports: (cursor?: string) =>
    [...analyticsKeys.all, "reports", cursor] as const,
  trends: (metric?: string, params?: Record<string, unknown>) =>
    [...analyticsKeys.all, "trends", metric, params] as const,
};

// ---------- Hooks ----------

export function useDashboard(startDate?: string, endDate?: string) {
  return useQuery<DashboardData>({
    queryKey: analyticsKeys.dashboard(startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      const { data } = await api.get(`${API_PREFIX}/dashboard?${params}`);
      return data;
    },
  });
}

export function useRevenue(params?: {
  start_date?: string;
  end_date?: string;
  platform?: string;
  book_id?: string;
  aggregation?: string;
}) {
  return useQuery<RevenueResponse>({
    queryKey: analyticsKeys.revenue(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set("start_date", params.start_date);
      if (params?.end_date) searchParams.set("end_date", params.end_date);
      if (params?.platform) searchParams.set("platform", params.platform);
      if (params?.book_id) searchParams.set("book_id", params.book_id);
      if (params?.aggregation) searchParams.set("aggregation", params.aggregation);
      const { data } = await api.get(`${API_PREFIX}/revenue?${searchParams}`);
      return data;
    },
  });
}

export function useRoyalties(cursor?: string, platform?: string) {
  return useQuery<PaginatedResponse<RoyaltyRecord>>({
    queryKey: analyticsKeys.royalties(cursor, platform),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (cursor) params.set("cursor", cursor);
      if (platform) params.set("platform", platform);
      const { data } = await api.get(`${API_PREFIX}/royalties?${params}`);
      return data;
    },
  });
}

export function usePortfolioMetrics() {
  return useQuery<PortfolioMetrics>({
    queryKey: analyticsKeys.portfolio(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/portfolio`);
      return data;
    },
  });
}

export function useReports(cursor?: string) {
  return useQuery<PaginatedResponse<ReportResponse>>({
    queryKey: analyticsKeys.reports(cursor),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (cursor) params.set("cursor", cursor);
      const { data } = await api.get(`${API_PREFIX}/reports?${params}`);
      return data;
    },
  });
}

export function useTrends(
  metric?: string,
  params?: { start_date?: string; end_date?: string; aggregation?: string }
) {
  return useQuery<TrendData>({
    queryKey: analyticsKeys.trends(metric, params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (metric) searchParams.set("metric", metric);
      if (params?.start_date) searchParams.set("start_date", params.start_date);
      if (params?.end_date) searchParams.set("end_date", params.end_date);
      if (params?.aggregation) searchParams.set("aggregation", params.aggregation);
      const { data } = await api.get(`${API_PREFIX}/trends?${searchParams}`);
      return data;
    },
  });
}

export function useImportRoyalties() {
  const queryClient = useQueryClient();
  return useMutation<RoyaltyImportResponse, Error, RoyaltyImportRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/royalties/import`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: analyticsKeys.all });
    },
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation<ReportResponse, Error, ReportRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/reports/generate`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: analyticsKeys.reports() });
    },
  });
}

export function useDownloadReport() {
  return useMutation<Blob, Error, string>({
    mutationFn: async (reportId) => {
      const { data } = await api.get(`${API_PREFIX}/reports/${reportId}/download`, {
        responseType: "blob",
      });
      return data;
    },
  });
}

export function useRecordEvent() {
  return useMutation<unknown, Error, { event_type: string; event_source?: string; data?: Record<string, unknown> }>({
    mutationFn: async (event) => {
      const { data } = await api.post(`${API_PREFIX}/events`, event);
      return data;
    },
  });
}

// ---------- Query Keys ----------

export const portfolioKeys = {
  all: ["portfolio"] as const,
  overview: () => [...portfolioKeys.all, "overview"] as const,
  backlist: (params?: Record<string, unknown>) =>
    [...portfolioKeys.all, "backlist", params] as const,
};

export const audienceKeys = {
  all: ["audience"] as const,
  personas: (bookId: string, genre?: string) =>
    [...audienceKeys.all, "personas", bookId, genre] as const,
  alsoBought: (bookId: string) =>
    [...audienceKeys.all, "also-bought", bookId] as const,
};

export const seasonalKeys = {
  all: ["seasonal"] as const,
  calendar: (year?: number, genres?: string[]) =>
    [...seasonalKeys.all, "calendar", year, genres] as const,
  niche: (genre: string, year?: number) =>
    [...seasonalKeys.all, "niche", genre, year] as const,
};

// ---------- Portfolio Economics Hooks ----------

export function usePortfolioOverview() {
  return useQuery<PortfolioOverview>({
    queryKey: portfolioKeys.overview(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/portfolio");
      return data.data;
    },
  });
}

export function useGreenlightMutation() {
  return useMutation<GreenlightResult, Error, GreenlightRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post("/api/v1/portfolio/greenlight", request);
      return data.data;
    },
  });
}

export function useAudiencePersonas(bookId: string, genre: string = "romance") {
  return useQuery<AudiencePersona[]>({
    queryKey: audienceKeys.personas(bookId, genre),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/audience/personas/${bookId}?genre=${genre}`);
      return data.data;
    },
  });
}

export function useAlsoBought(bookId: string, genre: string = "romance") {
  return useQuery<AlsoBoughtIntelligence>({
    queryKey: audienceKeys.alsoBought(bookId),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/audience/also-bought/${bookId}?genre=${genre}`);
      return data.data;
    },
  });
}

export function useSeasonalCalendar(year?: number, genres?: string[]) {
  return useQuery<{ events: SeasonalEvent[]; genre_seasonality: Record<string, NicheSeasonality> }>({
    queryKey: seasonalKeys.calendar(year, genres),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (year) params.set("year", year.toString());
      if (genres?.length) params.set("genres", genres.join(","));
      const { data } = await api.get(`/api/v1/seasonal/calendar?${params}`);
      return data.data;
    },
  });
}

export function useNicheSeasonality(genre: string, year?: number) {
  return useQuery<NicheSeasonality>({
    queryKey: seasonalKeys.niche(genre, year),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (year) params.set("year", year.toString());
      const { data } = await api.get(`/api/v1/seasonal/niche/${genre}?${params}`);
      return data.data;
    },
  });
}

// ---------- Enhanced Analytics Hooks ----------

export function useEnhancedDashboard(period: string = "30d", compare: string = "previous") {
  return useQuery({
    queryKey: ["analytics", "dashboard", "enhanced", period, compare],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/analytics/dashboard/enhanced", { params: { period, compare } });
      return data.data as EnhancedDashboardData;
    },
  });
}

export function useSalesData(params?: { period?: string; book_id?: string; marketplace?: string }) {
  return useQuery({
    queryKey: ["analytics", "sales", params],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/analytics/sales", { params });
      return data.data as SalesResponse;
    },
  });
}

export function useBookPerformance(bookId: string, period: string = "90d") {
  return useQuery({
    queryKey: ["analytics", "books", bookId, "performance", period],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/analytics/books/${bookId}/performance`, { params: { period } });
      return data.data as BookPerformanceData;
    },
    enabled: !!bookId,
  });
}

export function useGenerateEnhancedReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: EnhancedReportRequest) => {
      const { data } = await api.post("/api/v1/analytics/reports/generate", request);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics", "reports"] });
      toast.success("Report generation started");
    },
    onError: (error: any) => {
      toast.error(extractApiError(error));
    },
  });
}
