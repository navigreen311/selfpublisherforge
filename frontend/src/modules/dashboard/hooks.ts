"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types (mirror backend/app/modules/dashboard/schemas.py)
// ---------------------------------------------------------------------------

export interface DashboardStats {
  total_projects: number;
  in_progress: number;
  published: number;
  monthly_revenue: number | string;
}

export interface RevenuePoint {
  date: string;
  amount: number | string;
}

export interface ActivePipelineItem {
  id: string;
  title: string;
  stage: string | null;
  progress_pct: number;
  due_date: string | null;
}

export interface RecentActivityItem {
  id: string;
  action: string;
  description: string | null;
  resource_type: string | null;
  resource_id: string | null;
  created_at: string;
}

export interface AIInsight {
  id: string;
  type: string;
  message: string;
  action_url: string | null;
  priority: "info" | "warning" | "success" | string;
}

export interface UpcomingDeadline {
  id: string;
  title: string;
  date: string;
  source_type: string;
  source_id: string;
}

export interface DashboardResponseV2 {
  stats: DashboardStats;
  revenue_trend: RevenuePoint[];
  active_pipelines: ActivePipelineItem[];
  recent_activity: RecentActivityItem[];
  ai_insights: AIInsight[];
  upcoming_deadlines: UpcomingDeadline[];
}

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const dashboardKeys = {
  all: ["dashboard-v2"] as const,
  aggregate: () => [...dashboardKeys.all, "aggregate"] as const,
};

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/**
 * useDashboardAggregate -- calls GET /api/v1/dashboard (Phase 2.1).
 *
 * Returns stats + revenue_trend + active_pipelines + recent_activity
 * + ai_insights + upcoming_deadlines aggregated for the current org.
 */
export function useDashboardAggregate() {
  return useQuery<DashboardResponseV2>({
    queryKey: dashboardKeys.aggregate(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/dashboard");
      return data;
    },
    staleTime: 60_000,
  });
}
