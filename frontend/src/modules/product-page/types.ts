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
// Extended types for enhanced Product Page Lab
// ---------------------------------------------------------------------------

export interface ListingScore {
  dimension: string;
  score: number;
  color: "green" | "yellow" | "red";
}

export interface ListingFinding {
  type: "good" | "warning" | "problem";
  message: string;
}

export interface ListingSuggestion {
  dimension: string;
  current: string;
  suggested: string;
}

export interface ListingAnalysisResult {
  id: string;
  overall_score: number;
  scores: Record<string, ListingScore>;
  findings: Record<string, ListingFinding[]>;
  suggestions: Record<string, ListingSuggestion>;
  created_at: string;
}

export interface MobileIssue {
  area: string;
  severity: "critical" | "warning" | "info";
  message: string;
  suggestion: string;
}

export interface BlurbVersion {
  style: string;
  html_content: string;
  plain_content: string;
  score: number;
}

export type BlurbStyle = "story_led" | "benefit_led" | "problem_solution";

export interface KeywordRecommendation {
  keyword: string;
  search_vol: number;
  competition: "low" | "medium" | "high";
  relevance: number;
}

export interface OptimizeKeywordsRequest {
  book_id?: string;
  current_keywords: string[];
  genre: string;
  title: string;
}

export interface OptimizeKeywordsResponse {
  recommended: KeywordRecommendation[];
  optimal_seven: string[];
}

export interface APlusModule {
  type: string;
  title: string;
  content: string;
  image_spec: { width: number; height: number };
  ai_copy: string;
}

export interface APlusPlanResponse {
  id: string;
  modules: APlusModule[];
  status: string;
  created_at: string;
}
