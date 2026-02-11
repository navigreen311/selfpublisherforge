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
} from "./types";

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
};

// ---------- Hooks ----------

/**
 * List all reviews for the organization with optional filters.
 */
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

      const { data } = await api.get(`${API_PREFIX}?${searchParams}`);
      return data;
    },
  });
}

/**
 * Get reviews for a specific book with sentiment analysis.
 */
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

/**
 * Get sentiment breakdown for a book.
 */
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

/**
 * Get review velocity over time for a book.
 */
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

/**
 * List review alerts with optional filters.
 */
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

/**
 * Get reputation score and health metrics for a book.
 */
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

/**
 * Acknowledge a review alert.
 */
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

/**
 * Batch analyze reviews to extract themes, complaints, and praise.
 */
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
