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
