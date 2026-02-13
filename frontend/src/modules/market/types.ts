/**
 * Type definitions for the Market Intelligence module.
 */

export interface CategoryNode {
  id: string;
  name: string;
  parent_id: string | null;
  children: CategoryNode[];
  book_count: number | null;
  children_count?: number;
}

export interface CategoryAnalysis {
  category_id: string;
  category_name: string;
  book_count: number;
  avg_bsr: number;
  median_bsr: number;
  avg_price: number;
  avg_reviews: number;
  avg_rating: number;
  competition_score: number;
  saturation_score?: number;
  opportunity_score?: number;
  bsr_distribution: Record<string, number>;
  top_books: CompetitorSummary[];
  top_bsr?: number;
  new_books_30d?: number;
  avg_pub_date?: string;
}

export interface CategoryMetrics {
  total_books: number;
  avg_bsr: number;
  avg_price: number;
  avg_reviews: number;
  top_bsr: number;
  new_books_30d: number;
  avg_pub_date: string;
  competition_score: number;
  saturation_score: number;
  opportunity_score: number;
}

export interface KeywordData {
  keyword: string;
  search_volume: number;
  competition: number;
  competition_level?: "low" | "medium" | "high";
  cpc: number;
  opportunity_score?: number;
  trend: "up" | "down" | "stable";
  trend_data: number[];
  relevance_score: number;
}

export interface KeywordResearchResponse {
  keywords: KeywordData[];
  suggested_kdp_keywords?: string[];
  total_results?: number;
  marketplace: string;
  generated_at: string;
}

export interface CompetitorSummary {
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  image_url: string | null;
  estimated_revenue?: number | null;
  bsr_trend?: "up" | "down" | "stable";
  bsr_change?: number;
  publish_date?: string;
  page_count?: number;
  kindle_price?: number | null;
  paperback_price?: number | null;
  categories?: string[];
  description?: string;
  keywords?: string[];
}

export interface BSRHistoryPoint {
  date: string;
  bsr: number;
  price: number | null;
}

export interface CompetitorDetail {
  id: string;
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  image_url: string | null;
  category: string | null;
  marketplace: string;
  bsr_history: BSRHistoryPoint[];
  tracked_since: string;
  last_updated: string | null;
  description?: string;
  page_count?: number;
  publish_date?: string;
  estimated_monthly_revenue?: number;
  keywords_extracted?: string[];
  cover_image_url?: string;
}

export interface CompetitorListItem {
  id: string;
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  reviews_count: number;
  rating: number | null;
  marketplace: string;
  tracked_since: string;
  image_url?: string | null;
  estimated_monthly_revenue?: number | null;
  bsr_change?: number;
  publish_date?: string;
  project_id?: string;
}

export interface GapAnalysisItem {
  area: string;
  description: string;
  opportunity_level: string;
}

export interface NicheAnalysisResponse {
  niche: string;
  demand_score: number;
  supply_score: number;
  opportunity_score: number;
  top_competitors: CompetitorSummary[];
  gap_analysis: GapAnalysisItem[];
  avg_monthly_revenue: number | null;
  avg_bsr: number | null;
  recommendation: string;
  analyzed_at: string;
  charts_data?: ChartsData;
  ai_summary?: string;
  total_books?: number;
}

export interface ChartsData {
  bsr_distribution: { range: string; count: number }[];
  price_distribution: { range: string; count: number }[];
  review_distribution: { range: string; count: number }[];
}

export interface TrendDataPoint {
  date: string;
  value: number;
}

export interface MarketTrend {
  label: string;
  category_id: string | null;
  keyword: string | null;
  direction: "up" | "down" | "stable";
  data_points: TrendDataPoint[];
  change_pct: number;
}

export interface TrendingTopic {
  topic: string;
  change_pct: number;
  direction: "up" | "down";
}

export interface MarketTrendsResponse {
  trends: MarketTrend[];
  trending_up?: TrendingTopic[];
  trending_down?: TrendingTopic[];
  period_start: string;
  period_end: string;
}

export interface MarketSnapshot {
  id: string;
  category_id: string;
  category_name: string;
  snapshot_date: string;
  avg_bsr: number;
  avg_price: number;
  book_count: number;
  avg_reviews: number;
  competition_score: number;
}

export interface AIMarketSummaryData {
  summary: string;
  content_gaps: string[];
  positioning: string;
  price_recommendation: string;
  category_recommendation: string[];
}

export interface SavedSearch {
  id: string;
  query: string;
  created_at: string;
  opportunity_score?: number;
}
