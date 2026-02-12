/**
 * TypeScript types for the Dictation module.
 */

// ── Enums ───────────────────────────────────────────────────────

export type DictationStatus = "active" | "paused" | "completed" | "abandoned";

// ── Session Metrics ─────────────────────────────────────────────

export interface SessionMetrics {
  accuracy?: number;
  confidence_avg?: number;
  noise_level?: number;
  pauses?: number;
}

// ── Core Models ─────────────────────────────────────────────────

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

export interface WordTiming {
  word: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
}

export interface DiffSegment {
  type: "added" | "removed" | "unchanged" | "changed";
  original_text: string;
  new_text: string;
}

// ── Commands & Settings ─────────────────────────────────────────

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

// ── Request / Response ──────────────────────────────────────────

export interface CreateSessionRequest {
  book_id?: string;
  chapter_id?: string;
  language?: string;
  asr_provider?: string;
  asr_model?: string;
}

export interface UpdateSessionRequest {
  status?: DictationStatus;
  raw_transcript?: string;
  refined_text?: string;
  refinement_applied?: boolean;
  refinement_style_profile_id?: string;
}

export interface RefineSessionRequest {
  style_profile_id?: string;
}

export interface RefineTextRequest {
  text: string;
  style_profile_id?: string;
}

export interface RefineTextResponse {
  raw_text: string;
  refined_text: string;
  diff: DiffSegment[];
}

export interface CreateCommandRequest {
  command_phrase: string;
  action: string;
}

export interface SessionListResponse {
  items: DictationSession[];
  total: number;
  page: number;
  page_size: number;
}

// ── WebSocket Messages ──────────────────────────────────────────

export type DictationServerMessage =
  | { type: "partial_transcript"; text: string; confidence: number }
  | { type: "final_transcript"; text: string; confidence: number; words: WordTiming[] }
  | { type: "voice_command"; command: string; action: string }
  | { type: "error"; message: string; recoverable: boolean }
  | { type: "session_metrics"; wpm: number; accuracy: number; duration: number }
  | { type: "refinement_ready"; raw_text: string; refined_text: string; diff: DiffSegment[] }
  | { type: "session_paused" }
  | { type: "session_resumed" }
  | { type: "pong" };

export type DictationClientMessage =
  | { type: "pause" }
  | { type: "resume" }
  | { type: "end_session" }
  | { type: "ping" };
