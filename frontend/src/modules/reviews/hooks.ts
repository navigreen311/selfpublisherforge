"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Review,
  SentimentBreakdown,
  VelocityReport,
  ReviewAlert,
  ReputationHealthMetrics,
  PaginatedResponse,
  ReviewListParams,
  AlertListParams,
  VelocityPeriod,
  SentimentLabel,
  ReviewStats,
  SentimentTrendResponse,
  ReviewInsightsResponse,
  BackMatterOptimizeResponse,
  ARCCampaign,
  EmailSequenceResponse,
  BookReviewSummary,
  AlertNotification,
  CreateReviewAlertRequest,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/reviews";

// ---------- Query Keys ----------

export const reviewKeys = {
  all: ["reviews"] as const,
  list: (params?: ReviewListParams) => [...reviewKeys.all, "list", params] as const,
  book: (bookId: string, params?: ReviewListParams) =>
    [...reviewKeys.all, "book", bookId, params] as const,
  sentiment: (bookId: string) => [...reviewKeys.all, "sentiment", bookId] as const,
  velocity: (bookId: string, period?: VelocityPeriod, lookback?: number) =>
    [...reviewKeys.all, "velocity", bookId, period, lookback] as const,
  alerts: (params?: AlertListParams) => [...reviewKeys.all, "alerts", params] as const,
  reputation: (bookId: string) => [...reviewKeys.all, "reputation", bookId] as const,
  stats: (bookId?: string) => [...reviewKeys.all, "stats", bookId] as const,
  sentimentTrend: (bookId?: string, period?: string) =>
    [...reviewKeys.all, "sentiment-trend", bookId, period] as const,
  insights: (bookId?: string) => [...reviewKeys.all, "insights", bookId] as const,
  bookSummaries: () => [...reviewKeys.all, "book-summaries"] as const,
  arcCampaigns: () => [...reviewKeys.all, "arc-campaigns"] as const,
  alertNotifications: () => [...reviewKeys.all, "alert-notifications"] as const,
};

// ---------- Existing Hooks ----------

export function useReviews(params?: ReviewListParams) {
  return useQuery<PaginatedResponse<Review>>({
    queryKey: reviewKeys.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.cursor) searchParams.set("cursor", params.cursor);
      if (params?.limit) searchParams.set("limit", params.limit.toString());
      if (params?.sentiment) searchParams.set("sentiment", params.sentiment);
      if (params?.min_rating !== undefined)
        searchParams.set("min_rating", params.min_rating.toString());
      if (params?.max_rating !== undefined)
        searchParams.set("max_rating", params.max_rating.toString());
      if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
      if (params?.sort_dir) searchParams.set("sort_dir", params.sort_dir);
      if (params?.book_id) searchParams.set("book_id", params.book_id);

      const { data } = await api.get(`${API_PREFIX}?${searchParams}`);
      return data;
    },
  });
}

export function useBookReviews(bookId: string, params?: ReviewListParams) {
  return useQuery<PaginatedResponse<Review>>({
    queryKey: reviewKeys.book(bookId, params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.cursor) searchParams.set("cursor", params.cursor);
      if (params?.limit) searchParams.set("limit", params.limit.toString());
      if (params?.sentiment) searchParams.set("sentiment", params.sentiment);
      if (params?.min_rating !== undefined)
        searchParams.set("min_rating", params.min_rating.toString());
      if (params?.max_rating !== undefined)
        searchParams.set("max_rating", params.max_rating.toString());
      if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
      if (params?.sort_dir) searchParams.set("sort_dir", params.sort_dir);

      const { data } = await api.get(`${API_PREFIX}/book/${bookId}?${searchParams}`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useSentimentBreakdown(bookId: string) {
  return useQuery<SentimentBreakdown>({
    queryKey: reviewKeys.sentiment(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/sentiment/${bookId}`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useVelocity(
  bookId: string,
  period?: VelocityPeriod,
  lookback?: number
) {
  return useQuery<VelocityReport>({
    queryKey: reviewKeys.velocity(bookId, period, lookback),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (period) searchParams.set("period", period);
      if (lookback) searchParams.set("lookback", lookback.toString());

      const { data } = await api.get(`${API_PREFIX}/velocity/${bookId}?${searchParams}`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useAlerts(params?: AlertListParams) {
  return useQuery<PaginatedResponse<ReviewAlert>>({
    queryKey: reviewKeys.alerts(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.cursor) searchParams.set("cursor", params.cursor);
      if (params?.limit) searchParams.set("limit", params.limit.toString());
      if (params?.alert_type) searchParams.set("alert_type", params.alert_type);
      if (params?.severity) searchParams.set("severity", params.severity);
      if (params?.is_acknowledged !== undefined)
        searchParams.set("is_acknowledged", params.is_acknowledged.toString());
      if (params?.book_id) searchParams.set("book_id", params.book_id);

      const { data } = await api.get(`${API_PREFIX}/alerts?${searchParams}`);
      return data;
    },
  });
}

export function useReputation(bookId: string) {
  return useQuery<ReputationHealthMetrics>({
    queryKey: reviewKeys.reputation(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/reputation/${bookId}`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation<ReviewAlert, Error, { alertId: string; notes?: string }>({
    mutationFn: async ({ alertId, notes }) => {
      const { data } = await api.patch(`${API_PREFIX}/alerts/${alertId}/acknowledge`, {
        notes,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

export function useAnalyzeReviews() {
  const queryClient = useQueryClient();
  return useMutation<
    {
      total_analyzed: number;
      sentiment_breakdown: SentimentBreakdown;
      top_themes: Array<{ theme: string; count: number; sentiment: SentimentLabel }>;
      top_complaints: string[];
      top_praise: string[];
      actionable_insights: string[];
    },
    Error,
    { review_ids?: string[]; book_id?: string; limit?: number }
  >({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/analyze`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

// ---------- New Hooks ----------

export function useReviewStats(bookId?: string) {
  return useQuery<ReviewStats>({
    queryKey: reviewKeys.stats(bookId),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (bookId) params.book_id = bookId;
      const { data } = await api.get(`${API_PREFIX}/stats`, { params });
      return data;
    },
  });
}

export function useSentimentTrend(bookId?: string, period = "6m") {
  return useQuery<SentimentTrendResponse>({
    queryKey: reviewKeys.sentimentTrend(bookId, period),
    queryFn: async () => {
      const params: Record<string, string> = { period };
      if (bookId) params.book_id = bookId;
      const { data } = await api.get(`${API_PREFIX}/sentiment-trend`, { params });
      return data;
    },
  });
}

export function useReviewInsights(bookId?: string) {
  return useQuery<ReviewInsightsResponse>({
    queryKey: reviewKeys.insights(bookId),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (bookId) params.book_id = bookId;
      const { data } = await api.get(`${API_PREFIX}/insights`, { params });
      return data;
    },
  });
}

export function useRefreshInsights() {
  const queryClient = useQueryClient();
  return useMutation<{ job_id: string }, Error, { book_ids?: string[] }>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/analyze`, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.insights() });
    },
  });
}

export function useBookReviewSummaries() {
  return useQuery<BookReviewSummary[]>({
    queryKey: reviewKeys.bookSummaries(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/book-summaries`);
      return data;
    },
  });
}

export function useOptimizeBackMatter() {
  return useMutation<BackMatterOptimizeResponse, Error, { current_text: string; book_id?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/optimize-back-matter`, body);
      return data;
    },
  });
}

export function useARCCampaigns() {
  return useQuery<ARCCampaign[]>({
    queryKey: reviewKeys.arcCampaigns(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/arc-campaigns`);
      return data;
    },
  });
}

export function useCreateARCCampaign() {
  const queryClient = useQueryClient();
  return useMutation<ARCCampaign, Error, { book_id: string; name: string; deadline?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/arc-campaigns`, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.arcCampaigns() });
    },
  });
}

export function useSendARCReminder() {
  return useMutation<void, Error, string>({
    mutationFn: async (campaignId) => {
      await api.post(`${API_PREFIX}/arc-campaigns/${campaignId}/send-reminder`);
    },
  });
}

export function useGenerateEmailSequence() {
  return useMutation<EmailSequenceResponse, Error, { book_id: string; timing?: number[] }>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/email-sequences/generate`, body);
      return data;
    },
  });
}

export function useMarkReviewRead() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { reviewId: string; read: boolean }>({
    mutationFn: async ({ reviewId, read }) => {
      await api.patch(`${API_PREFIX}/${reviewId}`, { read });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

export function useFlagReview() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { reviewId: string; flagged: boolean; notes?: string }>({
    mutationFn: async ({ reviewId, flagged, notes }) => {
      await api.patch(`${API_PREFIX}/${reviewId}`, { flagged, flag_notes: notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

export function useAlertNotifications() {
  return useQuery<AlertNotification[]>({
    queryKey: reviewKeys.alertNotifications(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/alerts/history`);
      return data;
    },
  });
}

export function useCreateReviewAlert() {
  const queryClient = useQueryClient();
  return useMutation<ReviewAlert, Error, CreateReviewAlertRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/alerts`, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.alerts() });
    },
  });
}

export function useUpdateReviewAlert() {
  const queryClient = useQueryClient();
  return useMutation<ReviewAlert, Error, { id: string; updates: Partial<CreateReviewAlertRequest & { active: boolean }> }>({
    mutationFn: async ({ id, updates }) => {
      const { data } = await api.patch(`${API_PREFIX}/alerts/${id}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.alerts() });
    },
  });
}

export function useDeleteReviewAlert() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/alerts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.alerts() });
    },
  });
}
