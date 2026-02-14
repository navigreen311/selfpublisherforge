"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  AudiobookProject,
  AudiobookChapter,
  Voice,
  GenerationJob,
  CostBreakdown,
  ACXValidationResult,
  PronunciationEntry,
  AudiobookWSEvent,
  CreateAudiobookProjectPayload,
  UpdateAudiobookProjectPayload,
  VoiceSample,
  AudiobookCreateRequest,
  PaginatedResponse,
} from "./types";

export type * from "./types";
import { useAudiobookStudioStore } from "./store";

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const audiobookKeys = {
  all: ["audiobook"] as const,
  projects: (page?: number, pageSize?: number) =>
    [...audiobookKeys.all, "projects", { page, pageSize }] as const,
  project: (id: string) => [...audiobookKeys.all, "project", id] as const,
  chapters: (projectId: string) =>
    [...audiobookKeys.all, "chapters", projectId] as const,
  voices: () => [...audiobookKeys.all, "voices"] as const,
  voiceSamples: (tier?: string) =>
    [...audiobookKeys.all, "voice-samples", { tier }] as const,
  costEstimate: (projectId: string) =>
    [...audiobookKeys.all, "cost-estimate", projectId] as const,
  pronunciation: (projectId?: string) =>
    [...audiobookKeys.all, "pronunciation", projectId] as const,
  validation: (projectId: string) =>
    [...audiobookKeys.all, "validation", projectId] as const,
  stats: () => [...audiobookKeys.all, "stats"] as const,
};

// ---------------------------------------------------------------------------
// Stats & Overview
// ---------------------------------------------------------------------------

export interface AudiobookStats {
  total_projects: number;
  projects_in_progress: number;
  projects_completed: number;
  total_duration_hours: number;
}

export function useAudiobookStats() {
  return useQuery<AudiobookStats>({
    queryKey: audiobookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/audiobooks/stats");
      return data;
    },
  });
}
// Projects
// ---------------------------------------------------------------------------

export function useAudiobookProjects(page = 1, pageSize = 20) {
  return useQuery<PaginatedResponse<AudiobookProject>>({
    queryKey: audiobookKeys.projects(page, pageSize),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/audiobooks/projects", {
        params: { page, page_size: pageSize },
      });
      return data;
    },
  });
}

export function useAudiobookProject(id: string) {
  return useQuery<AudiobookProject & { chapters: AudiobookChapter[] }>({
    queryKey: audiobookKeys.project(id),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/audiobooks/projects/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateAudiobookProject() {
  const queryClient = useQueryClient();
  return useMutation<AudiobookProject, Error, CreateAudiobookProjectPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/audiobooks/projects", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.projects() });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.stats() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// Create audiobook from wizard flow
export function useCreateAudiobook() {
  const queryClient = useQueryClient();
  return useMutation<AudiobookProject, Error, AudiobookCreateRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post("/api/v1/audiobooks/create", request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.projects() });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.stats() });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.stats() });
      toast.success("Audiobook project created successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateAudiobookProject(id: string) {
  const queryClient = useQueryClient();
  return useMutation<AudiobookProject, Error, UpdateAudiobookProjectPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(
        `/api/v1/audiobooks/projects/${id}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(id) });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.projects() });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.stats() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteAudiobookProject() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (projectId) => {
      await api.delete(`/api/v1/audiobooks/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.projects() });
      queryClient.invalidateQueries({ queryKey: audiobookKeys.stats() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Voices
// ---------------------------------------------------------------------------

export function useVoices() {
  return useQuery<Voice[]>({
    queryKey: audiobookKeys.voices(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/audiobooks/voices");
      return data;
    },
  });
}

export function useVoicePreview() {
  return useMutation<{ audio_url: string }, Error, { voice_id: string; text: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/audiobooks/voices/preview", payload);
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// Get voice samples with optional tier filter
export function useVoiceSamples(tier?: string) {
  return useQuery<VoiceSample[]>({
    queryKey: audiobookKeys.voiceSamples(tier),
    queryFn: async () => {
      const params = tier ? { tier } : {};
      const { data } = await api.get("/api/v1/audiobooks/voices/samples", {
        params,
      });
      return data;
    },
  });
}

// Preview a specific voice with text
export function usePreviewVoice() {
  return useMutation<
    { audio_url: string },
    Error,
    { voiceId: string; text: string }
  >({
    mutationFn: async ({ voiceId, text }) => {
      const { data } = await api.post("/api/v1/audiobooks/voices/preview", {
        voice_id: voiceId,
        text,
      });
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Generation
// ---------------------------------------------------------------------------

export function useGenerateChapter(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<GenerationJob, Error, { chapter_id: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/chapters/${payload.chapter_id}/generate`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useGenerateAllChapters(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<GenerationJob[], Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/generate-all`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// Pause ongoing generation
export function usePauseGeneration(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await api.post(`/api/v1/audiobooks/projects/${projectId}/pause`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
      toast.success("Generation paused");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// Resume paused generation
export function useResumeGeneration(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await api.post(`/api/v1/audiobooks/projects/${projectId}/resume`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
      toast.success("Generation resumed");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useApproveChapter(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<AudiobookChapter, Error, { chapter_id: string; review_notes?: string }>({
    mutationFn: async ({ chapter_id, review_notes }) => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/chapters/${chapter_id}/approve`,
        { review_notes },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Mastering & Export
// ---------------------------------------------------------------------------

export function useMasterAudiobook(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<GenerationJob, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/master`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: audiobookKeys.project(projectId) });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useExportAudiobook(projectId: string) {
  return useMutation<{ download_url: string }, Error, { format?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/export`,
        payload,
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));

// Export specifically for ACX platform
export function useExportForACX(projectId: string) {
  return useMutation<{ download_url: string; validation: ACXValidationResult }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/export-acx`,
      );
      return data;
    },
    onSuccess: (data) => {
      if (data.validation.valid) {
        toast.success("ACX export ready for download");
      } else {
        toast.warning("Export complete but has validation warnings");
      }
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
    },
  });
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

export function useValidateAudiobook(projectId: string) {
  return useMutation<ACXValidationResult, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `/api/v1/audiobooks/projects/${projectId}/validate`,
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Pronunciation
// ---------------------------------------------------------------------------

export function usePronunciationDict(projectId?: string) {
  return useQuery<PronunciationEntry[]>({
    queryKey: audiobookKeys.pronunciation(projectId),
    queryFn: async () => {
      const params = projectId ? { project_id: projectId } : {};
      const { data } = await api.get("/api/v1/audiobooks/pronunciation", {
        params,
      });
      return data;
    },
  });
}

export function useAddPronunciation() {
  const queryClient = useQueryClient();
  return useMutation<
    PronunciationEntry,
    Error,
    Omit<PronunciationEntry, "id">
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/audiobooks/pronunciation", payload);
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: audiobookKeys.pronunciation(variables.audiobook_project_id),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Cost Estimate
// ---------------------------------------------------------------------------

export function useCostEstimate(projectId: string) {
  return useQuery<CostBreakdown>({
    queryKey: audiobookKeys.costEstimate(projectId),
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/audiobooks/projects/${projectId}/cost-estimate`,
      );
      return data;
    },
    enabled: !!projectId,
  });
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

export function useAudiobookWebSocket(projectId: string) {
  const [lastEvent, setLastEvent] = useState<AudiobookWSEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();
  const updateGenerationProgress = useAudiobookStudioStore(
    (s) => s.updateGenerationProgress,
  );

  const connect = useCallback(() => {
    if (!projectId) return;

    const baseUrl = (
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    ).replace(/^http/, "ws");
    const token = typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

    const ws = new WebSocket(
      `${baseUrl}/ws/audiobook/${projectId}?token=${token ?? ""}`,
    );
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const parsed: AudiobookWSEvent = JSON.parse(event.data);
        setLastEvent(parsed);

        if (parsed.type === "chapter_generation_progress") {
          updateGenerationProgress(
            parsed.chapter_id,
            parsed.percent,
            parsed.stage,
          );
        }

        if (
          parsed.type === "chapter_generation_complete" ||
          parsed.type === "mastering_complete"
        ) {
          queryClient.invalidateQueries({
            queryKey: audiobookKeys.project(projectId),
          });
        }
      } catch {
        // ignore malformed messages
      }
    };
  }, [projectId, queryClient, updateGenerationProgress]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { lastEvent, connected, send };
}
