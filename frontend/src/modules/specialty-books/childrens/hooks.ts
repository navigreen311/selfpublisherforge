"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  ChildrensBook,
  ChildrensBookStats,
  BookPage,
  Character,
  TextAnalysisResult,
  PreflightResult,
  CreateChildrensBookPayload,
  PaginatedResponse,
} from "./types";

export type * from "./types";

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const childrensBookKeys = {
  all: ["childrens-books"] as const,
  stats: () => [...childrensBookKeys.all, "stats"] as const,
  books: (page?: number, pageSize?: number) =>
    [...childrensBookKeys.all, "list", { page, pageSize }] as const,
  book: (id: string) => [...childrensBookKeys.all, "detail", id] as const,
  pages: (bookId: string) =>
    [...childrensBookKeys.all, "pages", bookId] as const,
  characters: (bookId: string) =>
    [...childrensBookKeys.all, "characters", bookId] as const,
  textAnalysis: (bookId: string) =>
    [...childrensBookKeys.all, "text-analysis", bookId] as const,
  preflight: (bookId: string) =>
    [...childrensBookKeys.all, "preflight", bookId] as const,
};

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export function useChildrensBookStats() {
  return useQuery<ChildrensBookStats>({
    queryKey: childrensBookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/specialty-books/childrens/stats");
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Books CRUD
// ---------------------------------------------------------------------------

export function useChildrensBooks(page = 1, pageSize = 20) {
  return useQuery<PaginatedResponse<ChildrensBook>>({
    queryKey: childrensBookKeys.books(page, pageSize),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/specialty-books/childrens", {
        params: { page, page_size: pageSize },
      });
      return data;
    },
  });
}

export function useChildrensBook(id: string) {
  return useQuery<ChildrensBook>({
    queryKey: childrensBookKeys.book(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/specialty-books/childrens/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateChildrensBook() {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBook, Error, CreateChildrensBookPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        "/api/v1/specialty-books/childrens",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.books() });
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.stats() });
      toast.success("Children\u2019s book created");
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
      await api.delete(`/api/v1/specialty-books/childrens/${bookId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.books() });
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.stats() });
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
  return useQuery<BookPage[]>({
    queryKey: childrensBookKeys.pages(bookId),
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/specialty-books/childrens/${bookId}/pages`,
      );
      return data;
    },
    enabled: !!bookId,
  });
}

export function useUpdatePage(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    BookPage,
    Error,
    { pageId: string; updates: Partial<BookPage> }
  >({
    mutationFn: async ({ pageId, updates }) => {
      const { data } = await api.patch(
        `/api/v1/specialty-books/childrens/${bookId}/pages/${pageId}`,
        updates,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useReorderPages(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { page_ids: string[] }>({
    mutationFn: async (payload) => {
      await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/pages/reorder`,
        payload,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Illustration Generation
// ---------------------------------------------------------------------------

export function useGenerateIllustration(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    BookPage,
    Error,
    { pageId: string; prompt: string; character_consistency: boolean }
  >({
    mutationFn: async ({ pageId, prompt, character_consistency }) => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/pages/${pageId}/generate`,
        { prompt, character_consistency },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useGenerateVariations(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ variations: string[] }, Error, { pageId: string }>({
    mutationFn: async ({ pageId }) => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/pages/${pageId}/variations`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Characters
// ---------------------------------------------------------------------------

export function useCharacters(bookId: string) {
  return useQuery<Character[]>({
    queryKey: childrensBookKeys.characters(bookId),
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/specialty-books/childrens/${bookId}/characters`,
      );
      return data;
    },
    enabled: !!bookId,
  });
}

export function useCreateCharacter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<Character, Error, Partial<Character>>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/characters`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
      toast.success("Character created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateCharacter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    Character,
    Error,
    { characterId: string; updates: Partial<Character> }
  >({
    mutationFn: async ({ characterId, updates }) => {
      const { data } = await api.patch(
        `/api/v1/specialty-books/childrens/${bookId}/characters/${characterId}`,
        updates,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useGenerateCharacterReferences(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<Character, Error, { characterId: string }>({
    mutationFn: async ({ characterId }) => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/characters/${characterId}/references`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
      toast.success("Reference images generated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Text Analysis
// ---------------------------------------------------------------------------

export function useTextAnalysis(bookId: string) {
  return useMutation<TextAnalysisResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/text-analysis`,
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Preflight & Export
// ---------------------------------------------------------------------------

export function usePreflight(bookId: string) {
  return useMutation<PreflightResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/preflight`,
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useExportBook(bookId: string) {
  return useMutation<
    { download_url: string },
    Error,
    { format: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `/api/v1/specialty-books/childrens/${bookId}/export`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Export ready for download");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
