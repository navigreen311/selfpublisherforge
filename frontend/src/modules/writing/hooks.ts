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
  EnhancedOutlineRequest,
  EnhancedOutlineResponse,
  WritingAnalyticsData,
  ChapterVersion,
  StyleProfile,
  AIWriteRequest,
  CreateManuscriptRequest,
  ReadabilityPostResponse,
  ExportResponse,
  EditorSettings,
  WritingSessionActive,
  SessionHeartbeat,
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

export function useDeleteChapter(bookId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (chapterId: string) => {
      await api.delete(
        `/api/v1/books/${bookId}/manuscript/chapters/${chapterId}`
      );
    },
    onSuccess: () => {
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

export function useChapterReadability(chapterId: string) {
  return useQuery<ReadabilityScore>({
    queryKey: ["chapter-readability", chapterId],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/writing/readability/${chapterId}`);
      return data;
    },
    enabled: !!chapterId,
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

// ---------------------------------------------------------------------------
// Enhanced Outline Generator
// ---------------------------------------------------------------------------

export function useGenerateEnhancedOutline() {
  return useMutation<EnhancedOutlineResponse, Error, EnhancedOutlineRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/writing/generate-outline", payload);
      return data;
    },
  });
}

export function useCreateFromOutline() {
  const qc = useQueryClient();
  return useMutation<ManuscriptResponse, Error, { project_id?: string; outline: EnhancedOutlineResponse; title: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/writing/create-from-outline", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

// ---------------------------------------------------------------------------
// AI Writing Generation
// ---------------------------------------------------------------------------

export function useAIWrite() {
  return useMutation<{ content: string }, Error, AIWriteRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/writing/generate", payload);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Writing Sessions
// ---------------------------------------------------------------------------

export function useRecordWritingSession() {
  return useMutation({
    mutationFn: async (payload: WritingSessionCreate) => {
      const { data } = await api.post("/api/v1/writing-sessions", payload);
      return data;
    },
  });
}

export function useStartWritingSession() {
  return useMutation<{ session_id: string }, Error, { manuscript_id: string; chapter_id?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/writing/sessions/start", payload);
      return data;
    },
  });
}

export function useEndWritingSession() {
  return useMutation<void, Error, { sessionId: string; words_written: number; duration_seconds: number }>({
    mutationFn: async ({ sessionId, ...body }) => {
      await api.patch(`/api/v1/writing/sessions/${sessionId}/end`, body);
    },
  });
}

// ---------------------------------------------------------------------------
// Writing Analytics
// ---------------------------------------------------------------------------

export function useWritingAnalytics(period = "30d") {
  return useQuery<WritingAnalyticsData>({
    queryKey: ["writing-analytics", period],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/writing/analytics", { params: { period } });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Chapter Version History
// ---------------------------------------------------------------------------

export function useChapterVersions(bookId: string, chapterId: string) {
  return useQuery<ChapterVersion[]>({
    queryKey: ["chapter-versions", bookId, chapterId],
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/manuscripts/${bookId}/chapters/${chapterId}/versions`
      );
      return data;
    },
    enabled: !!bookId && !!chapterId,
  });
}

export function useRestoreChapterVersion(bookId: string, chapterId: string) {
  const qc = useQueryClient();
  return useMutation<ChapterContent, Error, string>({
    mutationFn: async (versionId) => {
      const { data } = await api.post(
        `/api/v1/manuscripts/${bookId}/chapters/${chapterId}/versions/${versionId}/restore`
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chapter", bookId, chapterId] });
      qc.invalidateQueries({ queryKey: ["chapters", bookId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Style Profiles
// ---------------------------------------------------------------------------

export function useStyleProfiles() {
  return useQuery<StyleProfile[]>({
    queryKey: ["style-profiles"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/style-profiles");
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
      setTimeout(() => {
        setSaveStatus((prev) => (prev === "saved" ? "idle" : prev));
      }, 2000);
    },
    onError: () => {
      setSaveStatus("error");
    },
  });

  useEffect(() => {
    if (!chapterId || !bookId) return;
    if (content === lastSavedRef.current) return;

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

  const saveNow = useCallback(() => {
    if (!chapterId || !bookId) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    setSaveStatus("saving");
    mutation.mutate({ content });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId, bookId, content]);

  useEffect(() => {
    lastSavedRef.current = content;
    setSaveStatus("idle");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId]);

  return { saveStatus, saveNow };
}

// ---------------------------------------------------------------------------
// Create manuscript
// ---------------------------------------------------------------------------

export function useCreateManuscript() {
  const qc = useQueryClient();
  return useMutation<BookEntry, Error, CreateManuscriptRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/manuscripts", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Delete manuscript
// ---------------------------------------------------------------------------

export function useDeleteManuscript() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (manuscriptId) => {
      await api.delete(`/api/v1/manuscripts/${manuscriptId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Update manuscript metadata
// ---------------------------------------------------------------------------

export function useUpdateManuscript() {
  const qc = useQueryClient();
  return useMutation<BookEntry, Error, { id: string; data: Partial<BookEntry> }>({
    mutationFn: async ({ id, data: payload }) => {
      const { data } = await api.patch(`/api/v1/manuscripts/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Export manuscript
// ---------------------------------------------------------------------------

export function useExportManuscript() {
  return useMutation<ExportResponse, Error, { manuscriptId: string; format: string }>({
    mutationFn: async ({ manuscriptId, format }) => {
      const { data } = await api.post(`/api/v1/manuscripts/${manuscriptId}/export`, { format });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Post readability analysis (stateless)
// ---------------------------------------------------------------------------

export function useReadabilityPost() {
  return useMutation<ReadabilityPostResponse, Error, string>({
    mutationFn: async (text) => {
      const { data } = await api.post("/api/v1/writing/readability", { text });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Editor settings
// ---------------------------------------------------------------------------

export function useEditorSettings() {
  const qc = useQueryClient();
  const query = useQuery<EditorSettings>({
    queryKey: ["editor-settings"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/writing/settings");
      return data;
    },
  });

  const mutation = useMutation<EditorSettings, Error, Partial<EditorSettings>>({
    mutationFn: async (payload) => {
      const { data } = await api.patch("/api/v1/writing/settings", payload);
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["editor-settings"], data);
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateSettings: mutation.mutate,
    updateSettingsAsync: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  };
}

// ---------------------------------------------------------------------------
// Session heartbeat
// ---------------------------------------------------------------------------

export function useSessionHeartbeat(sessionId: string | null, intervalMs = 30000) {
  const mutation = useMutation<void, Error, SessionHeartbeat>({
    mutationFn: async (payload) => {
      if (!sessionId) return;
      await api.post(`/api/v1/writing/sessions/${sessionId}/heartbeat`, payload);
    },
  });

  useEffect(() => {
    if (!sessionId) return;

    const timer = setInterval(() => {
      mutation.mutate({ words_written: 0 });
    }, intervalMs);

    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, intervalMs]);

  return {
    sendHeartbeat: mutation.mutate,
    sendHeartbeatAsync: mutation.mutateAsync,
  };
}
