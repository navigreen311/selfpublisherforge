/**
 * React Query hooks for the Marketing & Launch Command module.
 *
 * Response conventions:
 *   - Single-item endpoints return SuccessResponse<T> = { data: T }   -> use `resp.data.data`
 *   - Paginated endpoints return PaginatedResponse<T> = { items, … }  -> use `resp.data`
 *   - Direct-shape endpoints (e.g. SocialCalendar)                    -> use `resp.data`
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SuccessResponse } from "@/types/api";

const MARKETING_KEYS = {
  launchPlans: ["marketing", "launch-plans"] as const,
  launchPlan: (id: string) => ["marketing", "launch-plans", id] as const,
  emailSequences: ["marketing", "email-sequences"] as const,
  emailSequence: (id: string) => ["marketing", "email-sequences", id] as const,
  socialCalendar: ["marketing", "social", "calendar"] as const,
  arcCampaigns: ["marketing", "arc"] as const,
  arcCampaign: (id: string) => ["marketing", "arc", id] as const,
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Launch Plan Hooks
// ---------------------------------------------------------------------------

export function useLaunchPlans(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...MARKETING_KEYS.launchPlans, params],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/marketing/launch-plans", { params });
      return data as { items: LaunchPlan[]; total_count: number; has_more: boolean };
    },
  });
}

export function useLaunchPlan(id: string) {
  return useQuery({
    queryKey: MARKETING_KEYS.launchPlan(id),
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<LaunchPlan>>(`/api/v1/marketing/launch-plans/${id}`);
      return data.data;
    },
    enabled: !!id,
  });
}

export function useGenerateLaunchPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: GenerateLaunchPlanRequest) => {
      const { data } = await api.post<SuccessResponse<LaunchPlan>>("/api/v1/marketing/launch-plan/generate", request);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.launchPlans });
    },
  });
}

export function useUpdateLaunchPlan(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Partial<LaunchPlan>) => {
      const { data } = await api.patch<SuccessResponse<LaunchPlan>>(`/api/v1/marketing/launch-plans/${id}`, updates);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.launchPlan(id) });
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.launchPlans });
    },
  });
}

// ---------------------------------------------------------------------------
// Email Sequence Hooks
// ---------------------------------------------------------------------------

export function useEmailSequences(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...MARKETING_KEYS.emailSequences, params],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/marketing/email-sequences", { params });
      return data as { items: EmailSequence[]; total_count: number; has_more: boolean };
    },
  });
}

export function useCreateEmailSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sequence: Partial<EmailSequence>) => {
      const { data } = await api.post<SuccessResponse<EmailSequence>>("/api/v1/marketing/email-sequences", sequence);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.emailSequences });
    },
  });
}

export function useUpdateEmailSequence(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Partial<EmailSequence>) => {
      const { data } = await api.patch<SuccessResponse<EmailSequence>>(`/api/v1/marketing/email-sequences/${id}`, updates);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.emailSequences });
    },
  });
}

export function useTriggerEmailSend(sequenceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { recipient_emails: string[]; personalization?: Record<string, string> }) => {
      const { data } = await api.post<SuccessResponse<EmailSequence>>(`/api/v1/marketing/email-sequences/${sequenceId}/send`, payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.emailSequences });
    },
  });
}

// ---------------------------------------------------------------------------
// Social Media Hooks
// ---------------------------------------------------------------------------

export function useSocialCalendar(params?: { start_date?: string; end_date?: string; platform?: string }) {
  return useQuery({
    queryKey: [...MARKETING_KEYS.socialCalendar, params],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/marketing/social/calendar", { params });
      return data as SocialCalendar;
    },
  });
}

export function useGenerateSocialContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: GenerateSocialContentRequest) => {
      const { data } = await api.post<SuccessResponse<SocialPost[]>>("/api/v1/marketing/social/generate", request);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.socialCalendar });
    },
  });
}

// ---------------------------------------------------------------------------
// ARC Campaign Hooks
// ---------------------------------------------------------------------------

export function useARCCampaigns(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...MARKETING_KEYS.arcCampaigns, params],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/marketing/arc", { params });
      return data as { items: ARCCampaign[]; total_count: number; has_more: boolean };
    },
  });
}

export function useCreateARCCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (campaign: Partial<ARCCampaign> & { book_id: string; recipients?: { name: string; email: string }[] }) => {
      const { data } = await api.post<SuccessResponse<ARCCampaign>>("/api/v1/marketing/arc", campaign);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.arcCampaigns });
    },
  });
}

export function useSendARCCopies(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { recipient_ids?: string[]; custom_message?: string }) => {
      const { data } = await api.post<SuccessResponse<ARCCampaign>>(`/api/v1/marketing/arc/${campaignId}/send`, payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MARKETING_KEYS.arcCampaigns });
    },
  });
}
