"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CompetitorAnalysis,
  CompetitorAnalysisDetail,
  CompetitorBookBrief,
  WeaknessSignal,
  OpportunityBlueprint,
  GapAnalysis,
  CompetitorAlert,
  AlertEvent,
  CompetitorAnalyzeRequest,
  BatchAnalyzeRequest,
  BatchAnalyzeResponse,
  GapAnalysisRequest,
  AddCompetitorRequest,
  CreateAlertRequest,
  ComparisonResult,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/competitors";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const competitorKeys = {
  all: ["competitors"] as const,
  tracked: (params?: Record<string, string>) => [...competitorKeys.all, "tracked", params] as const,
  analyses: () => [...competitorKeys.all, "analyses"] as const,
  analysis: (id: string) => [...competitorKeys.all, "analysis", id] as const,
  weaknesses: (analysisId: string) => [...competitorKeys.all, "weaknesses", analysisId] as const,
  opportunity: (analysisId: string) => [...competitorKeys.all, "opportunity", analysisId] as const,
  gaps: (niche?: string) => [...competitorKeys.all, "gaps", niche] as const,
  gapJob: (jobId: string) => [...competitorKeys.all, "gap-job", jobId] as const,
  alerts: (includeDismissed?: boolean) => [...competitorKeys.all, "alerts", includeDismissed] as const,
  alertHistory: () => [...competitorKeys.all, "alert-history"] as const,
  bsrHistory: (id: string) => [...competitorKeys.all, "bsr-history", id] as const,
  reviews: (id: string) => [...competitorKeys.all, "reviews", id] as const,
  compare: () => [...competitorKeys.all, "compare"] as const,
};

// ---------------------------------------------------------------------------
// Hooks for tracked competitors
// ---------------------------------------------------------------------------

export function useTrackedCompetitors(params?: {
  project_id?: string;
  sort?: string;
  order?: string;
  page?: number;
  limit?: number;
}) {
  return useQuery<{ competitors: CompetitorBookBrief[]; total: number }>({
    queryKey: competitorKeys.tracked(params as Record<string, string>),
    queryFn: async () => {
      const { data } = await api.get(API_PREFIX, { params });
      return data;
    },
  });
}

export function useAddCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<CompetitorBookBrief, Error, AddCompetitorRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(API_PREFIX, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
    },
  });
}

export function useRemoveCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
    },
  });
}

export function useCompetitorBsrHistory(competitorId: string, period = "90d") {
  return useQuery<{ data: { date: string; bsr: number }[] }>({
    queryKey: competitorKeys.bsrHistory(competitorId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${competitorId}/bsr-history`, {
        params: { period },
      });
      return data;
    },
    enabled: !!competitorId,
  });
}

export function useCompetitorReviews(competitorId: string, params?: {
  sort?: string;
  sentiment?: string;
  page?: number;
}) {
  return useQuery<{ reviews: Record<string, unknown>[]; total: number }>({
    queryKey: competitorKeys.reviews(competitorId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${competitorId}/reviews`, { params });
      return data;
    },
    enabled: !!competitorId,
  });
}

// ---------------------------------------------------------------------------
// Hooks for competitor analyses
// ---------------------------------------------------------------------------

export function useCompetitorAnalyses() {
  return useQuery<CompetitorAnalysis[]>({
    queryKey: competitorKeys.analyses(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/analyses`);
      return data;
    },
  });
}

export function useCompetitorAnalysis(analysisId: string) {
  return useQuery<CompetitorAnalysisDetail>({
    queryKey: competitorKeys.analysis(analysisId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/analyses/${analysisId}`);
      return data;
    },
    enabled: !!analysisId,
  });
}

export function useAnalyzeCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<CompetitorAnalysis, Error, CompetitorAnalyzeRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/analyze`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.analyses() });
    },
  });
}

export function useBatchAnalyze() {
  const queryClient = useQueryClient();
  return useMutation<BatchAnalyzeResponse, Error, { request: BatchAnalyzeRequest; marketplace?: string }>({
    mutationFn: async ({ request, marketplace = "US" }) => {
      const { data } = await api.post(`${API_PREFIX}/batch-analyze`, request, {
        params: { marketplace },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.analyses() });
    },
  });
}

// ---------------------------------------------------------------------------
// Hooks for weaknesses and opportunities
// ---------------------------------------------------------------------------

export function useWeaknesses(analysisId: string) {
  return useQuery<WeaknessSignal[]>({
    queryKey: competitorKeys.weaknesses(analysisId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${analysisId}/weaknesses`);
      return data;
    },
    enabled: !!analysisId,
  });
}

export function useOpportunity(analysisId: string) {
  return useQuery<OpportunityBlueprint | null>({
    queryKey: competitorKeys.opportunity(analysisId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${analysisId}/opportunity`);
      return data;
    },
    enabled: !!analysisId,
  });
}

// ---------------------------------------------------------------------------
// Hooks for gap analysis
// ---------------------------------------------------------------------------

export function useGapAnalysis() {
  const queryClient = useQueryClient();
  return useMutation<GapAnalysis, Error, { request: GapAnalysisRequest; marketplace?: string }>({
    mutationFn: async ({ request, marketplace = "US" }) => {
      const { data } = await api.post(`${API_PREFIX}/gap-analysis`, request, {
        params: { marketplace },
      });
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.gaps(data.niche) });
    },
  });
}

export function useGapAnalysisStatus(jobId: string) {
  return useQuery<GapAnalysis>({
    queryKey: competitorKeys.gapJob(jobId),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/gap-analysis/${jobId}`);
      return data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 3000;
    },
  });
}

// ---------------------------------------------------------------------------
// Hooks for compare
// ---------------------------------------------------------------------------

export function useCompareBooks() {
  return useMutation<ComparisonResult, Error, { book_ids: string[]; my_project_id?: string }>({
    mutationFn: async (body) => {
      const { data } = await api.post(`${API_PREFIX}/compare`, body);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Hooks for alerts
// ---------------------------------------------------------------------------

export function useCompetitorAlerts(includeDismissed = false, limit = 50) {
  return useQuery<CompetitorAlert[]>({
    queryKey: competitorKeys.alerts(includeDismissed),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/alerts`, {
        params: { include_dismissed: includeDismissed, limit },
      });
      return data;
    },
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();
  return useMutation<CompetitorAlert, Error, CreateAlertRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/alerts`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.alerts() });
    },
  });
}

export function useUpdateAlert() {
  const queryClient = useQueryClient();
  return useMutation<CompetitorAlert, Error, { id: string; updates: Partial<CreateAlertRequest & { active: boolean }> }>({
    mutationFn: async ({ id, updates }) => {
      const { data } = await api.patch(`${API_PREFIX}/alerts/${id}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.alerts() });
    },
  });
}

export function useDeleteAlert() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/alerts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.alerts() });
    },
  });
}

export function useAlertHistory(page = 1, limit = 20) {
  return useQuery<{ events: AlertEvent[] }>({
    queryKey: competitorKeys.alertHistory(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/alerts/history`, {
        params: { page, limit },
      });
      return data;
    },
  });
}
