"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CompetitorAnalysis,
  CompetitorAnalysisDetail,
  WeaknessSignal,
  OpportunityBlueprint,
  GapAnalysis,
  CompetitorAlert,
  CompetitorAnalyzeRequest,
  BatchAnalyzeRequest,
  BatchAnalyzeResponse,
  GapAnalysisRequest,
} from "./types";

const API_PREFIX = "/api/v1/competitors";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const competitorKeys = {
  all: ["competitors"] as const,
  analyses: () => [...competitorKeys.all, "analyses"] as const,
  analysis: (id: string) => [...competitorKeys.all, "analysis", id] as const,
  weaknesses: (analysisId: string) => [...competitorKeys.all, "weaknesses", analysisId] as const,
  opportunity: (analysisId: string) => [...competitorKeys.all, "opportunity", analysisId] as const,
  gaps: (niche?: string) => [...competitorKeys.all, "gaps", niche] as const,
  alerts: (includeDismissed?: boolean) => [...competitorKeys.all, "alerts", includeDismissed] as const,
};

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
