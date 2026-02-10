"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

const API_PREFIX = "/api/v1/analytics";

// ---------- Types ----------

export interface KPICard {
  label: string;
  value: string;
  change_percent: number | null;
  change_direction: string | null;
  period: string;
}

export interface RevenueDataPoint {
  period: string;
  revenue: number;
  units: number;
  platform?: string;
  book_title?: string;
}

export interface RoyaltyRecord {
  id: string;
  org_id: string;
  book_id: string | null;
  platform: string;
  marketplace: string;
  title: string;
  asin: string | null;
  isbn: string | null;
  format_type: string;
  units_sold: number;
  units_refunded: number;
  net_units: number;
  list_price: number;
  royalty_rate: number;
  gross_revenue: number;
  net_revenue: number;
  currency: string;
  period_start: string;
  period_end: string;
  import_batch_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  kpis: KPICard[];
  revenue_chart: RevenueDataPoint[];
  top_books: Record<string, unknown>[];
  platform_breakdown: Record<string, number>;
  recent_royalties: RoyaltyRecord[];
  period_start: string;
  period_end: string;
}

export interface RevenueResponse {
  total_revenue: number;
  total_units: number;
  data_points: RevenueDataPoint[];
  period_start: string;
  period_end: string;
  aggregation: string;
  by_platform: Record<string, number>;
  by_book: Record<string, unknown>[];
}

export interface PortfolioMetrics {
  total_books: number;
  total_revenue: number;
  total_units_sold: number;
  total_expenses: number;
  net_profit: number;
  avg_roi: number;
  platform_breakdown: Record<string, unknown>;
  format_breakdown: Record<string, unknown>;
  top_books: Record<string, unknown>[];
  snapshot_date: string | null;
}

export interface ReportResponse {
  id: string;
  org_id: string;
  title: string;
  report_type: string;
  status: string;
  output_format: string;
  parameters: Record<string, unknown>;
  file_path: string | null;
  file_size: number | null;
  generated_by: string | null;
  generated_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrendData {
  metric: string;
  data_points: { period: string; value: number; label?: string }[];
  aggregation: string;
  period_start: string;
  period_end: string;
  total: number;
  average: number;
  change_percent: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface RoyaltyImportResponse {
  import_batch_id: string;
  records_imported: number;
  records_skipped: number;
  errors: string[];
  platform: string;
}

export interface ReportRequest {
  title: string;
  report_type: "revenue_summary" | "book_performance" | "marketing_roi" | "portfolio_overview" | "custom";
  output_format: "pdf" | "xlsx";
  parameters: Record<string, unknown>;
}

export interface RoyaltyImportRequest {
  platform: "kdp" | "ingram_spark" | "draft2digital" | "other";
  file_content: string;
  file_name?: string;
}

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
