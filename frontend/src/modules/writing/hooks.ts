"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  ChapterContent,
  ManuscriptResponse,
  ReadabilityScore,
  ManuscriptAnalysis,
  OutlineChapter,
  OutlineResponse,
  GenerateRequest,
  WritingSessionCreate,
  SSEStreamState,
  StandaloneOutlineRequest,
  ChapterOutline,
  StandaloneOutlineResponse,
  BookEntry,
  WritingSessionEntry,
  SaveStatus,
} from "./types";

export type * from "./types";

export function useSSEGeneration() {
  const [state, setState] = useState<SSEStreamState>({
    content: "",
    isStreaming: false,
    error: null,
    qualityResults: null,
    completeMeta: null,
  });

  const abortRef = useRef<AbortController | null>(null);

  const startGeneration = useCallback(async (request: GenerateRequest) => {
    // Abort any ongoing stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({
      content: "",
      isStreaming: true,
      error: null,
      qualityResults: null,
      completeMeta: null,
    });

    try {
      const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("access_token")
          : null;

      const response = await fetch(`${baseURL}/api/v1/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ ...request, stream: true }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const eventLine = block
            .split("\n")
            .find((l) => l.startsWith("event:"));
          const dataLine = block
            .split("\n")
            .find((l) => l.startsWith("data:"));

          if (!dataLine) continue;
          const data = JSON.parse(dataLine.slice(5).trim());
          const eventType = eventLine?.slice(6).trim() || "token";

          if (eventType === "token") {
            setState((prev) => ({
              ...prev,
              content: prev.content + (data.text || ""),
            }));
          } else if (eventType === "quality") {
            setState((prev) => ({ ...prev, qualityResults: data }));
          } else if (eventType === "complete") {
            setState((prev) => ({
              ...prev,
              completeMeta: data,
              isStreaming: false,
            }));
          } else if (eventType === "error") {
            setState((prev) => ({
              ...prev,
              error: data.error || "Unknown error",
              isStreaming: false,
            }));
          }
        }
      }

      setState((prev) => ({ ...prev, isStreaming: false }));
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Unknown error",
        isStreaming: false,
      }));
    }
  }, []);

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { ...state, startGeneration, stopGeneration };
}

// ---------------------------------------------------------------------------
// React Query hooks
// ---------------------------------------------------------------------------

export function useManuscript(bookId: string) {
  return useQuery<ManuscriptResponse>({
    queryKey: ["manuscript", bookId],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/books/${bookId}/manuscript`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useChapters(bookId: string) {
  return useQuery<ChapterContent[]>({
    queryKey: ["chapters", bookId],
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/books/${bookId}/manuscript/chapters`
      );
      return data;
    },
    enabled: !!bookId,
  });
}

export function useChapter(bookId: string, chapterId: string) {
  return useQuery<ChapterContent>({
    queryKey: ["chapter", bookId, chapterId],
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/books/${bookId}/manuscript/chapters/${chapterId}`
      );
      return data;
    },
    enabled: !!bookId && !!chapterId,
  });
}

export function useCreateChapter(bookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      content?: string;
      order?: number;
      synopsis?: string;
    }) => {
      const { data } = await api.post(
        `/api/v1/books/${bookId}/manuscript/chapters`,
        payload
      );
      return data as ChapterContent;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chapters", bookId] });
      qc.invalidateQueries({ queryKey: ["manuscript", bookId] });
    },
  });
}

export function useUpdateChapter(bookId: string, chapterId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      content?: string;
      order?: number;
      synopsis?: string;
    }) => {
      const { data } = await api.put(
        `/api/v1/books/${bookId}/manuscript/chapters/${chapterId}`,
        payload
      );
      return data as ChapterContent;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chapter", bookId, chapterId] });
      qc.invalidateQueries({ queryKey: ["chapters", bookId] });
      qc.invalidateQueries({ queryKey: ["manuscript", bookId] });
    },
  });
}

export function useReorderChapters(bookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (
      chapters: { chapter_id: string; order: number }[]
    ) => {
      const { data } = await api.patch(
        `/api/v1/books/${bookId}/manuscript/chapters/reorder`,
        { chapters }
      );
      return data as ChapterContent[];
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chapters", bookId] });
      qc.invalidateQueries({ queryKey: ["manuscript", bookId] });
    },
  });
}

export function useReadabilityScore(bookId: string) {
  return useQuery<ReadabilityScore>({
    queryKey: ["readability", bookId],
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/books/${bookId}/manuscript/readability-score`
      );
      return data;
    },
    enabled: !!bookId,
  });
}

export function useManuscriptAnalysis(bookId: string) {
  const qc = useQueryClient();
  return useMutation<ManuscriptAnalysis>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/books/${bookId}/manuscript/analyze`
      );
      return data;
    },
  });
}

export function useGenerateOutline(bookId: string) {
  return useMutation<OutlineResponse, Error, Record<string, unknown>>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `/api/v1/books/${bookId}/outline/generate`,
        payload
      );
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Standalone Outline Generation (no book_id required)
// ---------------------------------------------------------------------------

export function useGenerateStandaloneOutline() {
  return useMutation<StandaloneOutlineResponse, Error, StandaloneOutlineRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        "/api/v1/writing/outline/generate",
        payload
      );
      return data;
    },
  });
}

export function useRecordWritingSession() {
  return useMutation({
    mutationFn: async (payload: WritingSessionCreate) => {
      const { data } = await api.post("/api/v1/writing-sessions", payload);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Book listing
// ---------------------------------------------------------------------------

export function useBooks() {
  return useQuery<BookEntry[]>({
    queryKey: ["books"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/books");
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Writing sessions listing
// ---------------------------------------------------------------------------

export function useWritingSessions(bookId?: string) {
  return useQuery<WritingSessionEntry[]>({
    queryKey: ["writing-sessions", bookId],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (bookId) {
        params.book_id = bookId;
      }
      const { data } = await api.get("/api/v1/writing-sessions", { params });
      return data;
    },
    enabled: bookId === undefined || !!bookId,
  });
}

// ---------------------------------------------------------------------------
// Auto-save hook (debounced)
// ---------------------------------------------------------------------------

export function useAutoSave(
  bookId: string,
  chapterId: string | null,
  content: string,
  /** Debounce delay in milliseconds (default 1500ms) */
  delay = 1500
) {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedRef = useRef<string>("");
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (payload: { content: string }) => {
      const { data } = await api.put(
        `/api/v1/books/${bookId}/manuscript/chapters/${chapterId}`,
        payload
      );
      return data as ChapterContent;
    },
    onSuccess: () => {
      setSaveStatus("saved");
      lastSavedRef.current = content;
      qc.invalidateQueries({ queryKey: ["chapters", bookId] });
      qc.invalidateQueries({ queryKey: ["manuscript", bookId] });
      // Reset to idle after 2 seconds
      setTimeout(() => {
        setSaveStatus((prev) => (prev === "saved" ? "idle" : prev));
      }, 2000);
    },
    onError: () => {
      setSaveStatus("error");
    },
  });

  useEffect(() => {
    // Do not auto-save when there is no active chapter or content is empty
    if (!chapterId || !bookId) return;
    // Do not save if content has not changed from last save
    if (content === lastSavedRef.current) return;

    // Clear existing debounce timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      setSaveStatus("saving");
      mutation.mutate({ content });
    }, delay);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content, chapterId, bookId, delay]);

  // Expose an imperative save for the manual "Save" button
  const saveNow = useCallback(() => {
    if (!chapterId || !bookId) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    setSaveStatus("saving");
    mutation.mutate({ content });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId, bookId, content]);

  // Reset when chapter changes
  useEffect(() => {
    lastSavedRef.current = content;
    setSaveStatus("idle");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId]);

  return { saveStatus, saveNow };
}
