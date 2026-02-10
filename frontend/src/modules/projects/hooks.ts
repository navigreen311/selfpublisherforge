"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Project {
  id: string;
  title: string;
  type: "book" | "series" | "course";
  status: "draft" | "active" | "archived" | "completed";
  settings: Record<string, unknown> | null;
  pen_name_id: string | null;
  books: BookSummary[];
  created_at: string;
  updated_at: string;
}

export interface BookSummary {
  id: string;
  title: string;
  format: string;
  status: string;
}

export interface CreateProjectData {
  title: string;
  type: "book" | "series" | "course";
  genre?: string;
  pen_name?: string;
  description?: string;
}

export interface UpdateProjectData {
  title?: string;
  type?: "book" | "series" | "course";
  status?: "draft" | "active" | "archived" | "completed";
  settings?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const projectKeys = {
  all: ["projects"] as const,
  list: (filters?: { status?: string; search?: string }) =>
    [...projectKeys.all, "list", filters] as const,
  detail: (id: string) => [...projectKeys.all, "detail", id] as const,
};

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useProjects(filters?: { status?: string; search?: string }) {
  return useQuery<Project[]>({
    queryKey: projectKeys.list(filters),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (filters?.status && filters.status !== "all") {
        params.status = filters.status;
      }
      if (filters?.search) {
        params.search = filters.search;
      }
      const { data } = await api.get("/api/v1/books", { params });
      return data;
    },
  });
}

export function useProject(id: string) {
  return useQuery<Project>({
    queryKey: projectKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/books/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation<Project, Error, CreateProjectData>({
    mutationFn: async (project) => {
      const { data } = await api.post("/api/v1/books", project);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation<Project, Error, { id: string; data: UpdateProjectData }>({
    mutationFn: async ({ id, data: updateData }) => {
      const { data } = await api.patch(`/api/v1/books/${id}`, updateData);
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(variables.id),
      });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`/api/v1/books/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}
