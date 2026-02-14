"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { extractApiError } from "@/hooks/use-api";
import type {
  PriceSimulationRequest,
  PriceSimulationResponse,
  KUCalculatorRequest,
  KUCalculatorResponse,
  PricingRule,
  CompetitorPriceSummary,
  PaginatedResponse,
  BookFormat,
  RuleStatus,
  PricingStrategy,
  StrategyCreatePayload,
  ScheduledPriceChange,
  ScheduledChangePayload,
  PriceHistoryEntry,
  RoyaltyAnalysisResponse,
  EnhancedSimulationResponse,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/pricing";

// ---------- Query Keys ----------

export const pricingKeys = {
  all: ["pricing"] as const,
  rules: (status?: RuleStatus, bookId?: string) =>
    [...pricingKeys.all, "rules", status, bookId] as const,
  competitors: (bookId: string, format?: BookFormat) =>
    [...pricingKeys.all, "competitors", bookId, format] as const,
  promotions: (bookId?: string) =>
    [...pricingKeys.all, "promotions", bookId] as const,
};

// ---------- Hooks ----------

export function usePricingRules(params?: {
  status?: RuleStatus;
  book_id?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<PaginatedResponse<PricingRule>>({
    queryKey: pricingKeys.rules(params?.status, params?.book_id),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set("status", params.status);
      if (params?.book_id) searchParams.set("book_id", params.book_id);
      if (params?.limit) searchParams.set("limit", String(params.limit));
      if (params?.offset) searchParams.set("offset", String(params.offset));
      const { data } = await api.get(`${API_PREFIX}/rules?${searchParams}`);
      return data;
    },
  });
}

export function useSimulatePrice() {
  return useMutation<PriceSimulationResponse, Error, PriceSimulationRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/simulate`, request);
      return data;
    },
  });
}

export function useKUCalculator() {
  return useMutation<KUCalculatorResponse, Error, KUCalculatorRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/ku-calculator`, request);
      return data;
    },
  });
}

export function useCompetitorPrices(bookId: string, format?: BookFormat) {
  return useQuery<CompetitorPriceSummary>({
    queryKey: pricingKeys.competitors(bookId, format),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (format) params.set("book_format", format);
      const { data } = await api.get(
        `${API_PREFIX}/competitors/${bookId}?${params}`
      );
      return data;
    },
    enabled: !!bookId,
  });
}

export function useCreatePricingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: Partial<PricingRule>) => {
      const { data } = await api.post(`${API_PREFIX}/rules`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
    },
  });
}

export function useUpdatePricingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...request
    }: Partial<PricingRule> & { id: string }) => {
      const { data } = await api.patch(`${API_PREFIX}/rules/${id}`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
    },
  });
}

export function useDeletePricingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${API_PREFIX}/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
    },
  });
}

// ---------- Strategy Hooks ----------

export function usePricingStrategies(status?: string) {
  return useQuery({
    queryKey: [...pricingKeys.all, "strategies", status],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pricing/strategies", { params: status ? { status } : {} });
      return data.data as PricingStrategy[];
    },
  });
}

export function useCreateStrategy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StrategyCreatePayload) => {
      const { data } = await api.post("/api/v1/pricing/strategies", payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
      toast.success("Strategy created");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...updates }: { id: string } & Partial<StrategyCreatePayload>) => {
      const { data } = await api.patch(`/api/v1/pricing/strategies/${id}`, updates);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/pricing/strategies/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
      toast.success("Strategy deleted");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

// ---------- Scheduled Changes Hooks ----------

export function useScheduledChanges(bookId?: string) {
  return useQuery({
    queryKey: [...pricingKeys.all, "scheduled-changes", bookId],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pricing/scheduled-changes", { params: bookId ? { book_id: bookId } : {} });
      return data.data as ScheduledPriceChange[];
    },
  });
}

export function useCreateScheduledChange() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduledChangePayload) => {
      const { data } = await api.post("/api/v1/pricing/scheduled-changes", payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
      toast.success("Price change scheduled");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

export function useCancelScheduledChange() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/pricing/scheduled-changes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pricingKeys.all });
      toast.success("Scheduled change cancelled");
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}

// ---------- History & Analysis Hooks ----------

export function usePriceHistory(bookId?: string, period: string = "90d") {
  return useQuery({
    queryKey: [...pricingKeys.all, "history", bookId, period],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pricing/history", { params: { book_id: bookId, period } });
      return data.data as PriceHistoryEntry[];
    },
  });
}

export function useRoyaltyAnalysis(period: string = "30d") {
  return useQuery({
    queryKey: [...pricingKeys.all, "royalty-analysis", period],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pricing/royalty-analysis", { params: { period } });
      return data.data as RoyaltyAnalysisResponse;
    },
  });
}

export function useEnhancedSimulation() {
  return useMutation({
    mutationFn: async (request: PriceSimulationRequest) => {
      const { data } = await api.post("/api/v1/pricing/simulate/enhanced", request);
      return data.data as EnhancedSimulationResponse;
    },
    onError: (error: any) => toast.error(extractApiError(error)),
  });
}
