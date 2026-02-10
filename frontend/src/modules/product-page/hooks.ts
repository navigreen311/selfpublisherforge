"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Recommendation {
  area: string;
  severity: "critical" | "warning" | "info";
  message: string;
  suggestion: string;
  current_value?: string;
  recommended_value?: string;
}

export interface TitleAnalysis {
  score: number;
  length: number;
  has_keywords: boolean;
  keyword_matches: string[];
  power_words: string[];
  issues: string[];
}

export interface BlurbAnalysis {
  score: number;
  word_count: number;
  has_hook: boolean;
  has_bullet_points: boolean;
  has_cta: boolean;
  has_html_formatting: boolean;
  readability_grade: number;
  emotional_words: string[];
  issues: string[];
}

export interface KeywordAnalysis {
  score: number;
  keywords_found: string[];
  keyword_density: number;
  missing_high_value_keywords: string[];
  over_stuffed: boolean;
}

export interface CategoryAnalysis {
  score: number;
  current_categories: string[];
  suggested_categories: string[];
  category_rank_potential?: string;
}

export interface PriceAnalysis {
  score: number;
  current_price?: number;
  genre_avg_price?: number;
  suggested_range?: string;
  issues: string[];
}

export interface ListingAnalysis {
  asin?: string;
  title?: string;
  title_score: number;
  blurb_score: number;
  keyword_score: number;
  category_score: number;
  price_score: number;
  overall_score: number;
  title_analysis: TitleAnalysis;
  blurb_analysis: BlurbAnalysis;
  keyword_analysis: KeywordAnalysis;
  category_analysis: CategoryAnalysis;
  price_analysis: PriceAnalysis;
  recommendations: Recommendation[];
  analyzed_at: string;
}

export interface BlurbVariant {
  variant_id: string;
  content: string;
  style: string;
  hook_type: string;
  estimated_conversion_score: number;
  highlights: string[];
}

export interface BlurbGenerateResponse {
  original_score: number;
  variants: BlurbVariant[];
  generation_metadata: Record<string, unknown>;
}

export interface ABTestVariantResult {
  variant_label: string;
  content: string;
  impressions: number;
  clicks: number;
  click_through_rate: number;
  conversion_rate: number;
  estimated_score: number;
}

export interface ABTestResponse {
  id: string;
  book_id: string;
  name: string;
  status: "draft" | "running" | "paused" | "completed";
  variant_a: ABTestVariantResult;
  variant_b: ABTestVariantResult;
  winner?: string;
  confidence?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MobileTruncation {
  field: string;
  original_length: number;
  visible_length: number;
  is_truncated: boolean;
  visible_text: string;
  truncated_text?: string;
}

export interface MobileCheckResult {
  overall_score: number;
  title_display: MobileTruncation;
  subtitle_display?: MobileTruncation;
  blurb_fold_point: number;
  blurb_above_fold: string;
  blurb_above_fold_word_count: number;
  cover_aspect_ratio_ok: boolean;
  cover_readable_at_thumbnail: boolean;
  price_visibility: string;
  buy_button_proximity: string;
  recommendations: Recommendation[];
  device_previews: Record<string, Record<string, unknown>>;
}

export interface LookInsideSection {
  section: string;
  score: number;
  feedback: string;
  suggestions: string[];
}

export interface LookInsideAnalysis {
  overall_score: number;
  hook_strength: number;
  first_page_impact: number;
  pacing_score: number;
  toc_effectiveness: number;
  sections: LookInsideSection[];
  recommendations: Recommendation[];
}

export interface ConversionScores {
  book_id: string;
  listing_score?: number;
  blurb_score?: number;
  mobile_score?: number;
  look_inside_score?: number;
  overall_score: number;
  last_analyzed_at?: string;
  recommendations_count: number;
}

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface AnalyzeListingRequest {
  asin?: string;
  url?: string;
  book_id?: string;
}

export interface GenerateBlurbRequest {
  book_id?: string;
  current_blurb: string;
  genre: string;
  target_audience?: string;
  keywords?: string[];
  tone?: string;
  num_variants?: number;
}

export interface CreateABTestRequest {
  book_id: string;
  name: string;
  variant_a: string;
  variant_b: string;
  duration_days?: number;
}

export interface LookInsideAnalyzeRequest {
  book_id?: string;
  preview_text: string;
  genre: string;
  chapter_titles?: string[];
}

export interface MobileCheckRequest {
  title: string;
  subtitle?: string;
  blurb: string;
  author_name: string;
  cover_image_url?: string;
  price?: number;
}

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
      const { data } = await api.post(`${BASE}/analyze`, req);
      return data.data;
    },
  });
}

/** Generate optimized blurb variations. */
export function useGenerateBlurb() {
  return useMutation<BlurbGenerateResponse, Error, GenerateBlurbRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post(`${BASE}/blurb/generate`, req);
      return data.data;
    },
  });
}

/** Create an A/B test for blurbs. */
export function useCreateABTest() {
  return useMutation<ABTestResponse, Error, CreateABTestRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post(`${BASE}/blurb/ab-test`, req);
      return data.data;
    },
  });
}

/** Fetch A/B test results by ID. */
export function useABTestResults(testId: string | undefined) {
  return useQuery<ABTestResponse>({
    queryKey: ["ab-test", testId],
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/blurb/ab-test/${testId}`);
      return data.data;
    },
    enabled: !!testId,
  });
}

/** Analyze Look Inside preview effectiveness. */
export function useAnalyzeLookInside() {
  return useMutation<LookInsideAnalysis, Error, LookInsideAnalyzeRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post(`${BASE}/look-inside/analyze`, req);
      return data.data;
    },
  });
}

/** Check listing appearance on mobile. */
export function useMobileCheck() {
  return useMutation<MobileCheckResult, Error, MobileCheckRequest>({
    mutationFn: async (req) => {
      const { data } = await api.post(`${BASE}/mobile-check`, req);
      return data.data;
    },
  });
}

/** Get conversion optimization scores for a book. */
export function useConversionScores(bookId: string | undefined) {
  return useQuery<ConversionScores>({
    queryKey: ["conversion-scores", bookId],
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/scores/${bookId}`);
      return data.data;
    },
    enabled: !!bookId,
  });
}
