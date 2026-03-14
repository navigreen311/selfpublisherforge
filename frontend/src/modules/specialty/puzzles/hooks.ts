/**
 * React Query hooks for the Puzzle Books module.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ─── Types ────────────────────────────────────────────────────────────────────

export type PuzzleType =
  | "word_search"
  | "crossword"
  | "maze"
  | "sudoku"
  | "word_scramble"
  | "cryptogram"
  | "number_search"
  | "word_connect"
  | "trivia";

export type Audience = "kids" | "teens" | "adults" | "large_print";

export type DifficultyMode = "progressive" | "fixed" | "mixed";

export type WordDifficulty = "simple" | "standard" | "advanced";

export type ClueStyle = "standard" | "kid_friendly" | "trivia" | "themed";

export type AnswerKeyPosition = "back" | "reverse" | "none";

export type PuzzleMixTemplate = "balanced" | "word_heavy" | "custom";

export interface PuzzleTypeConfig {
  type: PuzzleType;
  quantity: number;
  difficulty: string;
  grid_size: string;
}

export interface PuzzleBook {
  id: string;
  title: string;
  subtitle?: string;
  audience: Audience;
  status: "draft" | "in_progress" | "published";
  puzzle_config: PuzzleTypeConfig[];
  difficulty_mode: DifficultyMode;
  themes: string[];
  seasonal_theme?: string;
  word_difficulty: WordDifficulty;
  clue_style: ClueStyle;
  answer_key_position: AnswerKeyPosition;
  layout: "one_per_page" | "two_per_page";
  extras: string[];
  hint_config?: Record<string, string>;
  puzzle_mix_template?: PuzzleMixTemplate;
  custom_percentages?: Record<string, number>;
  total_puzzles: number;
  puzzles_created: number;
  series_id?: string;
  series_name?: string;
  volume_number?: number;
  quality_score?: number;
  cover_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Puzzle {
  id: string;
  book_id: string;
  puzzle_type: PuzzleType;
  puzzle_number: number;
  theme?: string;
  difficulty: string;
  difficulty_score: number;
  grid_size?: string;
  grid_data?: Record<string, unknown>;
  word_list?: string[];
  clues?: { clue: string; answer: string }[];
  solution_data?: Record<string, unknown>;
  answer_key_url?: string;
  status: "pending" | "generating" | "generated" | "verified" | "failed";
  quality_issues?: string[];
  created_at: string;
}

export interface CreatePuzzleBookInput {
  title: string;
  subtitle?: string;
  audience: Audience;
  puzzle_config: PuzzleTypeConfig[];
  difficulty_mode: DifficultyMode;
  themes: string[];
  seasonal_theme?: string;
  word_difficulty: WordDifficulty;
  clue_style: ClueStyle;
  answer_key_position: AnswerKeyPosition;
  layout: "one_per_page" | "two_per_page";
  extras: string[];
  hint_config?: Record<string, string>;
  puzzle_mix_template?: PuzzleMixTemplate;
  custom_percentages?: Record<string, number>;
  theme_input_method?: string;
  series_name?: string;
  volume_number?: number;
  template_id?: string;
}

export interface GeneratePuzzleInput {
  puzzle_type: PuzzleType;
  difficulty: string;
  grid_size?: string;
  theme?: string;
  word_list?: string[];
}

export interface GenerateWordListInput {
  theme: string;
  word_difficulty: WordDifficulty;
  count?: number;
}

export interface SanitizeWordListInput {
  words: string[];
}

export interface GenerateCluesInput {
  puzzle_id: string;
  style: ClueStyle;
}

export interface QACluesInput {
  puzzle_id: string;
}

export interface ExportOptions {
  format: "pdf" | "png";
  dpi?: number;
  include_answers?: boolean;
}

export interface ExportResult {
  download_url: string;
  format: string;
  file_size: number;
  page_count: number;
}

export interface PuzzleBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  puzzles_created: number;
}

// ─── Query Keys ───────────────────────────────────────────────────────────────

const BASE = "/api/v1/specialty/puzzle-books";

const QUERY_KEYS = {
  books: ["puzzle-books"] as const,
  book: (id: string) => ["puzzle-books", id] as const,
  puzzles: (bookId: string) => ["puzzle-books", bookId, "puzzles"] as const,
  stats: ["puzzle-books", "stats"] as const,
};

// ─── Book Hooks ───────────────────────────────────────────────────────────────

export function usePuzzleBooks(params?: {
  status?: string;
  search?: string;
  audience?: string;
  cursor?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.books, params],
    queryFn: async () => {
      const { data } = await api.get<{
        items: PuzzleBook[];
        total: number;
        cursor?: string;
      }>(BASE, { params });
      return data;
    },
  });
}

export function usePuzzleBook(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.book(id),
    queryFn: async () => {
      const { data } = await api.get<PuzzleBook>(`${BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreatePuzzleBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CreatePuzzleBookInput) => {
      const { data } = await api.post<PuzzleBook>(BASE, input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.books });
      toast.success("Puzzle book created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function usePuzzleBookStats() {
  return useQuery({
    queryKey: QUERY_KEYS.stats,
    queryFn: async () => {
      const { data } = await api.get<PuzzleBookStats>(`${BASE}/stats`);
      return data;
    },
  });
}

// ─── Puzzle Hooks ─────────────────────────────────────────────────────────────

export function usePuzzles(bookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.puzzles(bookId),
    queryFn: async () => {
      const { data } = await api.get<Puzzle[]>(`${BASE}/${bookId}/puzzles`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useGeneratePuzzle(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: GeneratePuzzleInput) => {
      const { data } = await api.post<Puzzle>(
        `${BASE}/${bookId}/puzzles/generate`,
        input
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.puzzles(bookId) });
      toast.success("Puzzle generated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Word List Hooks ──────────────────────────────────────────────────────────

export function useGenerateWordList() {
  return useMutation({
    mutationFn: async (input: GenerateWordListInput) => {
      const { data } = await api.post<{ words: string[] }>(
        `${BASE}/generate-word-list`,
        input
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Word list generated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useSanitizeWordList() {
  return useMutation({
    mutationFn: async (input: SanitizeWordListInput) => {
      const { data } = await api.post<{
        clean_words: string[];
        removed: { word: string; reason: string }[];
      }>(`${BASE}/sanitize-word-list`, input);
      return data;
    },
    onSuccess: (data) => {
      if (data.removed.length > 0) {
        toast.warning(`Removed ${data.removed.length} problematic words`);
      } else {
        toast.success("Word list is clean");
      }
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ─── Clue Hooks ───────────────────────────────────────────────────────────────

export function useGenerateClues(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: GenerateCluesInput) => {
      const { data } = await api.post<{
        clues: { clue: string; answer: string }[];
      }>(`${BASE}/${bookId}/puzzles/${input.puzzle_id}/generate-clues`, {
        style: input.style,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.puzzles(bookId) });
      toast.success("Clues generated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useQAClues(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: QACluesInput) => {
      const { data } = await api.post<{
        score: number;
        issues: { clue: string; issue: string; suggestion: string }[];
      }>(`${BASE}/${bookId}/puzzles/${input.puzzle_id}/qa-clues`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.puzzles(bookId) });
      toast.success("Clue QA complete");
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
