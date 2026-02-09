"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export type PipelineStatus = "draft" | "active" | "paused" | "completed" | "cancelled";
export type TaskType = "writing" | "editing" | "proofreading" | "formatting" | "review";
export type TaskStatus = "pending" | "in_progress" | "blocked" | "completed" | "cancelled";

export interface PipelineTask {
  id: string;
  pipeline_id: string;
  org_id: string;
  title: string;
  description?: string | null;
  type: TaskType;
  status: TaskStatus;
  assignee_id?: string | null;
  due_date?: string | null;
  depends_on: string[];
  completed_at?: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  id: string;
  org_id: string;
  book_id: string;
  name: string;
  description?: string | null;
  status: PipelineStatus;
  settings: Record<string, unknown>;
  deadline?: string | null;
  tasks: PipelineTask[];
  created_at: string;
  updated_at: string;
}

export interface PipelineSummary {
  id: string;
  org_id: string;
  book_id: string;
  name: string;
  status: PipelineStatus;
  deadline?: string | null;
  task_count: number;
  completed_task_count: number;
  overdue_task_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedPipelines {
  items: PipelineSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TimelineTask {
  id: string;
  title: string;
  type: TaskType;
  status: TaskStatus;
  assignee_id?: string | null;
  start_date?: string | null;
  due_date?: string | null;
  completed_at?: string | null;
  depends_on: string[];
  progress: number;
}

export interface TimelineView {
  pipeline_id: string;
  pipeline_name: string;
  deadline?: string | null;
  tasks: TimelineTask[];
  critical_path: string[];
}

export interface PipelineTemplate {
  id: string;
  org_id: string;
  name: string;
  description?: string | null;
  task_definitions: Record<string, unknown>[];
  settings?: Record<string, unknown> | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// ── Query keys ───────────────────────────────────────────────────────────

export const pipelineKeys = {
  all: ["pipelines"] as const,
  lists: () => [...pipelineKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...pipelineKeys.lists(), filters] as const,
  details: () => [...pipelineKeys.all, "detail"] as const,
  detail: (id: string) => [...pipelineKeys.details(), id] as const,
  timeline: (id: string) => [...pipelineKeys.all, "timeline", id] as const,
  templates: () => [...pipelineKeys.all, "templates"] as const,
};

// ── Placeholder org_id (replaced by auth context in production) ─────────

const ORG_ID = "00000000-0000-0000-0000-000000000001";

// ── Hooks ────────────────────────────────────────────────────────────────

export function usePipelines(
  page = 1,
  pageSize = 20,
  status?: PipelineStatus,
  bookId?: string
) {
  return useQuery<PaginatedPipelines>({
    queryKey: pipelineKeys.list({ page, pageSize, status, bookId }),
    queryFn: async () => {
      const params: Record<string, string | number> = {
        org_id: ORG_ID,
        page,
        page_size: pageSize,
      };
      if (status) params.status = status;
      if (bookId) params.book_id = bookId;
      const { data } = await api.get("/api/v1/pipelines", { params });
      return data;
    },
  });
}

export function usePipeline(id: string) {
  return useQuery<Pipeline>({
    queryKey: pipelineKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/pipelines/${id}`, {
        params: { org_id: ORG_ID },
      });
      return data;
    },
    enabled: !!id,
  });
}

export function useTimeline(id: string) {
  return useQuery<TimelineView>({
    queryKey: pipelineKeys.timeline(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/pipelines/${id}/timeline`, {
        params: { org_id: ORG_ID },
      });
      return data;
    },
    enabled: !!id,
  });
}

export function usePipelineTemplates() {
  return useQuery<PipelineTemplate[]>({
    queryKey: pipelineKeys.templates(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pipelines/templates", {
        params: { org_id: ORG_ID },
      });
      return data;
    },
  });
}

export function useCreatePipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name: string;
      book_id: string;
      description?: string;
      deadline?: string;
      template_id?: string;
      settings?: Record<string, unknown>;
    }) => {
      const { data } = await api.post("/api/v1/pipelines", payload, {
        params: { org_id: ORG_ID },
      });
      return data as Pipeline;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });
    },
  });
}

export function useUpdatePipeline(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name?: string;
      description?: string;
      status?: PipelineStatus;
      deadline?: string;
      settings?: Record<string, unknown>;
    }) => {
      const { data } = await api.patch(`/api/v1/pipelines/${id}`, payload, {
        params: { org_id: ORG_ID },
      });
      return data as Pipeline;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pipelineKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });
    },
  });
}

export function useAddTask(pipelineId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      type?: TaskType;
      description?: string;
      assignee_id?: string;
      due_date?: string;
      depends_on?: string[];
      position?: number;
    }) => {
      const { data } = await api.post(
        `/api/v1/pipelines/${pipelineId}/tasks`,
        payload,
        { params: { org_id: ORG_ID } }
      );
      return data as PipelineTask;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: pipelineKeys.detail(pipelineId),
      });
    },
  });
}

export function useUpdateTask(pipelineId: string, taskId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      type?: TaskType;
      status?: TaskStatus;
      description?: string;
      assignee_id?: string;
      due_date?: string;
      depends_on?: string[];
      position?: number;
    }) => {
      const { data } = await api.patch(
        `/api/v1/pipelines/${pipelineId}/tasks/${taskId}`,
        payload,
        { params: { org_id: ORG_ID } }
      );
      return data as PipelineTask;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: pipelineKeys.detail(pipelineId),
      });
      queryClient.invalidateQueries({
        queryKey: pipelineKeys.timeline(pipelineId),
      });
    },
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name: string;
      description?: string;
      task_definitions?: Array<{
        title: string;
        type?: TaskType;
        description?: string;
        depends_on?: string[];
        estimated_days?: number;
        position?: number;
      }>;
      settings?: Record<string, unknown>;
      is_public?: boolean;
    }) => {
      const { data } = await api.post("/api/v1/pipelines/templates", payload, {
        params: { org_id: ORG_ID },
      });
      return data as PipelineTemplate;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pipelineKeys.templates() });
    },
  });
}
