"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  PhotoReference,
  PhotoUsageType,
  PaginatedResponse,
} from "@/modules/specialty/types/photo";

export type { PhotoReference, PhotoUsageType };

const API_BASE = "/api/v1/specialty/photo-references";

export const photoKeys = {
  all: ["photos"] as const,
  list: (params?: Record<string, unknown>) =>
    [...photoKeys.all, "list", params] as const,
  detail: (id: string) => [...photoKeys.all, "detail", id] as const,
};

export function usePhotoReferences(
  page = 1,
  pageSize = 20,
  filters?: {
    book_type?: string;
    book_id?: string;
    usage_type?: string;
    search?: string;
  },
) {
  return useQuery<PaginatedResponse<PhotoReference>>({
    queryKey: photoKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, {
        params: { page, page_size: pageSize, ...filters },
      });
      return data;
    },
  });
}

export function usePhotoReference(id: string) {
  return useQuery<PhotoReference>({
    queryKey: photoKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useUploadPhoto() {
  const queryClient = useQueryClient();
  return useMutation<
    PhotoReference,
    Error,
    {
      file: File;
      name: string;
      description?: string;
      usage_type: string;
      book_type?: string;
      book_id?: string;
    }
  >({
    mutationFn: async (payload) => {
      const formData = new FormData();
      formData.append("file", payload.file);
      formData.append("name", payload.name);
      formData.append("description", payload.description || "");
      formData.append("usage_type", payload.usage_type);
      if (payload.book_type) formData.append("book_type", payload.book_type);
      if (payload.book_id) formData.append("book_id", payload.book_id);
      const { data } = await api.post(API_BASE, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: photoKeys.all });
      toast.success("Photo uploaded successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdatePhoto(id: string) {
  const queryClient = useQueryClient();
  return useMutation<PhotoReference, Error, Partial<PhotoReference>>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: photoKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: photoKeys.all });
      toast.success("Photo updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeletePhoto() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (photoId) => {
      await api.delete(`${API_BASE}/${photoId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: photoKeys.all });
      toast.success("Photo deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useGenerateWithRefs() {
  return useMutation<
    { image_url: string },
    Error,
    { reference_ids: string[]; prompt: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/generate-with-refs`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Image generated using references");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
