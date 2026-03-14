/**
 * TypeScript types for the Coloring Book Creator.
 *
 * Covers wizard, line art quality pipeline, page editor, batch generation,
 * quality dashboard, volume factory, and export.
 *
 * Blueprint refs: 4.1-4.8, 13.2, 14.2
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type ColoringAudience = "kids" | "teens" | "adults";

export type LineStyle =
  | "clean_outlines"
  | "sketchy_hand_drawn"
  | "whimsical_decorative"
  | "realistic_detailed"
  | "zentangle"
  | "bold_simple";

export type GenerationMethod = "all_at_once" | "one_at_a_time" | "mix";

export type ColoringPageType = "coloring" | "bonus" | "blank";

export type ColoringPageStatus =
  | "pending"
  | "generating"
  | "generated"
  | "cleaned"
  | "approved";

export type ColoringBookStatus = "draft" | "in_progress" | "published";

export type BonusPageType =
  | "title"
  | "belongs_to"
  | "color_test"
  | "progress_tracker"
  | "certificate"
  | "difficulty_ratings";

export type ColoringSimulationTool = "marker" | "crayon" | "colored_pencil";

export type ColoringExportFormat = "pdf" | "png" | "svg" | "digital_pdf";

// ---------------------------------------------------------------------------
// Core interfaces
// ---------------------------------------------------------------------------

export interface ColoringBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  audience: ColoringAudience;
  status: ColoringBookStatus;
  page_count: number;
  pages_created: number;
  trim_size: string;
  line_style: LineStyle;
  line_weight: number;
  complexity: number;
  stroke_uniformity: boolean;
  theme_description?: string;
  generation_method: GenerationMethod;
  bonus_pages: BonusPageType[];
  series_id?: string;
  series_name?: string;
  volume_number?: number;
  quality_score?: number;
  cover_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ColoringPage {
  id: string;
  book_id: string;
  page_number: number;
  page_type: ColoringPageType;
  illustration_prompt?: string;
  illustration_url?: string;
  cleaned_url?: string;
  vectorized_url?: string;
  illustration_model?: string;
  illustration_seed?: string;
  quality_score?: number;
  quality_issues?: string[];
  complexity_score?: number;
  ink_density?: number;
  is_duplicate?: boolean;
  status: ColoringPageStatus;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Line Art Quality Pipeline (7 steps)
// ---------------------------------------------------------------------------

export interface LineArtQualityStep {
  step: number;
  name: string;
  status: "pending" | "running" | "passed" | "failed";
  issues?: string[];
}

export interface LineArtQualityReport {
  page_id: string;
  steps: LineArtQualityStep[];
  overall_passed: boolean;
  auto_clean_applied: boolean;
  closed_shapes_count: number;
  open_shapes_count: number;
  specks_removed: number;
  background_pure_white: boolean;
}

// ---------------------------------------------------------------------------
// Wizard / creation payloads
// ---------------------------------------------------------------------------

export interface CreateColoringBookRequest {
  title: string;
  subtitle?: string;
  audience: ColoringAudience;
  page_count: number;
  trim_size: string;
  line_style: LineStyle;
  line_weight: number;
  complexity: number;
  stroke_uniformity: boolean;
  theme_description?: string;
  generation_method: GenerationMethod;
  bonus_pages: BonusPageType[];
  series_name?: string;
  volume_number?: number;
  template_id?: string;
}

// ---------------------------------------------------------------------------
// Batch generation
// ---------------------------------------------------------------------------

export interface BatchGenerateResult {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  total_pages: number;
  completed_pages: number;
  failed_pages: number;
  cost_estimate_cents?: number;
}

// ---------------------------------------------------------------------------
// Quality dashboard
// ---------------------------------------------------------------------------

export interface ComplexityDistribution {
  level: number;
  count: number;
}

export interface PrintQualityMetrics {
  line_quality: number;
  closed_shapes: number;
  stroke_uniformity: number;
  ink_density: number;
  small_areas: number;
}

export interface QualityCheckResult {
  overall_score: number;
  complexity_distribution: ComplexityDistribution[];
  theme_cohesion_score: number;
  issues: {
    page_id: string;
    page_number: number;
    issues: string[];
  }[];
  print_quality: PrintQualityMetrics;
  duplicate_pages: { page_a: number; page_b: number; similarity: number }[];
}

// ---------------------------------------------------------------------------
// Volume factory
// ---------------------------------------------------------------------------

export interface VolumeCard {
  volume_number: number;
  book_id?: string;
  title: string;
  theme: string;
  status: "planned" | "draft" | "in_progress" | "published";
  page_count: number;
  quality_score?: number;
}

export interface SeriesPlan {
  series_name: string;
  volumes: VolumeCard[];
  branding_locked: boolean;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export interface ColoringExportOptions {
  format: ColoringExportFormat;
  dpi?: number;
}

export interface ColoringExportResult {
  download_url: string;
  format: string;
  file_size: number;
  page_count: number;
}

// ---------------------------------------------------------------------------
// Coloring simulation
// ---------------------------------------------------------------------------

export interface ColoringSimulationResult {
  page_id: string;
  tool: ColoringSimulationTool;
  preview_url: string;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export interface ColoringBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  pages_created: number;
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export interface ColoringTemplate {
  id: string;
  name: string;
  description: string;
  thumbnail_url: string;
  audience: ColoringAudience;
  theme: string;
  page_count: number;
  line_style: LineStyle;
  complexity: number;
}
