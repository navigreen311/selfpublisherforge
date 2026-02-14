"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Cover,
  CoverTemplate,
  CoverGenerateRequest,
  CoverGenerationJobResponse,
  CoverGenerationStatusResponse,
  CoverVariationRequest,
  CoverExportRequest,
  CoverExportResponse,
  SaveEditorStateRequest,
  CompetitorAnalysisRequest,
  CompetitorAnalysisResponse,
  CoverGenre,
  CoverArtStyle,
  CoverABTest,
  CreateABTestRequest,
  CastVoteRequest,
  ABTestResults,
  DuplicateCoverRequest,
  SetActiveCoverRequest,
} from "./types";

export type * from "./types";

// ── Query keys ──────────────────────────────────────────────────

const KEYS = {
  all: ["covers"] as const,
  list: (bookId?: string) => ["covers", "list", bookId] as const,
  detail: (id: string) => ["covers", "detail", id] as const,
  templates: (genre?: CoverGenre, style?: CoverArtStyle) =>
    ["covers", "templates", genre, style] as const,
  generationStatus: (jobId: string) =>
    ["covers", "generation-status", jobId] as const,
  abTests: () => ["covers", "ab-tests"] as const,
  abTest: (id: string) => ["covers", "ab-test", id] as const,
  abTestResults: (id: string) => ["covers", "ab-test-results", id] as const,
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

// ── Start cover generation (returns job_id) ─────────────────────

export function useStartCoverGeneration() {
  return useMutation({
    mutationFn: async (payload: CoverGenerateRequest) => {
      const { data } = await api.post<{ data: CoverGenerationJobResponse }>(
        "/api/v1/covers/generate",
        payload
      );
      return data.data;
    },
  });
}

// ── Poll generation status ──────────────────────────────────────

export function usePollGenerationStatus(jobId?: string) {
  return useQuery({
    queryKey: KEYS.generationStatus(jobId || ""),
    queryFn: async () => {
      const { data } = await api.get<{ data: CoverGenerationStatusResponse }>(
        `/api/v1/covers/generation/${jobId}`
      );
      return data.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 3000;
    },
  });
}

// ── Generate cover (legacy single-request method) ──────────────

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

// ── Save cover editor state ─────────────────────────────────────

export function useSaveCoverEditorState(coverId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SaveEditorStateRequest) => {
      const { data } = await api.put<{ data: Cover }>(
        `/api/v1/covers/${coverId}/editor-state`,
        payload
      );
      return data.data;
    },
    onSuccess: (cover) => {
      qc.invalidateQueries({ queryKey: KEYS.detail(coverId) });
      qc.invalidateQueries({ queryKey: KEYS.all });
    },
  });
}

// ── Export cover ────────────────────────────────────────────────

export function useExportCover(coverId: string) {
  return useMutation({
    mutationFn: async (payload: CoverExportRequest) => {
      const { data } = await api.post<{ data: CoverExportResponse }>(
        `/api/v1/covers/${coverId}/export`,
        payload
      );
      return data.data;
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

// ── Duplicate cover ─────────────────────────────────────────────

export function useDuplicateCover(coverId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DuplicateCoverRequest) => {
      const { data } = await api.post<{ data: Cover }>(
        `/api/v1/covers/${coverId}/duplicate`,
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

// ── Set active cover ────────────────────────────────────────────

export function useSetActiveCover(bookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SetActiveCoverRequest) => {
      const { data } = await api.post<{ data: Cover }>(
        `/api/v1/covers/book/${bookId}/active`,
        payload
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list(bookId) });
      qc.invalidateQueries({ queryKey: KEYS.all });
    },
  });
}

// ── List templates ──────────────────────────────────────────────

export function useCoverTemplates(
  genre?: CoverGenre,
  style?: CoverArtStyle
) {
  return useQuery({
    queryKey: KEYS.templates(genre, style),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (genre) params.set("genre", genre);
      if (style) params.set("style", style);
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

export function useCompetitorAnalysis(genre: CoverGenre, subcategory?: string) {
  return useQuery({
    queryKey: ["covers", "competitor-analysis", genre, subcategory],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("genre", genre);
      if (subcategory) params.set("subcategory", subcategory);
      const { data } = await api.get<{ data: CompetitorAnalysisResponse }>(
        `/api/v1/covers/competitor-analysis?${params.toString()}`
      );
      return data.data;
    },
    enabled: !!genre,
  });
}

// ── A/B Testing ─────────────────────────────────────────────────

export function useCreateABTest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateABTestRequest) => {
      const { data } = await api.post<{ data: CoverABTest }>(
        "/api/v1/covers/ab-tests",
        payload
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.abTests() });
    },
  });
}

export function useABTests() {
  return useQuery({
    queryKey: KEYS.abTests(),
    queryFn: async () => {
      const { data } = await api.get<{ data: CoverABTest[] }>(
        "/api/v1/covers/ab-tests"
      );
      return data.data;
    },
  });
}

export function useABTest(id: string) {
  return useQuery({
    queryKey: KEYS.abTest(id),
    queryFn: async () => {
      const { data } = await api.get<{ data: ABTestResults }>(
        `/api/v1/covers/ab-tests/${id}`
      );
      return data.data;
    },
    enabled: !!id,
  });
}

export function useEndABTest(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{ data: CoverABTest }>(
        `/api/v1/covers/ab-tests/${id}/end`
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.abTest(id) });
      qc.invalidateQueries({ queryKey: KEYS.abTests() });
    },
  });
}

export function useVote(testId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CastVoteRequest) => {
      const { data } = await api.post<{ data: { success: boolean } }>(
        `/api/v1/covers/ab-tests/${testId}/vote`,
        payload
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.abTest(testId) });
      qc.invalidateQueries({ queryKey: KEYS.abTestResults(testId) });
    },
  });
}
