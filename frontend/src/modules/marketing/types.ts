/**
 * Type definitions for the Marketing & Launch Command module.
 */

export interface LaunchPlan {
  id: string;
  org_id: string;
  book_id: string;
  title: string;
  description?: string;
  status: "draft" | "active" | "completed" | "archived";
  launch_date?: string;
  genre?: string;
  target_audience?: string;
  budget?: number;
  goals?: Record<string, unknown>;
  ai_metadata?: Record<string, unknown>;
  created_by: string;
  phases: LaunchPhase[];
  created_at: string;
  updated_at: string;
}

export interface LaunchPhase {
  id: string;
  launch_plan_id: string;
  phase_type: "pre_launch" | "launch_week" | "post_launch";
  name: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  order_index: number;
  tasks: PhaseTask[];
  created_at: string;
  updated_at: string;
}

export interface PhaseTask {
  id: string;
  phase_id: string;
  title: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "skipped";
  due_date?: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface EmailSequence {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  status: "draft" | "active" | "paused" | "completed" | "archived";
  trigger_event?: string;
  recipient_count: number;
  sent_count: number;
  open_rate?: number;
  click_rate?: number;
  emails: EmailTemplate[];
  created_at: string;
  updated_at: string;
}

export interface EmailTemplate {
  id: string;
  sequence_id: string;
  template_type: "welcome" | "launch_announcement" | "follow_up" | "review_request" | "custom";
  subject: string;
  body_html?: string;
  body_text?: string;
  delay_days: number;
  delay_hours: number;
  order_index: number;
  send_status: "pending" | "scheduled" | "sent" | "failed" | "bounced";
  scheduled_at?: string;
  sent_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SocialPost {
  id: string;
  org_id: string;
  platform: "twitter" | "facebook" | "instagram";
  content: string;
  hashtags?: string[];
  status: "draft" | "scheduled" | "published" | "failed";
  scheduled_at?: string;
  published_at?: string;
  engagement_metrics?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SocialCalendar {
  posts: SocialPost[];
  total_scheduled: number;
  total_published: number;
  total_draft: number;
  platforms: Record<string, number>;
}

export interface ARCCampaign {
  id: string;
  org_id: string;
  book_id: string;
  name: string;
  description?: string;
  status: "draft" | "active" | "sending" | "completed" | "archived";
  total_copies: number;
  sent_copies: number;
  reviews_received: number;
  deadline?: string;
  recipients: ARCRecipient[];
  created_at: string;
  updated_at: string;
}

export interface ARCRecipient {
  id: string;
  campaign_id: string;
  name: string;
  email: string;
  status: "pending" | "sent" | "delivered" | "reviewed" | "failed";
  sent_at?: string;
  review_url?: string;
  review_received_at?: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateLaunchPlanRequest {
  book_id: string;
  book_title: string;
  genre: string;
  target_audience: string;
  launch_date: string;
  budget?: number;
  goals?: string[];
  additional_context?: string;
}

export interface GenerateSocialContentRequest {
  book_title: string;
  genre: string;
  target_audience: string;
  book_description: string;
  platforms?: string[];
  tone?: string;
  num_posts_per_platform?: number;
  launch_plan_id?: string;
}

export interface RecentActivityItem {
  id: string;
  type: "launch_plan" | "email_sequence" | "arc_campaign" | "social_post";
  action: string;
  title: string;
  timestamp: string;
}
