/**
 * Shared TypeScript types for the Specialty Books module.
 *
 * These types are used across Children's, Coloring, and Puzzle book studios
 * for provenance, originality, pricing, color management, batch processing,
 * series management, accessibility, and distributor preflight.
 *
 * Blueprint refs: 6.1-6.5, 7.1-7.4, 8.1-8.2, 9.1-9.3, 10.1-10.3, 11.1-11.3,
 * 12.1-12.6, 13.4
 */

// ---------------------------------------------------------------------------
// Book type discriminator
// ---------------------------------------------------------------------------

export type BookType = "childrens" | "coloring" | "puzzle";

// ---------------------------------------------------------------------------
// Asset Provenance & Rights Ledger (6.2)
// ---------------------------------------------------------------------------

export type AssetType =
  | "illustration"
  | "line_art"
  | "puzzle_grid"
  | "cover"
  | "reference_image";

export interface ProvenanceRecord {
  id: string;
  org_id: string;
  book_type: BookType;
  book_id: string;
  page_id?: string;
  asset_type: AssetType;
  model?: string;
  prompt_text?: string;
  prompt_hash?: string;
  seed?: string;
  settings?: Record<string, unknown>;
  generation_date: string;
  status: string;
}

export interface ProvenanceReport {
  report_type: "provenance";
  book_type: BookType;
  book_id: string;
  generated_at: string;
  total_assets: number;
  models_used: string[];
  assets: ProvenanceRecord[];
}

// ---------------------------------------------------------------------------
// Originality Fingerprinting (7.1-7.3)
// ---------------------------------------------------------------------------

export type ContentType = "image" | "grid" | "word_list" | "text";

export interface FingerprintResult {
  id: string;
  book_type: BookType;
  book_id: string;
  page_id?: string;
  content_type: ContentType;
  phash?: string;
  data_hash?: string;
  ngram_fingerprint?: string;
  jaccard_vector?: Record<string, number>;
  created_at: string;
}

export interface SimilarityComparison {
  book_a_id: string;
  book_b_id: string;
  overall_similarity: number;
  component_scores: {
    images?: number;
    grids?: number;
    word_lists?: number;
    text?: number;
  };
  flagged: boolean;
}

// ---------------------------------------------------------------------------
// KDP Spam Risk Detector (7.2, 7.4)
// ---------------------------------------------------------------------------

export type SpamRiskLevel = "low" | "medium" | "high" | "critical";

export interface SpamRiskReport {
  book_type: BookType;
  book_id: string;
  overall_score: number;
  risk_level: SpamRiskLevel;
  interior_originality: number;
  metadata_quality: number;
  minor_edit_score: number;
  content_substance: number;
  flags: string[];
  recommendations: string[];
}

// ---------------------------------------------------------------------------
// Print Cost & Pricing Engine (8.1)
// ---------------------------------------------------------------------------

export type InteriorType = "black_white" | "premium_color" | "standard_color";

export interface PricingScenario {
  label: string;
  list_price: number;
  print_cost: number;
  royalty: number;
  margin_percent: number;
}

export interface PricingResult {
  book_type: BookType;
  page_count: number;
  trim_size: string;
  interior_type: InteriorType;
  ink_coverage_percent?: number;
  print_cost: number;
  minimum_list_price: number;
  scenarios: PricingScenario[];
  margin_warning?: string;
}

export interface InkCoveragePage {
  page_number: number;
  coverage_percent: number;
  density_score: number;
}

export interface InkCoverageResult {
  book_id: string;
  pages: InkCoveragePage[];
  average_coverage: number;
  aggregate_density: number;
}

// ---------------------------------------------------------------------------
// CMYK / Soft-Proof Workflow (8.2)
// ---------------------------------------------------------------------------

export interface GamutWarning {
  page_number: number;
  x: number;
  y: number;
  rgb_value: string;
  cmyk_value: string;
  delta_e: number;
}

export interface SoftProofResult {
  book_id: string;
  page_number: number;
  rgb_preview_url: string;
  cmyk_preview_url: string;
  out_of_gamut_warnings: GamutWarning[];
  shadow_crush_detected: boolean;
  ink_density_percent: number;
}

export interface ColorAdjustResult {
  book_id: string;
  pages_adjusted: number;
  gamut_fixes: number;
  ink_density_fixes: number;
  shadow_fixes: number;
}

// ---------------------------------------------------------------------------
// Batch Factory Mode (6.4)
// ---------------------------------------------------------------------------

export type BatchStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export interface BatchJob {
  id: string;
  org_id: string;
  book_type: BookType;
  batch_config: Record<string, unknown>;
  budget_limit_cents: number;
  spent_cents: number;
  status: BatchStatus;
  volumes_total: number;
  volumes_completed: number;
  pages_total: number;
  pages_completed: number;
  pages_failed: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Template & Pack Marketplace (6.5)
// ---------------------------------------------------------------------------

export interface Template {
  id: string;
  name: string;
  description: string;
  book_type: BookType;
  category: string;
  thumbnail_url: string;
  config: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Series Branding Manager (12.1)
// ---------------------------------------------------------------------------

export interface BrandingConfig {
  title_font?: string;
  title_position?: string;
  author_position?: string;
  volume_badge?: boolean;
  spine_layout?: string;
  color_scheme?: Record<string, string>;
}

export interface Series {
  id: string;
  org_id: string;
  name: string;
  book_type: BookType;
  naming_format: string;
  branding_config: BrandingConfig;
  branding_locked: boolean;
  volume_count: number;
  volumes: SeriesVolume[];
  created_at: string;
  updated_at: string;
}

export interface SeriesVolume {
  book_id: string;
  volume_number: number;
  title: string;
  status: string;
}

export interface CoherenceCheckResult {
  series_id: string;
  overall_score: number;
  branding_consistent: boolean;
  naming_consistent: boolean;
  spine_consistent: boolean;
  theme_score: number;
  issues: string[];
}

// ---------------------------------------------------------------------------
// Back Matter CTA Engine (12.2)
// ---------------------------------------------------------------------------

export type BackMatterTemplateType =
  | "about_author"
  | "also_by"
  | "review_request"
  | "newsletter_signup"
  | "custom";

export interface BackMatterTemplate {
  id: string;
  org_id: string;
  template_type: BackMatterTemplateType;
  content: string;
  cta_url?: string;
  qr_code_url?: string;
}

export interface QRCodeResult {
  qr_code_url: string;
  target_url: string;
  format: "png" | "svg";
  size_px: number;
}

// ---------------------------------------------------------------------------
// ISBN & Barcode Management (12.4)
// ---------------------------------------------------------------------------

export type ISBNStatus = "available" | "assigned" | "used";

export interface ISBNRecord {
  id: string;
  org_id: string;
  isbn: string;
  publisher_name: string;
  assigned_to_book_type?: BookType;
  assigned_to_book_id?: string;
  barcode_url?: string;
  status: ISBNStatus;
}

// ---------------------------------------------------------------------------
// Multi-Distributor Preflight (12.5)
// ---------------------------------------------------------------------------

export type DistributorName = "kdp" | "ingram_spark" | "bn_press";

export type PreflightStatus = "pending" | "passed" | "failed" | "warnings";

export interface PreflightCheck {
  name: string;
  passed: boolean;
  message: string;
  severity: "error" | "warning" | "info";
}

export interface DistributorPreflight {
  id: string;
  book_type: BookType;
  book_id: string;
  distributor: DistributorName;
  status: PreflightStatus;
  checks: PreflightCheck[];
  issues: string[];
  exported_url?: string;
}

// ---------------------------------------------------------------------------
// Accessibility Pack (11.1-11.3)
// ---------------------------------------------------------------------------

export type VariantType = "dyslexia_friendly" | "large_print" | "high_contrast";

export interface AccessibilitySettings {
  font_family?: string;
  line_spacing?: number;
  letter_spacing?: number;
  text_alignment?: string;
  background_color?: string;
  min_font_size?: number;
  contrast_ratio?: number;
  grid_line_thickness?: number;
  scale_factor?: number;
}

export interface AccessibilityVariant {
  id: string;
  source_book_type: BookType;
  source_book_id: string;
  variant_type: VariantType;
  variant_book_id: string;
  settings: AccessibilitySettings;
}

// ---------------------------------------------------------------------------
// Device Preview System (9.2)
// ---------------------------------------------------------------------------

export type DeviceName =
  | "kindle_fire_hd_10"
  | "kindle_fire_hd_8"
  | "kindle_paperwhite"
  | "ipad"
  | "ipad_mini"
  | "iphone";

export interface DeviceSpec {
  name: DeviceName;
  display_name: string;
  width_px: number;
  height_px: number;
  ppi: number;
}

export interface DevicePreviewResult {
  device: DeviceName;
  preview_url: string;
  width_px: number;
  height_px: number;
}

// ---------------------------------------------------------------------------
// Safe-Zone Heatmap & Gutter (10.1-10.2)
// ---------------------------------------------------------------------------

export interface SafeZoneOverlay {
  page_number: number;
  overlay_url: string;
  bleed_zone: { top: number; right: number; bottom: number; left: number };
  trim_zone: { top: number; right: number; bottom: number; left: number };
  safe_zone: { top: number; right: number; bottom: number; left: number };
  gutter_zone: number;
  face_detections: { x: number; y: number; width: number; height: number }[];
  text_detections: { x: number; y: number; width: number; height: number }[];
}

export interface GutterCheckResult {
  book_id: string;
  pages_checked: number;
  collisions: {
    page_number: number;
    element_type: "face" | "text" | "content";
    distance_from_gutter: number;
    auto_shift_available: boolean;
  }[];
}

// ---------------------------------------------------------------------------
// Auto-Reflow (10.3)
// ---------------------------------------------------------------------------

export interface ReflowRequest {
  target_trim_size: string;
}

export interface ReflowResult {
  new_book_id: string;
  original_trim_size: string;
  target_trim_size: string;
  pages_reflowed: number;
  issues: string[];
}

// ---------------------------------------------------------------------------
// Kindle Export (9.1)
// ---------------------------------------------------------------------------

export type KindleFormat = "kpf" | "epub3";

export interface KindleExportRequest {
  format: KindleFormat;
  include_read_aloud?: boolean;
  include_text_popup?: boolean;
}

export interface KindleExportResult {
  download_url: string;
  format: KindleFormat;
  file_size: number;
  page_count: number;
  read_aloud_enabled: boolean;
}

// ---------------------------------------------------------------------------
// Font Licensing (6.2)
// ---------------------------------------------------------------------------

export type LicenseType = "open_source" | "commercial" | "personal" | "sil_ofl";

export interface FontLicense {
  id: string;
  font_name: string;
  license_type: LicenseType;
  commercial_print: boolean;
  source: string;
  license_url?: string;
}

// ---------------------------------------------------------------------------
// KDP Metadata Advisor (6.3)
// ---------------------------------------------------------------------------

export interface MetadataAdvisorRequest {
  title: string;
  subtitle?: string;
  description?: string;
  book_type: BookType;
  audience?: string;
  themes?: string[];
}

export interface MetadataAdvisorResult {
  bisac_categories: { code: string; name: string; confidence: number }[];
  keywords: string[];
  subtitle_suggestions: string[];
  compliance_issues: string[];
}

// ---------------------------------------------------------------------------
// Common API payload types
// ---------------------------------------------------------------------------

export interface ExportOptions {
  format: string;
  dpi?: number;
  include_provenance?: boolean;
  include_font_summary?: boolean;
}

export interface ExportResult {
  download_url: string;
  format: string;
  file_size: number;
  page_count: number;
}
