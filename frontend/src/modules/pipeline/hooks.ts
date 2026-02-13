"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import type {
  PipelineStatus,
  TaskType,
  TaskStatus,
  PipelineTask,
  Pipeline,
  PipelineSummary,
  PaginatedPipelines,
  TimelineTask,
  TimelineView,
  PipelineTemplate,
} from "./types";

export type * from "./types";

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

// ── Hooks ────────────────────────────────────────────────────────────────

export function usePipelines(
  page = 1,
  pageSize = 20,
  status?: PipelineStatus,
  bookId?: string
) {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
  return useQuery<PaginatedPipelines>({
    queryKey: pipelineKeys.list({ page, pageSize, status, bookId }),
    queryFn: async () => {
      const params: Record<string, string | number> = {
        org_id: orgId!,
        page,
        page_size: pageSize,
      };
      if (status) params.status = status;
      if (bookId) params.book_id = bookId;
      const { data } = await api.get("/api/v1/pipelines", { params });
      return data;
    },
    enabled: !!orgId,
  });
}

export function usePipeline(id: string) {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
  return useQuery<Pipeline>({
    queryKey: pipelineKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/pipelines/${id}`, {
        params: { org_id: orgId },
      });
      return data;
    },
    enabled: !!id && !!orgId,
  });
}

export function useTimeline(id: string) {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
  return useQuery<TimelineView>({
    queryKey: pipelineKeys.timeline(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/pipelines/${id}/timeline`, {
        params: { org_id: orgId },
      });
      return data;
    },
    enabled: !!id && !!orgId,
  });
}

export function usePipelineTemplates() {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
  return useQuery<PipelineTemplate[]>({
    queryKey: pipelineKeys.templates(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/pipelines/templates", {
        params: { org_id: orgId },
      });
      return data;
    },
    enabled: !!orgId,
  });
}

export function useCreatePipeline() {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
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
        params: { org_id: orgId },
      });
      return data as Pipeline;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });
    },
  });
}

export function useUpdatePipeline(id: string) {
  const { user } = useAuthStore();
  const orgId = user?.org_id;
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
        params: { org_id: orgId },
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
  const { user } = useAuthStore();
  const orgId = user?.org_id;
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
        { params: { org_id: orgId } }
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
  const { user } = useAuthStore();
  const orgId = user?.org_id;
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
        { params: { org_id: orgId } }
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
  const { user } = useAuthStore();
  const orgId = user?.org_id;
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
        params: { org_id: orgId },
      });
      return data as PipelineTemplate;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pipelineKeys.templates() });
    },
  });
}
