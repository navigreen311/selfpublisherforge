"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type { Comic, ComicPage, ComicPanel, ComicBubble, ComicCharacter, ComicStats, CreateComicRequest, UpdateComicRequest, LayoutTemplate } from "@/modules/specialty/types/comic";

export type { Comic, ComicPage, ComicPanel, ComicBubble, ComicCharacter, ComicStats };

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

const API_BASE = "/api/v1/specialty/comic-books";

export const comicKeys = {
  all: ["comics"] as const,
  list: (params?: Record<string, unknown>) => [...comicKeys.all, "list", params] as const,
  detail: (id: string) => [...comicKeys.all, "detail", id] as const,
  pages: (comicId: string) => [...comicKeys.all, "pages", comicId] as const,
  panels: (pageId: string) => [...comicKeys.all, "panels", pageId] as const,
  characters: (comicId: string) => [...comicKeys.all, "characters", comicId] as const,
  stats: () => [...comicKeys.all, "stats"] as const,
};

export function useComics(page = 1, pageSize = 20, filters?: { status?: string; format?: string; search?: string }) {
  return useQuery<PaginatedResponse<Comic>>({
    queryKey: comicKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } });
      return data;
    },
  });
}

export function useComicStats() {
  return useQuery<ComicStats>({
    queryKey: comicKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(API_BASE + "/stats");
      return data;
    },
  });
}

export function useComic(id: string) {
  return useQuery<Comic>({
    queryKey: comicKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(API_BASE + "/" + id);
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
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

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

export function useDeleteComic() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (comicId) => { await api.delete(API_BASE + "/" + comicId); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comicKeys.all });
      toast.success("Comic deleted");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}
