"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
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
