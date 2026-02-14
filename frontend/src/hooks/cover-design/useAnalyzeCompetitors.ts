/**
 * Hook for analyzing competitor book covers to extract design patterns.
 *
 * Fetches top-performing covers for a genre/subcategory and analyzes:
 *   - Dominant colors and palettes
 *   - Typography patterns
 *   - Layout patterns
 *   - Image styles
 *   - AI-generated recommendations
 */

import { useApiQuery } from "@/hooks/use-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CoverThumbnail {
  id: string;
  title: string;
  author: string;
  image_url: string;
  bsr: number;
  rating?: number;
}

export interface ColorAnalysis {
  color: string; // hex code
  percentage: number;
  name: string; // color name
}

export interface TypographyPattern {
  serif: number;
  sans_serif: number;
  script: number;
  decorative: number;
}

export interface LayoutPattern {
  centered: number;
  left_aligned: number;
  right_aligned: number;
  asymmetric: number;
}

export interface ImageStyle {
  photography: number;
  illustration: number;
  abstract: number;
  typography_only: number;
}

export interface DesignInsights {
  dominant_colors: ColorAnalysis[];
  typography_patterns: TypographyPattern;
  layout_patterns: LayoutPattern;
  image_styles: ImageStyle;
  recommendations: string[];
}

export interface CompetitorCoversAnalysis {
  covers: CoverThumbnail[];
  insights: DesignInsights;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseAnalyzeCompetitorsParams {
  genre?: string;
  subcategory?: string;
  enabled?: boolean;
}

export function useAnalyzeCompetitors({
  genre,
  subcategory,
  enabled = true,
}: UseAnalyzeCompetitorsParams) {
  const params: Record<string, unknown> = {};
  if (genre) params.genre = genre;
  if (subcategory) params.subcategory = subcategory;

  return useApiQuery<CompetitorCoversAnalysis>({
    queryKey: ["competitor-covers", genre, subcategory],
    url: "/api/v1/cover-design/analyze-competitors",
    params,
    enabled: enabled && !!genre,
  });
}
