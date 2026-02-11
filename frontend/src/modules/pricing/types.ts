export enum PricingStrategyType {
  COMPETITIVE_MATCH = "competitive_match",
  VALUE_BASED = "value_based",
  PENETRATION = "penetration",
  DYNAMIC = "dynamic",
  PROMOTIONAL = "promotional",
}

export enum RuleStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  PAUSED = "paused",
  ARCHIVED = "archived",
}

export enum BookFormat {
  EBOOK = "ebook",
  PAPERBACK = "paperback",
  HARDCOVER = "hardcover",
  AUDIOBOOK = "audiobook",
}

export interface PricePoint {
  price: number;
  estimated_daily_sales: number;
  estimated_daily_revenue: number;
  estimated_monthly_revenue: number;
  royalty_rate: number;
  estimated_daily_royalties: number;
  estimated_monthly_royalties: number;
}

export interface PriceSimulationRequest {
  book_id?: string;
  current_price: number;
  proposed_price: number;
  book_format?: BookFormat;
  current_daily_sales: number;
  elasticity?: number;
  royalty_rate?: number;
}

export interface PriceSimulationResponse {
  book_id?: string;
  current_price: number;
  proposed_price: number;
  price_change_pct: number;
  book_format: BookFormat;
  elasticity: number;
  current_metrics: PricePoint;
  proposed_metrics: PricePoint;
  revenue_change_pct: number;
  royalty_change_pct: number;
  breakeven_sales: number;
  recommended_price_points: PricePoint[];
}

export interface KUCalculatorRequest {
  book_page_count: number;
  estimated_ku_reads_per_month: number;
  ku_page_rate?: number;
  wide_price: number;
  wide_monthly_sales: number;
  wide_royalty_rate?: number;
  amazon_price: number;
  amazon_monthly_sales: number;
  amazon_royalty_rate?: number;
}

export interface RevenueBreakdown {
  source: string;
  monthly_revenue: number;
  monthly_royalties: number;
  annual_revenue: number;
  annual_royalties: number;
}

export interface KUCalculatorResponse {
  ku_exclusive: RevenueBreakdown;
  wide_distribution: RevenueBreakdown;
  difference_monthly: number;
  difference_annual: number;
  recommendation: string;
  details: Record<string, unknown>;
}

export interface PricingRule {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  book_id?: string;
  strategy: PricingStrategyType;
  status: RuleStatus;
  book_format: BookFormat;
  min_price: number;
  max_price: number;
  target_price?: number;
  parameters: Record<string, unknown>;
  is_auto_apply: boolean;
  last_applied_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CompetitorPriceEntry {
  id: string;
  book_id: string;
  competitor_asin?: string;
  competitor_title: string;
  competitor_author?: string;
  book_format: BookFormat;
  price: number;
  currency: string;
  bsr_rank?: number;
  review_count?: number;
  review_rating?: number;
  category?: string;
  snapshot_date: string;
  source: string;
}

export interface CompetitorPriceSummary {
  book_id: string;
  book_format: BookFormat;
  total_competitors: number;
  avg_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  price_percentile_25: number;
  price_percentile_75: number;
  avg_bsr?: number;
  avg_review_rating?: number;
  competitors: CompetitorPriceEntry[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  has_more: boolean;
}
