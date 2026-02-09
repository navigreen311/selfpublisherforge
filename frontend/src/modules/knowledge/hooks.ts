"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/types";

// ── Types ───────────────────────────────────────────────────────

export interface KnowledgeEntry {
  id: string;
  org_id: string;
  title: string;
  content: string;
  source_url: string | null;
  source_type: "manual" | "url" | "file" | "clip";
  tags: string[];
  credibility_score: number | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface SearchHit {
  id: string;
  title: string;
  content_snippet: string;
  source_type: string;
  tags: string[];
  score: number;
  credibility_score: number | null;
  created_at: string | null;
}

export interface SearchResult {
  hits: SearchHit[];
  total: number;
  query: string;
}

export interface SummarizeResult {
  entry_id: string;
  summary: string;
  key_points: string[];
  suggested_tags: string[];
}

export interface TagList {
  tags: string[];
  counts: Record<string, number>;
}

export interface ImportPayload {
  url?: string;
  file_name?: string;
  file_content_base64?: string;
  extract_facts?: boolean;
}

export interface ImportResult {
  entry_id: string;
  title: string;
  content_preview: string;
  tags: string[];
  source_type: string;
  status: string;
}

// ── Query keys ──────────────────────────────────────────────────

const KEYS = {
  all: ["knowledge"] as const,
  list: (params?: Record<string, unknown>) => ["knowledge", "list", params] as const,
  detail: (id: string) => ["knowledge", "detail", id] as const,
  search: (query: string) => ["knowledge", "search", query] as const,
  tags: () => ["knowledge", "tags"] as const,
  suggestions: () => ["knowledge", "suggestions"] as const,
};

// ── List entries ────────────────────────────────────────────────

export function useKnowledgeEntries(params?: {
  tag?: string[];
  source_type?: string;
  cursor?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: KEYS.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.tag) params.tag.forEach((t) => searchParams.append("tag", t));
      if (params?.source_type) searchParams.set("source_type", params.source_type);
      if (params?.cursor) searchParams.set("cursor", params.cursor);
      if (params?.limit) searchParams.set("limit", String(params.limit));

      const { data } = await api.get<PaginatedResponse<KnowledgeEntry>>(
        `/api/v1/knowledge?${searchParams.toString()}`
      );
      return data;
    },
  });
}

// ── Get single entry ────────────────────────────────────────────

export function useKnowledgeEntry(id: string) {
  return useQuery({
    queryKey: KEYS.detail(id),
    queryFn: async () => {
      const { data } = await api.get<KnowledgeEntry>(`/api/v1/knowledge/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// ── Create entry ────────────────────────────────────────────────

export function useCreateEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      content: string;
      source_type?: string;
      tags?: string[];
    }) => {
      const { data } = await api.post<KnowledgeEntry>("/api/v1/knowledge", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

// ── Update entry ────────────────────────────────────────────────

export function useUpdateEntry(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<KnowledgeEntry>) => {
      const { data } = await api.put<KnowledgeEntry>(`/api/v1/knowledge/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(id) });
      qc.invalidateQueries({ queryKey: KEYS.all });
    },
  });
}

// ── Delete entry ────────────────────────────────────────────────

export function useDeleteEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/knowledge/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

// ── Search ──────────────────────────────────────────────────────

export function useKnowledgeSearch() {
  return useMutation({
    mutationFn: async (payload: {
      query: string;
      tags?: string[];
      source_type?: string;
      limit?: number;
      offset?: number;
    }) => {
      const { data } = await api.post<SearchResult>("/api/v1/knowledge/search", payload);
      return data;
    },
  });
}

// ── Import ──────────────────────────────────────────────────────

export function useImportEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ImportPayload) => {
      const { data } = await api.post<ImportResult>("/api/v1/knowledge/import", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

// ── Summarize ───────────────────────────────────────────────────

export function useSummarizeEntry(id: string) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<SummarizeResult>(
        `/api/v1/knowledge/${id}/summarize`
      );
      return data;
    },
  });
}

// ── Tags ────────────────────────────────────────────────────────

export function useKnowledgeTags() {
  return useQuery({
    queryKey: KEYS.tags(),
    queryFn: async () => {
      const { data } = await api.get<TagList>("/api/v1/knowledge/tags");
      return data;
    },
  });
}

// ── AI Suggestions ──────────────────────────────────────────────

export function useKnowledgeSuggestions() {
  return useQuery({
    queryKey: KEYS.suggestions(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/knowledge/suggestions");
      return data;
    },
    enabled: false, // Only fetch on demand
  });
}
