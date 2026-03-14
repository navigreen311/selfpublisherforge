"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChildrensBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  age_range: "board" | "picture" | "early_reader" | "chapter";
  page_count: number;
  trim_size: string;
  illustration_style: string;
  color_palette: string;
  story_mode: string;
  creation_mode: string;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: string;
  fear_intensity: string;
  tone: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  status: "draft" | "in-progress" | "published";
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ChildrensBookPage {
  id: string;
  book_id: string;
  page_number: number;
  page_type: string;
  layout: string;
  text_content?: string;
  translated_text?: string;
  text_font?: string;
  text_size?: number;
  text_color?: string;
  text_position?: string;
  illustration_prompt?: string;
  illustration_url?: string;
  illustration_model?: string;
  text_plate_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChildrensBookCharacter {
  id: string;
  book_id: string;
  name: string;
  species?: string;
  description: string;
  reference_images: string[];
  auto_append: boolean;
  clothing_rules?: Record<string, unknown>;
  scale_rules?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateChildrensBookPayload {
  title: string;
  subtitle?: string;
  author: string;
  age_range: string;
  page_count: number;
  trim_size: string;
  illustration_style: string;
  color_palette: string;
  story_mode: string;
  creation_mode: string;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: string;
  fear_intensity: string;
  tone: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  safety_settings: Record<string, boolean>;
}

export interface UpdateChildrensBookPayload {
  title?: string;
  subtitle?: string;
  author?: string;
  age_range?: string;
  page_count?: number;
  trim_size?: string;
  illustration_style?: string;
  color_palette?: string;
  status?: string;
}

export interface ChildrensBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  pages_created: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/childrens-books";

export const childrensBookKeys = {
  all: ["childrens-books"] as const,
  list: (params?: Record<string, unknown>) =>
    [...childrensBookKeys.all, "list", params] as const,
  detail: (id: string) => [...childrensBookKeys.all, "detail", id] as const,
  pages: (bookId: string) =>
    [...childrensBookKeys.all, "pages", bookId] as const,
  characters: (bookId: string) =>
    [...childrensBookKeys.all, "characters", bookId] as const,
  stats: () => [...childrensBookKeys.all, "stats"] as const,
};

// ---------------------------------------------------------------------------
// List / Stats
// ---------------------------------------------------------------------------

export function useChildrensBooks(
  page = 1,
  pageSize = 20,
  filters?: { status?: string; age_range?: string; search?: string },
) {
  return useQuery<PaginatedResponse<ChildrensBook>>({
    queryKey: childrensBookKeys.list({ page, pageSize, ...filters }),
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

export function useChildrensBookStats() {
  return useQuery<ChildrensBookStats>({
    queryKey: childrensBookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/stats`);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Single Book CRUD
// ---------------------------------------------------------------------------

export function useChildrensBook(id: string) {
  return useQuery<ChildrensBook>({
    queryKey: childrensBookKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateChildrensBook() {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBook, Error, CreateChildrensBookPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(API_BASE, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
      toast.success("Children's book created successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateChildrensBook(id: string) {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBook, Error, UpdateChildrensBookPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.detail(id),
      });
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteChildrensBook() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (bookId) => {
      await api.delete(`${API_BASE}/${bookId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
      toast.success("Book deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

export function useBookPages(bookId: string) {
  return useQuery<ChildrensBookPage[]>({
    queryKey: childrensBookKeys.pages(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${bookId}/pages`);
      return data;
    },
    enabled: !!bookId,
  });
}

// ---------------------------------------------------------------------------
// Characters
// ---------------------------------------------------------------------------

export function useBookCharacters(bookId: string) {
  return useQuery<ChildrensBookCharacter[]>({
    queryKey: childrensBookKeys.characters(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${bookId}/characters`);
      return data;
    },
    enabled: !!bookId,
  });
}
