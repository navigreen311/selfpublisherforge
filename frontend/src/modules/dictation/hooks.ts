"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRef, useState, useCallback, useEffect } from "react";
import type {
  DictationSession,
  DictationCommand,
  DictationSettings,
  DictationServerMessage,
  SessionListResponse,
  CreateSessionRequest,
  UpdateSessionRequest,
  RefineSessionRequest,
  RefineTextRequest,
  RefineTextResponse,
  CreateCommandRequest,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/dictation";

// ── Query Keys ──────────────────────────────────────────────────

export const dictationKeys = {
  all: ["dictation"] as const,
  sessions: () => [...dictationKeys.all, "sessions"] as const,
  sessionList: (page: number, pageSize: number) =>
    [...dictationKeys.sessions(), "list", { page, pageSize }] as const,
  sessionDetail: (id: string) =>
    [...dictationKeys.sessions(), "detail", id] as const,
  commands: () => [...dictationKeys.all, "commands"] as const,
  settings: () => [...dictationKeys.all, "settings"] as const,
};

// ── Session CRUD ────────────────────────────────────────────────

export function useDictationSessions(page = 1, pageSize = 20) {
  return useQuery<SessionListResponse>({
    queryKey: dictationKeys.sessionList(page, pageSize),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/sessions`, {
        params: { page, page_size: pageSize },
      });
      return data;
    },
  });
}

export function useDictationSession(id: string) {
  return useQuery<DictationSession>({
    queryKey: dictationKeys.sessionDetail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/sessions/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateDictationSession() {
  const queryClient = useQueryClient();
  return useMutation<DictationSession, Error, CreateSessionRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/sessions`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dictationKeys.sessions() });
    },
  });
}

export function useUpdateDictationSession() {
  const queryClient = useQueryClient();
  return useMutation<
    DictationSession,
    Error,
    { id: string; request: UpdateSessionRequest }
  >({
    mutationFn: async ({ id, request }) => {
      const { data } = await api.patch(
        `${API_PREFIX}/sessions/${id}`,
        request,
      );
      return data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({
        queryKey: dictationKeys.sessionDetail(id),
      });
      queryClient.invalidateQueries({ queryKey: dictationKeys.sessions() });
    },
  });
}

// ── Refinement ──────────────────────────────────────────────────

export function useRefineSession() {
  const queryClient = useQueryClient();
  return useMutation<
    DictationSession,
    Error,
    { id: string; request: RefineSessionRequest }
  >({
    mutationFn: async ({ id, request }) => {
      const { data } = await api.post(
        `${API_PREFIX}/sessions/${id}/refine`,
        request,
      );
      return data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({
        queryKey: dictationKeys.sessionDetail(id),
      });
    },
  });
}

export function useRefineText() {
  return useMutation<RefineTextResponse, Error, RefineTextRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/refine`, request);
      return data;
    },
  });
}

// ── Commands ────────────────────────────────────────────────────

export function useDictationCommands() {
  return useQuery<DictationCommand[]>({
    queryKey: dictationKeys.commands(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/commands`);
      return data;
    },
  });
}

export function useCreateDictationCommand() {
  const queryClient = useQueryClient();
  return useMutation<DictationCommand, Error, CreateCommandRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/commands`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dictationKeys.commands() });
    },
  });
}

export function useDeleteDictationCommand() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/commands/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dictationKeys.commands() });
    },
  });
}

// ── Settings ────────────────────────────────────────────────────

export function useDictationSettings() {
  return useQuery<DictationSettings>({
    queryKey: dictationKeys.settings(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/settings`);
      return data;
    },
  });
}

export function useUpdateDictationSettings() {
  const queryClient = useQueryClient();
  return useMutation<DictationSettings, Error, Partial<DictationSettings>>({
    mutationFn: async (request) => {
      const { data } = await api.patch(`${API_PREFIX}/settings`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dictationKeys.settings() });
    },
  });
}

// ── WebSocket + Audio Recording ─────────────────────────────────

export function useDictation(sessionId: string | null) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [partialText, setPartialText] = useState("");
  const [finalTexts, setFinalTexts] = useState<string[]>([]);
  const [voiceCommand, setVoiceCommand] = useState<{
    command: string;
    action: string;
  } | null>(null);
  const [metrics, setMetrics] = useState<{
    wpm: number;
    accuracy: number;
    duration: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
      recorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    };
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;

    const wsUrl = `${
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"
    }/api/v1/ws/dictation/${sessionId}`;
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    const url = token
      ? `${wsUrl}?token=${encodeURIComponent(token)}`
      : wsUrl;

    const ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      setConnected(true);
      setError(null);
      // Start heartbeat
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      try {
        const msg: DictationServerMessage = JSON.parse(event.data as string);
        switch (msg.type) {
          case "partial_transcript":
            setPartialText(msg.text);
            break;
          case "final_transcript":
            setPartialText("");
            setFinalTexts((prev) => [...prev, msg.text]);
            break;
          case "voice_command":
            setVoiceCommand({ command: msg.command, action: msg.action });
            break;
          case "session_metrics":
            setMetrics({
              wpm: msg.wpm,
              accuracy: msg.accuracy,
              duration: msg.duration,
            });
            break;
          case "error":
            setError(msg.message);
            break;
          case "session_paused":
            setIsPaused(true);
            break;
          case "session_resumed":
            setIsPaused(false);
            break;
          case "pong":
            // heartbeat acknowledged
            break;
        }
      } catch {
        // Non-JSON message — ignore
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
    };

    wsRef.current = ws;
  }, [sessionId]);

  const startRecording = useCallback(async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError("WebSocket not connected");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      recorder.ondataavailable = (event) => {
        if (
          event.data.size > 0 &&
          wsRef.current?.readyState === WebSocket.OPEN
        ) {
          wsRef.current.send(event.data);
        }
      };

      // Capture ~250ms chunks
      recorder.start(250);
      recorderRef.current = recorder;
      setIsRecording(true);
      setIsPaused(false);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to access microphone",
      );
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    recorderRef.current = null;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_session" }));
    }

    setIsRecording(false);
    setIsPaused(false);
  }, []);

  const pauseRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === "recording") {
      recorderRef.current.pause();
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "pause" }));
    }
    setIsPaused(true);
  }, []);

  const resumeRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === "paused") {
      recorderRef.current.resume();
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "resume" }));
    }
    setIsPaused(false);
  }, []);

  const disconnect = useCallback(() => {
    stopRecording();
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, [stopRecording]);

  const clearTranscript = useCallback(() => {
    setFinalTexts([]);
    setPartialText("");
  }, []);

  return {
    // State
    isRecording,
    isPaused,
    connected,
    partialText,
    finalTexts,
    fullTranscript: finalTexts.join(" "),
    voiceCommand,
    metrics,
    error,
    // Actions
    connect,
    disconnect,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearTranscript,
  };
}
