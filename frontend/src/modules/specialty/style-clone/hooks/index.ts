"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  StyleCloneProfile,
  CreateStyleCloneRequest,
  UpdateStyleCloneRequest,
  StyleAnalysisResult,
  TestGenerateResult,
  DriftCheckResult,
  PaginatedStyleCloneResponse,
} from "@/modules/specialty/types/style-clone";

export type {
  StyleCloneProfile,
  StyleAnalysisResult,
  TestGenerateResult,
  DriftCheckResult,
};

const API_BASE = "/api/v1/specialty/style-clones";

export const styleCloneKeys = {
  all: ["style-clones"] as const,
  list: (params?: Record<string, unknown>) =>
    [...styleCloneKeys.all, "list", params] as const,
  detail: (id: string) => [...styleCloneKeys.all, "detail", id] as const,
};

// ---------------------------------------------------------------------------
// List
// ---------------------------------------------------------------------------

export function useStyleClones(
  page = 1,
  pageSize = 20,
  filters?: { book_type?: string; search?: string; active_only?: boolean },
) {
  return useQuery<PaginatedStyleCloneResponse>({
    queryKey: styleCloneKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, {
        params: {
          page,
          page_size: pageSize,
          ...filters,
        },
      });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Single Profile
// ---------------------------------------------------------------------------

export function useStyleClone(id: string) {
  return useQuery<StyleCloneProfile>({
    queryKey: styleCloneKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// ---------------------------------------------------------------------------
// Create
// ---------------------------------------------------------------------------

export function useCreateStyleClone() {
  const queryClient = useQueryClient();
  return useMutation<StyleCloneProfile, Error, CreateStyleCloneRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post(API_BASE, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleCloneKeys.all });
      toast.success("Style profile created successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Update
// ---------------------------------------------------------------------------

export function useUpdateStyleClone(id: string) {
  const queryClient = useQueryClient();
  return useMutation<StyleCloneProfile, Error, UpdateStyleCloneRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: styleCloneKeys.detail(id),
      });
      queryClient.invalidateQueries({ queryKey: styleCloneKeys.all });
      toast.success("Style profile updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Delete
// ---------------------------------------------------------------------------

export function useDeleteStyleClone() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (profileId) => {
      await api.delete(`${API_BASE}/${profileId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleCloneKeys.all });
      toast.success("Style profile deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Analyze Style
// ---------------------------------------------------------------------------

export function useAnalyzeStyle(profileId: string) {
  const queryClient = useQueryClient();
  return useMutation<StyleAnalysisResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${profileId}/analyze`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: styleCloneKeys.detail(profileId),
      });
      toast.success("Style analysis complete");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Test Generate
// ---------------------------------------------------------------------------

export function useTestGenerate(profileId: string) {
  const queryClient = useQueryClient();
  return useMutation<TestGenerateResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${profileId}/test-generate`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: styleCloneKeys.detail(profileId),
      });
      toast.success("Test images generated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Check Drift
// ---------------------------------------------------------------------------

export function useCheckDrift(profileId: string) {
  const queryClient = useQueryClient();
  return useMutation<DriftCheckResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${profileId}/check-drift`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: styleCloneKeys.detail(profileId),
      });
      toast.success("Drift check complete");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Set Default
// ---------------------------------------------------------------------------

export function useSetDefault(profileId: string) {
  const queryClient = useQueryClient();
  return useMutation<StyleCloneProfile, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${profileId}/set-default`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleCloneKeys.all });
      toast.success("Default style profile updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
