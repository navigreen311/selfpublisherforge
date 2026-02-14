"use client";

/**
 * React Query hooks for the Product Page Conversion Lab.
 *
 * All product-page endpoints return SuccessResponse<T> = { data: T }.
 * After Axios destructuring (`const { data } = await api.get<SuccessResponse<T>>(...)`),
 * the inner payload is accessed via `data.data`.
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SuccessResponse } from "@/types/api";
import type {
  Recommendation,
  TitleAnalysis,
  BlurbAnalysis,
  KeywordAnalysis,
  CategoryAnalysis,
  PriceAnalysis,
  ListingAnalysis,
  BlurbVariant,
  BlurbGenerateResponse,
  ABTestVariantResult,
  ABTestResponse,
  MobileTruncation,
  MobileCheckResult,
  LookInsideSection,
  LookInsideAnalysis,
  ConversionScores,
  AnalyzeListingRequest,
  GenerateBlurbRequest,
  CreateABTestRequest,
  LookInsideAnalyzeRequest,
  MobileCheckRequest,
  ListingAnalysisResult,
  BlurbVersion,
  OptimizeKeywordsRequest,
  OptimizeKeywordsResponse,
  APlusPlanResponse,
} from "./types";

export type * from "./types";

// ---------------------------------------------------------------------------
// API base path
// ---------------------------------------------------------------------------

const BASE = "/api/v1/product-page";

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/** Analyze an Amazon listing by ASIN or URL. */
export function useAnalyzeListing() {
  return useMutation<ListingAnalysis, Error, AnalyzeListingRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<ListingAnalysis>>(`${BASE}/analyze`, req);
      return data.data;
    },
  });
}

/** Generate optimized blurb variations. */
export function useGenerateBlurb() {
  return useMutation<BlurbGenerateResponse, Error, GenerateBlurbRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<BlurbGenerateResponse>>(`${BASE}/blurb/generate`, req);
      return data.data;
    },
  });
}

/** Create an A/B test for blurbs. */
export function useCreateABTest() {
  return useMutation<ABTestResponse, Error, CreateABTestRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<ABTestResponse>>(`${BASE}/blurb/ab-test`, req);
      return data.data;
    },
  });
}

/** Fetch A/B test results by ID. */
export function useABTestResults(testId: string | undefined) {
  return useQuery<ABTestResponse>({
    queryKey: ["ab-test", testId],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<ABTestResponse>>(`${BASE}/blurb/ab-test/${testId}`);
      return data.data;
    },
    enabled: !!testId,
  });
}

/** Analyze Look Inside preview effectiveness. */
export function useAnalyzeLookInside() {
  return useMutation<LookInsideAnalysis, Error, LookInsideAnalyzeRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<LookInsideAnalysis>>(`${BASE}/look-inside/analyze`, req);
      return data.data;
    },
  });
}

/** Check listing appearance on mobile. */
export function useMobileCheck() {
  return useMutation<MobileCheckResult, Error, MobileCheckRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<MobileCheckResult>>(`${BASE}/mobile-check`, req);
      return data.data;
    },
  });
}

/** Get conversion optimization scores for a book. */
export function useConversionScores(bookId: string | undefined) {
  return useQuery<ConversionScores>({
    queryKey: ["conversion-scores", bookId],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<ConversionScores>>(`${BASE}/scores/${bookId}`);
      return data.data;
    },
    enabled: !!bookId,
  });
}

// ---------------------------------------------------------------------------
// Extended hooks for enhanced Product Page Lab
// ---------------------------------------------------------------------------

/** Analyze a listing (mutation alias with enhanced return type). */
export function useAnalyzeListingMutation() {
  return useMutation<ListingAnalysisResult, Error, AnalyzeListingRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<ListingAnalysisResult>>(`${BASE}/analyze`, req);
      return data.data;
    },
  });
}

/** List past listing analyses. */
export function useListingAnalyses() {
  return useQuery<ListingAnalysisResult[]>({
    queryKey: ["listing-analyses"],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<ListingAnalysisResult[]>>(`${BASE}/analyses`);
      return data.data;
    },
  });
}

/** Get a single listing analysis by ID. */
export function useListingAnalysisDetail(id: string | undefined) {
  return useQuery<ListingAnalysisResult>({
    queryKey: ["listing-analysis", id],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<ListingAnalysisResult>>(`${BASE}/analyses/${id}`);
      return data.data;
    },
    enabled: !!id,
  });
}

/** Mobile check mutation (enhanced). */
export function useMobileCheckMutation() {
  return useMutation<MobileCheckResult, Error, MobileCheckRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<MobileCheckResult>>(`${BASE}/mobile-check`, req);
      return data.data;
    },
  });
}

/** Generate blurb with 3 style versions. */
export function useGenerateBlurbMutation() {
  return useMutation<BlurbVersion[], Error, GenerateBlurbRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<BlurbVersion[]>>(`${BASE}/blurb/generate`, req);
      return data.data;
    },
  });
}

/** List previously generated blurbs. */
export function useGeneratedBlurbs() {
  return useQuery<BlurbVersion[]>({
    queryKey: ["generated-blurbs"],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<BlurbVersion[]>>(`${BASE}/blurbs`);
      return data.data;
    },
  });
}

/** Optimize keywords for a book listing. */
export function useOptimizeKeywordsMutation() {
  return useMutation<OptimizeKeywordsResponse, Error, OptimizeKeywordsRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<OptimizeKeywordsResponse>>(`${BASE}/optimize-keywords`, req);
      return data.data;
    },
  });
}

/** Generate an A+ content plan. */
export function useGenerateAPlusPlan() {
  return useMutation<APlusPlanResponse, Error, { book_id?: string; genre: string; title: string }>({
    mutationFn: async (req) => {
      const { data } = await api.post<SuccessResponse<APlusPlanResponse>>(`${BASE}/aplus-plan`, req);
      return data.data;
    },
  });
}

/** List past A+ plans. */
export function useAPlusPlans() {
  return useQuery<APlusPlanResponse[]>({
    queryKey: ["aplus-plans"],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<APlusPlanResponse[]>>(`${BASE}/aplus-plans`);
      return data.data;
    },
  });
}

/** Get a single A+ plan by ID. */
export function useAPlusPlanDetail(id: string | undefined) {
  return useQuery<APlusPlanResponse>({
    queryKey: ["aplus-plan", id],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<APlusPlanResponse>>(`${BASE}/aplus-plans/${id}`);
      return data.data;
    },
    enabled: !!id,
  });
}
