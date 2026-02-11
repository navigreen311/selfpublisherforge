/**
 * Type definitions for the Market Intelligence module.
 */

export interface CategoryNode {
  id: string;
  name: string;
  parent_id: string | null;
  children: CategoryNode[];
  book_count: number | null;
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
  bsr_distribution: Record<string, number>;
  top_books: CompetitorSummary[];
}

export interface KeywordData {
  keyword: string;
  search_volume: number;
  competition: number;
  cpc: number;
  trend: "up" | "down" | "stable";
  trend_data: number[];
  relevance_score: number;
}

export interface KeywordResearchResponse {
  keywords: KeywordData[];
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

export interface MarketTrendsResponse {
  trends: MarketTrend[];
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
