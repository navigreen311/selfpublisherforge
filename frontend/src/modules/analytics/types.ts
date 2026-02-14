/**
 * Type definitions for the Analytics module.
 */

export interface KPICard {
  label: string;
  value: string;
  change_percent: number | null;
  change_direction: string | null;
  period: string;
}

export interface RevenueDataPoint {
  period: string;
  revenue: number;
  units: number;
  platform?: string;
  book_title?: string;
}

export interface RoyaltyRecord {
  id: string;
  org_id: string;
  book_id: string | null;
  platform: string;
  marketplace: string;
  title: string;
  asin: string | null;
  isbn: string | null;
  format_type: string;
  units_sold: number;
  units_refunded: number;
  net_units: number;
  list_price: number;
  royalty_rate: number;
  gross_revenue: number;
  net_revenue: number;
  currency: string;
  period_start: string;
  period_end: string;
  import_batch_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  kpis: KPICard[];
  revenue_chart: RevenueDataPoint[];
  top_books: Record<string, unknown>[];
  platform_breakdown: Record<string, number>;
  recent_royalties: RoyaltyRecord[];
  period_start: string;
  period_end: string;
}

export interface RevenueResponse {
  total_revenue: number;
  total_units: number;
  data_points: RevenueDataPoint[];
  period_start: string;
  period_end: string;
  aggregation: string;
  by_platform: Record<string, number>;
  by_book: Record<string, unknown>[];
}

export interface PortfolioMetrics {
  total_books: number;
  total_revenue: number;
  total_units_sold: number;
  total_expenses: number;
  net_profit: number;
  avg_roi: number;
  platform_breakdown: Record<string, unknown>;
  format_breakdown: Record<string, unknown>;
  top_books: Record<string, unknown>[];
  snapshot_date: string | null;
}

export interface ReportResponse {
  id: string;
  org_id: string;
  title: string;
  report_type: string;
  status: string;
  output_format: string;
  parameters: Record<string, unknown>;
  file_path: string | null;
  file_size: number | null;
  generated_by: string | null;
  generated_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrendData {
  metric: string;
  data_points: { period: string; value: number; label?: string }[];
  aggregation: string;
  period_start: string;
  period_end: string;
  total: number;
  average: number;
  change_percent: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface RoyaltyImportResponse {
  import_batch_id: string;
  records_imported: number;
  records_skipped: number;
  errors: string[];
  platform: string;
}

export interface ReportRequest {
  title: string;
  report_type: "revenue_summary" | "book_performance" | "marketing_roi" | "portfolio_overview" | "custom";
  output_format: "pdf" | "xlsx";
  parameters: Record<string, unknown>;
}

export interface RoyaltyImportRequest {
  platform: "kdp" | "ingram_spark" | "draft2digital" | "other";
  file_content: string;
  file_name?: string;
}

// Portfolio Economics Types

export interface BookSummary {
  book_id: string;
  title: string;
  genre: string;
  launch_date: string | null;
  monthly_revenue: number;
  monthly_units: number;
  total_revenue: number;
  roi: number;
  status: string;
}

export interface PortfolioOverview {
  org_id: string;
  total_books: number;
  active_books: number;
  total_revenue: number;
  total_investment: number;
  portfolio_roi: number;
  monthly_revenue: number;
  monthly_trend: number;
  top_performers: BookSummary[];
  underperformers: BookSummary[];
  genre_distribution: Record<string, number>;
  revenue_by_genre: Record<string, number>;
  updated_at: string;
}

export interface GreenlightRequest {
  title: string;
  genre: string;
  sub_genre?: string;
  estimated_word_count?: number;
  estimated_price?: number;
  royalty_rate?: number;
  estimated_production_cost?: number;
  estimated_marketing_budget?: number;
  is_series?: boolean;
  series_position?: number;
  comparable_asins?: string[];
  market_size_estimate?: number;
}

export interface GreenlightResult {
  title: string;
  genre: string;
  greenlight_score: number;
  recommendation: string;
  confidence: string;
  estimated_market_size: number;
  estimated_capture_rate: number;
  projected_monthly_units: number;
  projected_monthly_revenue: number;
  projected_monthly_royalty: number;
  total_investment: number;
  breakeven_months: number | null;
  first_year_roi: number;
  first_year_profit: number;
  risk_factors: string[];
  opportunity_factors: string[];
  suggestions: string[];
  calculated_at: string;
}

export interface AudiencePersona {
  persona_id: string;
  book_id: string;
  name: string;
  description: string;
  age_range: string;
  gender_skew: string;
  reading_frequency: string;
  preferred_formats: string[];
  price_sensitivity: string;
  discovery_channels: string[];
  motivations: string[];
  pain_points: string[];
  favorite_authors: string[];
  percentage_of_audience: number;
  created_at: string;
}

export interface AlsoBoughtItem {
  asin: string;
  title: string;
  author: string;
  genre: string;
  price: number;
  rating: number;
  review_count: number;
  overlap_score: number;
}

export interface AlsoBoughtIntelligence {
  book_id: string;
  also_bought: AlsoBoughtItem[];
  common_genres: string[];
  average_price: number;
  average_rating: number;
  audience_insights: string[];
  positioning_suggestions: string[];
  analyzed_at: string;
}

export interface SeasonalEvent {
  event_id: string;
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  genres_affected: string[];
  impact_level: string;
  demand_multiplier: number;
  recommendations: string[];
  is_recurring: boolean;
}

export interface NicheSeasonality {
  genre: string;
  monthly_demand: Record<string, number>;
  peak_months: string[];
  low_months: string[];
  seasonal_events: SeasonalEvent[];
  best_launch_windows: Array<{ start_month: string; end_month: string; reason: string }>;
  avoid_windows: Array<{ start_month: string; end_month: string; reason: string }>;
}

export interface LaunchRecommendation {
  recommended_date: string;
  alternative_dates: string[];
  season_type: string;
  demand_index: number;
  confidence: string;
  reasoning: string[];
  competing_events: string[];
  favorable_events: string[];
  pre_launch_checklist: Array<{ days_before: number; action: string; description: string }>;
  marketing_timeline: Array<{ date: string; action: string; channel: string }>;
  calculated_at: string;
}

// --- Enhanced Analytics types ---

export interface DailySalesRow {
  date: string;
  kindle: number;
  print: number;
  audio: number;
  kenp: number;
  revenue: number;
  royalties: number;
}

export interface SalesResponse {
  daily_data: DailySalesRow[];
  totals: {
    units: number;
    revenue: number;
    royalties: number;
  };
  by_marketplace: Array<{
    marketplace: string;
    revenue: number;
    units: number;
    percentage?: number;
  }>;
}

export interface BSRDataPoint {
  recorded_at: string;
  bsr: number;
  category_rank?: number;
  category_name?: string;
}

export interface BookPerformanceData {
  book_id: string;
  stats: {
    bsr: number;
    bsr_change: number;
    monthly_revenue: number;
    avg_daily_sales: number;
    reviews: number;
    avg_rating: number;
    new_reviews_month: number;
  };
  bsr_history: BSRDataPoint[];
  revenue_breakdown: Array<{
    format: string;
    revenue: number;
    percentage: number;
  }>;
}

export interface EnhancedDashboardData {
  stats: Array<{
    label: string;
    value: string;
    change_percent: number;
    change_direction: "up" | "down" | "flat";
  }>;
  trend_data: Array<{
    date: string;
    revenue: number;
    units: number;
    royalties: number;
    kenp: number;
  }>;
  revenue_by_book: Array<{
    book_title: string;
    revenue: number;
    percentage: number;
  }>;
  revenue_by_format: Array<{
    format: string;
    revenue: number;
    percentage: number;
  }>;
  insights: Array<{
    type: string;
    message: string;
    book_id?: string;
    severity: "info" | "warning" | "success";
  }>;
  period: string;
}

export interface EnhancedReportRequest {
  title: string;
  report_type: string;
  period_start?: string;
  period_end?: string;
  book_ids?: string[];
  format: "pdf" | "xlsx" | "csv";
  sections?: string[];
}
