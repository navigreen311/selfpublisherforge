# VF28: Frontend — Dictation Types, Hooks & Store

## Task
Create TypeScript types, React Query hooks, and state management for the dictation module.

## Files to Create

### `frontend/src/modules/dictation/types.ts`

```typescript
export type DictationStatus = 'active' | 'paused' | 'completed' | 'abandoned';

export interface DictationSession {
  id: string;
  org_id: string;
  user_id: string;
  book_id?: string;
  chapter_id?: string;
  status: DictationStatus;
  duration_seconds: number;
  words_dictated: number;
  words_after_refinement: number;
  raw_transcript?: string;
  refined_text?: string;
  asr_provider: string;
  asr_model: string;
  language: string;
  audio_recording_url?: string;
  refinement_applied: boolean;
  refinement_style_profile_id?: string;
  session_metrics: SessionMetrics;
  created_at: string;
  ended_at?: string;
}

export interface SessionMetrics {
  accuracy?: number;
  confidence_avg?: number;
  noise_level?: number;
  pauses?: number;
}

export interface WordTiming {
  word: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
}

export interface DiffSegment {
  type: 'added' | 'removed' | 'unchanged' | 'changed';
  original_text: string;
  new_text: string;
}

export interface DictationCommand {
  id: string;
  command_phrase: string;
  action: string;
  is_system: boolean;
  active: boolean;
}

export interface DictationSettings {
  language: string;
  auto_refine: boolean;
  voice_commands_enabled: boolean;
  auto_punctuate: boolean;
  remove_fillers: boolean;
  confidence_threshold: number;
  default_style_profile_id?: string;
}

// WebSocket messages
export type DictationServerMessage =
  | { type: 'partial_transcript'; text: string; confidence: number }
  | { type: 'final_transcript'; text: string; confidence: number; words: WordTiming[] }
  | { type: 'voice_command'; command: string; action: string }
  | { type: 'error'; message: string; recoverable: boolean }
  | { type: 'session_metrics'; wpm: number; accuracy: number; duration: number }
  | { type: 'refinement_ready'; raw_text: string; refined_text: string; diff: DiffSegment[] }
  | { type: 'session_paused' }
  | { type: 'session_resumed' }
  | { type: 'pong' };
```

### `frontend/src/modules/dictation/hooks.ts`

```typescript
"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRef, useState, useCallback, useEffect } from "react";
// import RecordRTC from "recordrtc";

// CRUD hooks
export function useDictationSessions(page = 1, pageSize = 20) { ... }
export function useDictationSession(id: string) { ... }
export function useCreateDictationSession() { ... }
export function useUpdateDictationSession() { ... }
export function useRefineSession() { ... }
export function useRefineText() { ... }
export function useDictationCommands() { ... }
export function useCreateDictationCommand() { ... }
export function useDeleteDictationCommand() { ... }
export function useDictationSettings() { ... }
export function useUpdateDictationSettings() { ... }

// WebSocket + Audio Recording hook
export function useDictation(sessionId: string | null) {
  const [isRecording, setIsRecording] = useState(false);
  const [partialText, setPartialText] = useState('');
  const [finalTexts, setFinalTexts] = useState<string[]>([]);
  const [voiceCommand, setVoiceCommand] = useState<{ command: string; action: string } | null>(null);
  const [metrics, setMetrics] = useState<{ wpm: number; duration: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<any>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/ws/dictation/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case 'partial_transcript': setPartialText(msg.text); break;
        case 'final_transcript':
          setPartialText('');
          setFinalTexts(prev => [...prev, msg.text]);
          break;
        case 'voice_command': setVoiceCommand(msg); break;
        case 'session_metrics': setMetrics(msg); break;
        case 'error': setError(msg.message); break;
      }
    };

    wsRef.current = ws;
  }, [sessionId]);

  const startRecording = useCallback(async () => {
    // Use RecordRTC or MediaRecorder to capture mic audio
    // Send audio chunks to WebSocket as binary frames
    // 16kHz, 16-bit PCM, 250ms chunks
    ...
  }, []);

  const stopRecording = useCallback(() => {
    recorderRef.current?.stopRecording();
    wsRef.current?.send(JSON.stringify({ type: 'end_session' }));
    setIsRecording(false);
  }, []);

  const pauseRecording = useCallback(() => {
    recorderRef.current?.pauseRecording();
    wsRef.current?.send(JSON.stringify({ type: 'pause' }));
  }, []);

  const resumeRecording = useCallback(() => {
    recorderRef.current?.resumeRecording();
    wsRef.current?.send(JSON.stringify({ type: 'resume' }));
  }, []);

  return {
    isRecording, partialText, finalTexts, voiceCommand, metrics, error,
    connect, startRecording, stopRecording, pauseRecording, resumeRecording,
    fullTranscript: finalTexts.join(' '),
  };
}
```

### `frontend/src/modules/dictation/store.ts`

Zustand store for dictation UI state (active session, audio level, recording state).
