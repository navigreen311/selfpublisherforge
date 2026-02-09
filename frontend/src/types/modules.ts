/**
 * TypeScript interfaces for each module's domain data types.
 *
 * These mirror the backend SQLAlchemy / Pydantic models and are used by
 * React components and hooks throughout the frontend.
 */

import type {
  AgentType,
  BookFormat,
  BookStatus,
  CampaignStatus,
  OrgScoped,
  PlanTier,
  ProjectType,
  StatusEnum,
  TimestampMixin,
  UserRole,
} from "./api";

// ---------------------------------------------------------------------------
// Auth / Users (modules 1-2)
// ---------------------------------------------------------------------------

export interface User extends TimestampMixin {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  role: UserRole;
  org_id: string;
  is_active: boolean;
  last_login_at: string | null;
}

export interface Organization extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  slug: string;
  plan_tier: PlanTier;
  owner_id: string;
  member_count: number;
  storage_used_bytes: number;
  storage_limit_bytes: number;
}

export interface OrgInvite extends TimestampMixin {
  id: string;
  org_id: string;
  email: string;
  role: UserRole;
  invited_by: string;
  accepted_at: string | null;
  expires_at: string;
}

// ---------------------------------------------------------------------------
// Projects / Books (modules 3-4)
// ---------------------------------------------------------------------------

export interface Project extends TimestampMixin, OrgScoped {
  id: string;
  title: string;
  description: string | null;
  type: ProjectType;
  status: StatusEnum;
  owner_id: string;
  book_count: number;
}

export interface Book extends TimestampMixin, OrgScoped {
  id: string;
  project_id: string;
  title: string;
  subtitle: string | null;
  isbn: string | null;
  asin: string | null;
  format: BookFormat;
  status: BookStatus;
  word_count: number;
  page_count: number | null;
  language: string;
  cover_image_url: string | null;
}

export interface Chapter extends TimestampMixin {
  id: string;
  book_id: string;
  title: string;
  order: number;
  word_count: number;
  status: StatusEnum;
}

// ---------------------------------------------------------------------------
// Market Research (modules 5-6)
// ---------------------------------------------------------------------------

export interface MarketData extends TimestampMixin, OrgScoped {
  id: string;
  category: string;
  subcategory: string | null;
  marketplace: string;
  avg_bsr: number | null;
  avg_price: number | null;
  avg_reviews: number | null;
  competition_score: number | null;
  demand_score: number | null;
  opportunity_score: number | null;
  snapshot_date: string;
}

export interface KeywordData extends TimestampMixin {
  id: string;
  keyword: string;
  search_volume: number | null;
  competition: number | null;
  relevance_score: number | null;
  marketplace: string;
}

export interface CompetitorBook extends TimestampMixin {
  id: string;
  asin: string;
  title: string;
  author: string;
  bsr: number | null;
  price: number | null;
  review_count: number | null;
  avg_rating: number | null;
  category: string;
  marketplace: string;
}

// ---------------------------------------------------------------------------
// Style / Branding (modules 7-8)
// ---------------------------------------------------------------------------

export interface StyleProfile extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  description: string | null;
  tone: string;
  voice: string;
  target_audience: string;
  genre: string;
  style_rules: Record<string, unknown>;
  is_default: boolean;
}

export interface BrandKit extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_heading: string;
  font_body: string;
  logo_url: string | null;
}

// ---------------------------------------------------------------------------
// AI Content Generation (modules 9-12)
// ---------------------------------------------------------------------------

export interface GenerationJob extends TimestampMixin, OrgScoped {
  id: string;
  book_id: string | null;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  prompt: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost_cents: number;
  result_url: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ContentTemplate extends TimestampMixin {
  id: string;
  name: string;
  description: string | null;
  type: string;
  template_body: string;
  variables: string[];
  is_system: boolean;
}

// ---------------------------------------------------------------------------
// Publishing / Distribution (modules 13-15)
// ---------------------------------------------------------------------------

export interface PublishingAccount extends TimestampMixin, OrgScoped {
  id: string;
  platform: "kdp" | "ingramspark" | "draft2digital" | "smashwords" | "acx";
  account_name: string;
  is_connected: boolean;
  last_synced_at: string | null;
}

export interface BookListing extends TimestampMixin {
  id: string;
  book_id: string;
  platform: string;
  platform_id: string | null;
  status: "draft" | "pending" | "live" | "suspended" | "removed";
  listing_url: string | null;
  price: number | null;
  currency: string;
  last_synced_at: string | null;
}

export interface ValidationResult extends TimestampMixin {
  id: string;
  book_id: string;
  platform: string;
  is_valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
}

export interface ValidationIssue {
  code: string;
  message: string;
  field: string | null;
  severity: "error" | "warning" | "info";
}

// ---------------------------------------------------------------------------
// Marketing / Campaigns (modules 16-18)
// ---------------------------------------------------------------------------

export interface Campaign extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  description: string | null;
  book_id: string | null;
  status: CampaignStatus;
  start_date: string | null;
  end_date: string | null;
  budget_cents: number | null;
  spent_cents: number;
  channel: "email" | "social" | "ads" | "cross_promo";
}

export interface SocialPost extends TimestampMixin {
  id: string;
  campaign_id: string;
  platform: "twitter" | "facebook" | "instagram" | "tiktok" | "linkedin";
  content: string;
  media_urls: string[];
  scheduled_at: string | null;
  published_at: string | null;
  status: "draft" | "scheduled" | "published" | "failed";
  engagement: SocialEngagement | null;
}

export interface SocialEngagement {
  likes: number;
  shares: number;
  comments: number;
  clicks: number;
  impressions: number;
}

export interface EmailCampaign extends TimestampMixin {
  id: string;
  campaign_id: string;
  subject: string;
  body_html: string;
  recipient_count: number;
  sent_count: number;
  open_count: number;
  click_count: number;
  status: "draft" | "scheduled" | "sending" | "sent" | "failed";
  scheduled_at: string | null;
  sent_at: string | null;
}

// ---------------------------------------------------------------------------
// Agents (modules 19-21)
// ---------------------------------------------------------------------------

export interface Agent extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  type: AgentType;
  description: string | null;
  model: string;
  system_prompt: string;
  is_active: boolean;
  max_budget_cents: number;
  spent_cents: number;
  success_rate: number | null;
  total_tasks: number;
}

export interface AgentTask extends TimestampMixin {
  id: string;
  agent_id: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  cost_cents: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface AgentConversation extends TimestampMixin {
  id: string;
  agent_id: string;
  user_id: string;
  title: string | null;
  messages: AgentMessage[];
}

export interface AgentMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tokens_used: number | null;
}

// ---------------------------------------------------------------------------
// Analytics / Reporting (modules 22-24)
// ---------------------------------------------------------------------------

export interface SalesMetric extends TimestampMixin {
  id: string;
  book_id: string;
  platform: string;
  date: string;
  units_sold: number;
  revenue_cents: number;
  pages_read: number;
  kenp_royalty_cents: number;
}

export interface DashboardWidget {
  id: string;
  type: "chart" | "stat" | "table" | "list";
  title: string;
  config: Record<string, unknown>;
  position: { x: number; y: number; w: number; h: number };
}

export interface Report extends TimestampMixin, OrgScoped {
  id: string;
  name: string;
  type: "sales" | "royalties" | "marketing" | "agent_performance" | "custom";
  parameters: Record<string, unknown>;
  status: "pending" | "generating" | "ready" | "failed";
  download_url: string | null;
  generated_at: string | null;
}

// ---------------------------------------------------------------------------
// Notifications / Settings (modules 25-27)
// ---------------------------------------------------------------------------

export interface Notification extends TimestampMixin {
  id: string;
  user_id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  is_read: boolean;
  action_url: string | null;
  source_module: string | null;
}

export interface UserPreferences {
  user_id: string;
  theme: "light" | "dark" | "system";
  language: string;
  timezone: string;
  email_notifications: boolean;
  push_notifications: boolean;
  digest_frequency: "realtime" | "daily" | "weekly" | "none";
}

// ---------------------------------------------------------------------------
// Billing / Subscription (modules 28-29)
// ---------------------------------------------------------------------------

export interface Subscription extends TimestampMixin, OrgScoped {
  id: string;
  plan_tier: PlanTier;
  status: "active" | "trialing" | "past_due" | "cancelled" | "expired";
  stripe_subscription_id: string | null;
  current_period_start: string;
  current_period_end: string;
  cancel_at: string | null;
}

export interface Invoice extends TimestampMixin {
  id: string;
  org_id: string;
  stripe_invoice_id: string;
  amount_cents: number;
  currency: string;
  status: "draft" | "open" | "paid" | "void" | "uncollectible";
  invoice_url: string | null;
  paid_at: string | null;
}

export interface UsageRecord extends TimestampMixin {
  id: string;
  org_id: string;
  metric: "ai_tokens" | "storage_bytes" | "api_calls" | "agent_tasks";
  quantity: number;
  period_start: string;
  period_end: string;
}
