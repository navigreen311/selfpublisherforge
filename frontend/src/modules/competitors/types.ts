/**
 * TypeScript types for the Competitor Finder module
 * Mirrors backend schemas from backend/app/modules/competitor_finder/schemas.py
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type WeaknessCategory =
  | "content_quality"
  | "format_layout"
  | "missing_features"
  | "pricing"
  | "coverage_gaps"
  | "content_depth"
  | "missing_deliverables"
  | "practical_gaps"
  | "production_quality"
  | "voice_mismatch"
  | "currency_gaps"
  | "value_perception"
  | "promise_delivery";

export type Severity = "low" | "medium" | "high" | "critical";

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";

export type AlertType =
  | "price_change"
  | "bsr_shift"
  | "new_book"
  | "review_spike"
  | "bsr_drop"
  | "new_negative_theme"
  | "rank_change"
  | "new_book_by_author";

export type AlertSeverity = "info" | "warning" | "critical";

// ---------------------------------------------------------------------------
// Evidence and sub-schemas
// ---------------------------------------------------------------------------

export interface ReviewEvidence {
  review_id?: string;
  excerpt: string;
  rating?: number;
  helpful_votes?: number;
}

export interface WeaknessSignal {
  id: string;
  analysis_id: string;
  category: WeaknessCategory;
  severity: Severity;
  signal_text: string;
  evidence?: ReviewEvidence[];
  frequency: number;
  confidence: number;
  actionable: boolean;
  suggestion?: string;
  book_sources?: string[];
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Opportunity Blueprint
// ---------------------------------------------------------------------------

export interface ContentStrategy {
  key_topics: string[];
  unique_angles: string[];
  depth_level: string;
  suggested_length?: string;
  structure_notes?: string;
}

export interface PricingStrategy {
  recommended_price?: number;
  price_range_low?: number;
  price_range_high?: number;
  rationale?: string;
  bundle_suggestions: string[];
}

export interface OpportunityBlueprint {
  id: string;
  analysis_id: string;
  title_suggestions?: string[];
  content_strategy?: ContentStrategy;
  format_recommendations?: string[];
  pricing_strategy?: PricingStrategy;
  differentiators?: string[];
  target_audience?: string;
  estimated_opportunity_score?: number;
  action_items?: string[];
  differentiation_score?: number;
  full_blueprint?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Competitor Analysis
// ---------------------------------------------------------------------------

export interface CompetitorBookBrief {
  id: string;
  asin: string;
  title: string;
  author?: string;
  bsr?: number;
  price?: number;
  rating?: number;
  review_count?: number;
  category?: string;
  image_url?: string;
  estimated_monthly_revenue?: number;
  bsr_change?: number;
  publish_date?: string;
  page_count?: number;
  description?: string;
  keywords_extracted?: string[];
  tracked?: boolean;
  project_id?: string;
}

export interface CompetitorAnalysis {
  id: string;
  org_id: string;
  book_id: string;
  status: AnalysisStatus;
  overall_score?: number;
  sentiment_score?: number;
  weakness_count: number;
  strength_count: number;
  review_summary?: string;
  positioning_analysis?: Record<string, unknown>;
  metadata_json?: Record<string, unknown>;
  completed_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface CompetitorAnalysisDetail extends CompetitorAnalysis {
  weaknesses: WeaknessSignal[];
  opportunity?: OpportunityBlueprint;
  book?: CompetitorBookBrief;
}

// ---------------------------------------------------------------------------
// Gap Analysis
// ---------------------------------------------------------------------------

export interface CoverGap {
  gap_type: string;
  description: string;
  prevalence: number;
  opportunity?: string;
}

export interface TitleGap {
  gap_type: string;
  description: string;
  missing_keywords: string[];
  opportunity?: string;
}

export interface ContentGap {
  topic: string;
  description: string;
  demand_signal?: string;
  competitor_coverage: number;
}

export interface GapAnalysis {
  id: string;
  org_id: string;
  niche: string;
  category?: string;
  books_analyzed: number;
  cover_gaps?: CoverGap[];
  title_gaps?: TitleGap[];
  content_gaps?: ContentGap[];
  weakness_signals?: WeaknessSignalGroup[];
  opportunity_blueprint?: OpportunityBlueprint;
  differentiation_score?: number;
  total_signals?: number;
  summary?: string;
  recommendations?: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WeaknessSignalGroup {
  category: string;
  label: string;
  count: number;
  signals: string[];
  book_sources: string[];
}

// ---------------------------------------------------------------------------
// Competitor Alerts
// ---------------------------------------------------------------------------

export interface CompetitorAlert {
  id: string;
  org_id: string;
  book_id?: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  name?: string;
  description?: string;
  config?: Record<string, unknown>;
  delivery_channels?: string[];
  check_frequency?: string;
  active?: boolean;
  data?: Record<string, unknown>;
  read: boolean;
  dismissed: boolean;
  last_checked_at?: string;
  last_triggered_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AlertEvent {
  id: string;
  alert_id: string;
  event_data: Record<string, unknown>;
  read: boolean;
  delivered_channels: string[];
  created_at: string;
  message?: string;
}

export interface CreateAlertRequest {
  alert_type: AlertType;
  name: string;
  config: Record<string, unknown>;
  delivery_channels: string[];
  check_frequency?: string;
  active?: boolean;
}

// ---------------------------------------------------------------------------
// Compare
// ---------------------------------------------------------------------------

export interface ComparisonBook {
  id?: string;
  title: string;
  author?: string;
  bsr?: number;
  price?: number;
  pages?: number;
  reviews_count?: number;
  rating?: number;
  publish_date?: string;
  features?: Record<string, boolean>;
  strengths?: string[];
  weaknesses?: string[];
  is_user_book?: boolean;
}

export interface ComparisonResult {
  books: ComparisonBook[];
  feature_list: string[];
  strategy?: string;
}

// ---------------------------------------------------------------------------
// Request/Response types
// ---------------------------------------------------------------------------

export interface CompetitorAnalyzeRequest {
  book_id: string;
  include_opportunity?: boolean;
  max_reviews?: number;
}

export interface BatchAnalyzeRequest {
  category: string;
  top_n?: number;
  include_opportunity?: boolean;
}

export interface BatchAnalyzeResponse {
  task_id: string;
  analyses_created: number;
  book_ids: string[];
  message: string;
}

export interface GapAnalysisRequest {
  niche: string;
  category?: string;
  book_ids?: string[];
  max_books?: number;
  competitor_ids?: string[];
  project_id?: string;
}

export interface AddCompetitorRequest {
  identifier: string;
  type: "asin" | "url" | "title";
  project_id?: string;
}
