/**
 * TypeScript types for Review Intelligence module.
 * Aligned with backend schemas from backend/app/modules/review_intelligence/schemas.py
 */

export enum SentimentLabel {
  POSITIVE = "positive",
  NEGATIVE = "negative",
  NEUTRAL = "neutral",
  MIXED = "mixed",
}

export enum AlertType {
  NEGATIVE_SPIKE = "negative_spike",
  VELOCITY_DROP = "velocity_drop",
  RATING_DECLINE = "rating_decline",
  COMPETITOR_SURGE = "competitor_surge",
}

export enum AlertSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum VelocityPeriod {
  DAILY = "daily",
  WEEKLY = "weekly",
  MONTHLY = "monthly",
}

export enum VelocityTrend {
  RISING = "rising",
  STABLE = "stable",
  DECLINING = "declining",
}

export enum ReviewSource {
  AMAZON = "amazon",
  GOODREADS = "goodreads",
  BOOKBUB = "bookbub",
  APPLE_BOOKS = "apple_books",
  BARNES_NOBLE = "barnes_noble",
  KOBO = "kobo",
  OTHER = "other",
}

export interface Review {
  id: string;
  org_id: string;
  book_id: string;
  source: ReviewSource;
  source_review_id: string | null;
  reviewer_name: string | null;
  reviewer_profile_url: string | null;
  star_rating: number;
  title: string | null;
  body: string | null;
  review_date: string | null;
  verified_purchase: boolean;
  helpful_count: number;
  is_competitor: boolean;
  sentiment: SentimentLabel | null;
  sentiment_score: number | null;
  themes: Record<string, unknown> | null;
  analyzed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ThemeItem {
  theme: string;
  count: number;
  sentiment: SentimentLabel;
  example_quotes: string[];
}

export interface SentimentBreakdown {
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  mixed_count: number;
  total_count: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  mixed_pct: number;
  avg_sentiment_score: number;
  themes: ThemeItem[];
}

export interface VelocityDataPoint {
  period_start: string;
  period_end: string;
  review_count: number;
  avg_rating: number | null;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
}

export interface VelocityReport {
  book_id: string;
  period: VelocityPeriod;
  data_points: VelocityDataPoint[];
  current_rate: number;
  previous_rate: number;
  change_pct: number;
  trend: VelocityTrend;
  anomalies: Record<string, unknown>[];
}

export interface ReviewAlert {
  id: string;
  org_id: string;
  book_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  data: Record<string, unknown> | null;
  is_acknowledged: boolean;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReputationHealthMetrics {
  book_id: string;
  overall_score: number;
  avg_rating: number;
  total_reviews: number;
  sentiment_ratio: number;
  velocity_trend: VelocityTrend;
  health_grade: string;
  rating_distribution: Record<string, number>;
  recent_trend: string;
  recommendations: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface ReviewListParams {
  cursor?: string;
  limit?: number;
  sentiment?: SentimentLabel;
  min_rating?: number;
  max_rating?: number;
  sort_by?: string;
  sort_dir?: string;
}

export interface AlertListParams {
  cursor?: string;
  limit?: number;
  alert_type?: AlertType;
  severity?: AlertSeverity;
  is_acknowledged?: boolean;
  book_id?: string;
}
