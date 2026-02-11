/**
 * React Query hooks for the Marketing & Launch Command module.
 *
 * Response conventions:
 *   - Single-item endpoints return SuccessResponse<T> = { data: T }   -> use `resp.data.data`
 *   - Paginated endpoints return PaginatedResponse<T> = { items, … }  -> use `resp.data`
 *   - Direct-shape endpoints (e.g. SocialCalendar)                    -> use `resp.data`
 */

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type { SuccessResponse } from "@/types/api";
import type {
  LaunchPlan,
  LaunchPhase,
  PhaseTask,
  EmailSequence,
  EmailTemplate,
  SocialPost,
  SocialCalendar,
  ARCCampaign,
  ARCRecipient,
  GenerateLaunchPlanRequest,
  GenerateSocialContentRequest,
  RecentActivityItem,
} from "./types";

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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
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
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Recent Activity (derived from existing marketing data)
// ---------------------------------------------------------------------------

/**
 * Derives a recent-activity feed from the existing marketing data queries.
 * Combines launch plans, email sequences, ARC campaigns, and social posts,
 * then sorts by most recent timestamp.
 */
export function useRecentActivity(limit = 8) {
  const { data: plans, isLoading: plansLoading } = useLaunchPlans({ limit: 10 });
  const { data: sequences, isLoading: seqLoading } = useEmailSequences({ limit: 10 });
  const { data: arc, isLoading: arcLoading } = useARCCampaigns({ limit: 10 });
  const { data: social, isLoading: socialLoading } = useSocialCalendar();

  const isLoading = plansLoading || seqLoading || arcLoading || socialLoading;

  const items: RecentActivityItem[] = useMemo(() => {
    const activities: RecentActivityItem[] = [];

    // Launch plans
    for (const plan of plans?.items ?? []) {
      const action =
        plan.status === "draft"
          ? "Plan created"
          : plan.status === "active"
            ? "Plan activated"
            : plan.status === "completed"
              ? "Plan completed"
              : "Plan updated";
      activities.push({
        id: `lp-${plan.id}`,
        type: "launch_plan",
        action,
        title: plan.title,
        timestamp: plan.updated_at,
      });
    }

    // Email sequences
    for (const seq of sequences?.items ?? []) {
      const action =
        seq.sent_count > 0
          ? `Email sent (${seq.sent_count}/${seq.recipient_count})`
          : seq.status === "draft"
            ? "Sequence created"
            : "Sequence updated";
      activities.push({
        id: `es-${seq.id}`,
        type: "email_sequence",
        action,
        title: seq.name,
        timestamp: seq.updated_at,
      });
    }

    // ARC campaigns
    for (const campaign of arc?.items ?? []) {
      const action =
        campaign.sent_copies > 0
          ? `ARC copies sent (${campaign.sent_copies}/${campaign.total_copies})`
          : campaign.status === "draft"
            ? "Campaign created"
            : "Campaign updated";
      activities.push({
        id: `arc-${campaign.id}`,
        type: "arc_campaign",
        action,
        title: campaign.name,
        timestamp: campaign.updated_at,
      });
    }

    // Social posts
    for (const post of social?.posts ?? []) {
      const action =
        post.status === "published"
          ? "Post published"
          : post.status === "scheduled"
            ? "Post scheduled"
            : "Post drafted";
      activities.push({
        id: `sp-${post.id}`,
        type: "social_post",
        action,
        title: post.content.slice(0, 60) + (post.content.length > 60 ? "..." : ""),
        timestamp: post.published_at || post.scheduled_at || post.updated_at,
      });
    }

    // Sort by timestamp descending
    activities.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return activities.slice(0, limit);
  }, [plans, sequences, arc, social, limit]);

  return { items, isLoading };
}
