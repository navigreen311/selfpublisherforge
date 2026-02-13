"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Cover,
  CoverTemplate,
  CoverGenerateRequest,
  CoverVariationRequest,
  CompetitorAnalysisRequest,
  CompetitorAnalysisResponse,
  CoverGenre,
} from "./types";

export type * from "./types";

// ── Query keys ──────────────────────────────────────────────────

const KEYS = {
  all: ["covers"] as const,
  list: (bookId?: string) => ["covers", "list", bookId] as const,
  detail: (id: string) => ["covers", "detail", id] as const,
  templates: (genre?: CoverGenre) => ["covers", "templates", genre] as const,
};

// ── List covers for a book ──────────────────────────────────────

export function useCovers(bookId?: string) {
  return useQuery({
    queryKey: KEYS.list(bookId),
    queryFn: async () => {
      const endpoint = bookId
        ? `/api/v1/covers/book/${bookId}`
        : "/api/v1/covers";
      const { data } = await api.get<{ data: Cover[] }>(endpoint);
      return data.data;
    },
  });
}

// ── Get single cover ────────────────────────────────────────────

export function useCover(id: string) {
  return useQuery({
    queryKey: KEYS.detail(id),
    queryFn: async () => {
      const { data } = await api.get<{ data: Cover }>(`/api/v1/covers/${id}`);
      return data.data;
    },
    enabled: !!id,
  });
}

// ── Generate cover ──────────────────────────────────────────────

export function useGenerateCover() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CoverGenerateRequest) => {
      const { data } = await api.post<{ data: Cover }>(
        "/api/v1/covers/generate",
        payload
      );
      return data.data;
    },
    onSuccess: (cover) => {
      qc.invalidateQueries({ queryKey: KEYS.all });
      if (cover.book_id) {
        qc.invalidateQueries({ queryKey: KEYS.list(cover.book_id) });
      }
    },
  });
}

// ── Delete cover ────────────────────────────────────────────────

export function useDeleteCover() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/covers/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

// ── List templates ──────────────────────────────────────────────

export function useCoverTemplates(genre?: CoverGenre) {
  return useQuery({
    queryKey: KEYS.templates(genre),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (genre) params.set("genre", genre);
      const { data } = await api.get<{ data: CoverTemplate[] }>(
        `/api/v1/covers/templates?${params.toString()}`
      );
      return data.data;
    },
  });
}

// ── Generate variations ─────────────────────────────────────────

export function useGenerateVariations(coverId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CoverVariationRequest) => {
      const { data } = await api.post<{ data: Cover[] }>(
        `/api/v1/covers/${coverId}/variations`,
        payload
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all });
      qc.invalidateQueries({ queryKey: KEYS.detail(coverId) });
    },
  });
}

// ── Analyze competitors ─────────────────────────────────────────

export function useAnalyzeCompetitors() {
  return useMutation({
    mutationFn: async (payload: CompetitorAnalysisRequest) => {
      const { data } = await api.post<{ data: CompetitorAnalysisResponse }>(
        "/api/v1/covers/analyze-competitors",
        payload
      );
      return data.data;
    },
  });
}
