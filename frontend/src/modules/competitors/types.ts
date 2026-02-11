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
  | "coverage_gaps";

export type Severity = "low" | "medium" | "high" | "critical";

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";

export type AlertType = "price_change" | "bsr_shift" | "new_book" | "review_spike";

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
  summary?: string;
  recommendations?: string[];
  status: string;
  created_at: string;
  updated_at: string;
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
  description?: string;
  data?: Record<string, unknown>;
  read: boolean;
  dismissed: boolean;
  created_at: string;
  updated_at: string;
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
}
