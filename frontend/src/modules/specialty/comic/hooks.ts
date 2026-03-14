"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  Comic,
  ComicPage,
  ComicPanel,
  ComicBubble,
  ComicCharacter,
  ComicStats,
  CreateComicRequest,
  UpdateComicRequest,
  LayoutTemplate,
} from "@/modules/specialty/types/comic";

// Re-export types for convenience
export type {
  Comic,
  ComicPage,
  ComicPanel,
  ComicBubble,
  ComicCharacter,
  ComicStats,
};

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/comic-books";

export const comicKeys = {
  all: ["comics"] as const,
  list: (params?: Record<string, unknown>) =>
    [...comicKeys.all, "list", params] as const,
  detail: (id: string) => [...comicKeys.all, "detail", id] as const,
  pages: (comicId: string) => [...comicKeys.all, "pages", comicId] as const,
  panels: (pageId: string) => [...comicKeys.all, "panels", pageId] as const,
  characters: (comicId: string) =>
    [...comicKeys.all, "characters", comicId] as const,
  stats: () => [...comicKeys.all, "stats"] as const,
  script: (comicId: string) => [...comicKeys.all, "script", comicId] as const,
  layouts: () => [...comicKeys.all, "layouts"] as const,
};

// ---------------------------------------------------------------------------
// List / Stats
// ---------------------------------------------------------------------------

export function useComics(
  page = 1,
  pageSize = 20,
  filters?: { status?: string; format?: string; search?: string },
) {
  return useQuery<PaginatedResponse<Comic>>({
    queryKey: comicKeys.list({ page, pageSize, ...filters }),
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

export function useComicStats() {
  return useQuery<ComicStats>({
    queryKey: comicKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/stats`);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Single Comic CRUD
// ---------------------------------------------------------------------------

export function useComic(id: string) {
  return useQuery<Comic>({
    queryKey: comicKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateComic() {
  const queryClient = useQueryClient();
  return useMutation<Comic, Error, CreateComicRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post(API_BASE, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.all });
      toast.success("Comic book created successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateComic(id: string) {
  const queryClient = useQueryClient();
  return useMutation<Comic, Error, UpdateComicRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: comicKeys.all });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteComic() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (comicId) => {
      await api.delete(`${API_BASE}/${comicId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.all });
      toast.success("Comic deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

export function useComicPages(comicId: string) {
  return useQuery<ComicPage[]>({
    queryKey: comicKeys.pages(comicId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${comicId}/pages`);
      return data;
    },
    enabled: !!comicId,
  });
}

export function useCreatePage(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ComicPage,
    Error,
    { page_number: number; page_type?: string; layout_template?: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/${comicId}/pages`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.pages(comicId) });
      toast.success("Page created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdatePage(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ComicPage,
    Error,
    { pageId: string; payload: Partial<ComicPage> }
  >({
    mutationFn: async ({ pageId, payload }) => {
      const { data } = await api.patch(
        `${API_BASE}/${comicId}/pages/${pageId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.pages(comicId) });
      toast.success("Page updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeletePage(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (pageId) => {
      await api.delete(`${API_BASE}/${comicId}/pages/${pageId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.pages(comicId) });
      toast.success("Page deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Panels
// ---------------------------------------------------------------------------

export function useComicPanels(pageId: string) {
  return useQuery<ComicPanel[]>({
    queryKey: comicKeys.panels(pageId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/panels/${pageId}`);
      return data;
    },
    enabled: !!pageId,
  });
}

export function useCreatePanel(pageId: string) {
  const queryClient = useQueryClient();
  return useMutation<ComicPanel, Error, Partial<ComicPanel>>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/panels/${pageId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.panels(pageId) });
      toast.success("Panel created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Characters
// ---------------------------------------------------------------------------

export function useComicCharacters(comicId: string) {
  return useQuery<ComicCharacter[]>({
    queryKey: comicKeys.characters(comicId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${comicId}/characters`);
      return data;
    },
    enabled: !!comicId,
  });
}

export interface CreateCharacterPayload {
  name: string;
  role?: string;
  description?: string;
  visual_description?: string;
  auto_append: boolean;
  default_costume?: string;
  color_palette?: Record<string, string>;
}

export interface UpdateCharacterPayload
  extends Partial<CreateCharacterPayload> {}

export function useCreateCharacter(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<ComicCharacter, Error, CreateCharacterPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/${comicId}/characters`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: comicKeys.characters(comicId),
      });
      toast.success("Character created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateCharacter(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ComicCharacter,
    Error,
    { characterId: string; payload: UpdateCharacterPayload }
  >({
    mutationFn: async ({ characterId, payload }) => {
      const { data } = await api.patch(
        `${API_BASE}/${comicId}/characters/${characterId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: comicKeys.characters(comicId),
      });
      toast.success("Character updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteCharacter(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (characterId) => {
      await api.delete(`${API_BASE}/${comicId}/characters/${characterId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: comicKeys.characters(comicId),
      });
      toast.success("Character deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Script
// ---------------------------------------------------------------------------

export interface ComicScript {
  comic_id: string;
  pages: { page_number: number; script_text: string }[];
}

export function useComicScript(comicId: string) {
  return useQuery<ComicScript>({
    queryKey: comicKeys.script(comicId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${comicId}/script`);
      return data;
    },
    enabled: !!comicId,
  });
}

export function useGenerateScript(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<ComicScript, Error, { prompt?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/${comicId}/generate-script`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.script(comicId) });
      queryClient.invalidateQueries({ queryKey: comicKeys.pages(comicId) });
      toast.success("Script generated successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Layout Templates
// ---------------------------------------------------------------------------

export function useLayoutTemplates() {
  return useQuery<LayoutTemplate[]>({
    queryKey: comicKeys.layouts(),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/layout-templates`);
      return data;
    },
  });
}

export function useApplyLayout(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ComicPage,
    Error,
    { pageId: string; templateId: string }
  >({
    mutationFn: async ({ pageId, templateId }) => {
      const { data } = await api.post(
        `${API_BASE}/${comicId}/pages/${pageId}/apply-layout`,
        { template_id: templateId },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.pages(comicId) });
      toast.success("Layout applied");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Export & Preflight
// ---------------------------------------------------------------------------

export interface PreflightResult {
  passed: boolean;
  issues: { severity: string; message: string }[];
}

export function useExportComic(comicId: string) {
  return useMutation<Blob, Error, { format?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/${comicId}/export`,
        payload,
        { responseType: "blob" },
      );
      return data;
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `comic-${comicId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Comic exported successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function usePreflight(comicId: string) {
  const queryClient = useQueryClient();
  return useMutation<PreflightResult, Error>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/${comicId}/preflight`);
      return data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: comicKeys.detail(comicId) });
      if (result.passed) {
        toast.success("Preflight check passed");
      } else {
        toast.warning("Preflight check found issues");
      }
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
