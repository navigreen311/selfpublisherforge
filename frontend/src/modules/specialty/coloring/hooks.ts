/**
 * React Query hooks for the Coloring Books module.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ColoringBook {
  id: string;
  title: string;
  subtitle?: string;
  audience: "kids" | "teens" | "adults";
  status: "draft" | "in_progress" | "published";
  page_count: number;
  pages_created: number;
  trim_size: string;
  line_style: string;
  line_weight: number;
  complexity: number;
  stroke_uniformity: boolean;
  theme_description?: string;
  generation_method: "all_at_once" | "one_at_a_time" | "mix";
  bonus_pages: string[];
  series_id?: string;
  series_name?: string;
  volume_number?: number;
  quality_score?: number;
  cover_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ColoringPage {
  id: string;
  book_id: string;
  page_number: number;
  page_type: "coloring" | "bonus" | "blank";
  illustration_prompt?: string;
  illustration_url?: string;
  cleaned_url?: string;
  vectorized_url?: string;
  quality_score?: number;
  quality_issues?: string[];
  complexity_score?: number;
  status: "pending" | "generating" | "generated" | "cleaned" | "approved";
  created_at: string;
}

export interface CreateColoringBookInput {
  title: string;
  subtitle?: string;
  audience: "kids" | "teens" | "adults";
  page_count: number;
  trim_size: string;
  line_style: string;
  line_weight: number;
  complexity: number;
  stroke_uniformity: boolean;
  theme_description?: string;
  generation_method: "all_at_once" | "one_at_a_time" | "mix";
  bonus_pages: string[];
  series_name?: string;
  volume_number?: number;
  template_id?: string;
}

export interface BatchGenerateResult {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  total_pages: number;
  completed_pages: number;
  failed_pages: number;
}

export interface QualityCheckResult {
  overall_score: number;
  complexity_distribution: { level: number; count: number }[];
  theme_cohesion_score: number;
  issues: {
    page_id: string;
    page_number: number;
    issues: string[];
  }[];
  print_quality: {
    line_quality: number;
    closed_shapes: number;
    stroke_uniformity: number;
    ink_density: number;
    small_areas: number;
  };
}

export interface ExportOptions {
  format: "pdf" | "png" | "svg" | "digital_pdf";
  dpi?: number;
}

export interface ExportResult {
  download_url: string;
  format: string;
  file_size: number;
  page_count: number;
}

// ─── Query Keys ───────────────────────────────────────────────────────────────

const BASE = "/api/v1/specialty/coloring-books";

const QUERY_KEYS = {
  books: ["coloring-books"] as const,
  book: (id: string) => ["coloring-books", id] as const,
  pages: (bookId: string) => ["coloring-books", bookId, "pages"] as const,
  qualityCheck: (bookId: string) =>
    ["coloring-books", bookId, "quality-check"] as const,
};

// ─── Book Hooks ───────────────────────────────────────────────────────────────

export function useColoringBooks(params?: {
  status?: string;
  search?: string;
  cursor?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.books, params],
    queryFn: async () => {
      const { data } = await api.get<{
        items: ColoringBook[];
        total: number;
        cursor?: string;
      }>(BASE, { params });
      return data;
    },
  });
}

export function useColoringBook(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.book(id),
    queryFn: async () => {
      const { data } = await api.get<ColoringBook>(`${BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateColoringBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CreateColoringBookInput) => {
      const { data } = await api.post<ColoringBook>(BASE, input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.books });
      toast.success("Coloring book created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Page Hooks ───────────────────────────────────────────────────────────────

export function useColoringPages(bookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.pages(bookId),
    queryFn: async () => {
      const { data } = await api.get<ColoringPage[]>(
        `${BASE}/${bookId}/pages`
      );
      return data;
    },
    enabled: !!bookId,
  });
}

// ─── Batch Generation ─────────────────────────────────────────────────────────

export function useBatchGenerate(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      options?: { page_ids?: string[] }
    ) => {
      const { data } = await api.post<BatchGenerateResult>(
        `${BASE}/${bookId}/batch-generate`,
        options
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pages(bookId) });
      toast.success("Batch generation started");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Quality Check ────────────────────────────────────────────────────────────

export function useQualityCheck(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<QualityCheckResult>(
        `${BASE}/${bookId}/quality-check`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.qualityCheck(bookId),
      });
      toast.success("Quality check complete");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Export ───────────────────────────────────────────────────────────────────

export function useExport(bookId: string) {
  return useMutation({
    mutationFn: async (options: ExportOptions) => {
      const { data } = await api.post<ExportResult>(
        `${BASE}/${bookId}/export`,
        options
      );
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Export ready: ${data.format.toUpperCase()}`);
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
