export interface DictationSettings {
  language: string;
  microphoneDeviceId: string;
  autoRefine: boolean;
  voiceCommandsEnabled: boolean;
}

export interface DictationCommand {
  id: string;
  phrase: string;
  action: string;
  active: boolean;
  builtIn: boolean;
}

export interface DiffSegment {
  type: "unchanged" | "added" | "removed" | "changed";
  rawText: string;
  refinedText: string;
}

export interface LowConfidenceWord {
  word: string;
  confidence: number;
  index: number;
}

export interface VoiceCommandEvent {
  command: string;
  action: string;
}

// ── Session Types ────────────────────────────────────────────────────────

export type DictationSessionStatus =
  | "active"
  | "paused"
  | "completed"
  | "cancelled";

export interface DictationSession {
  id: string;
  org_id: string;
  user_id: string;
  manuscript_id: string | null;
  chapter_id: string | null;
  status: DictationSessionStatus;
  language: string;
  raw_transcript: string;
  refined_transcript: string | null;
  word_count: number;
  duration_seconds: number;
  words_dictated: number;
  accuracy: number | null;
  settings: DictationSettings;
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  manuscript_id?: string;
  chapter_id?: string;
  language?: string;
  settings?: Partial<DictationSettings>;
}

export interface UpdateSessionRequest {
  status?: DictationSessionStatus;
  raw_transcript?: string;
  refined_transcript?: string;
  word_count?: number;
}

export interface RefineSessionRequest {
  style_profile_id?: string;
  options?: {
    restore_punctuation?: boolean;
    remove_fillers?: boolean;
    match_style?: boolean;
  };
}

export interface RefineTextRequest {
  text: string;
  style_profile_id?: string;
}

export interface RefineTextResponse {
  original_text: string;
  refined_text: string;
  diff: DiffSegment[];
  style_match_score: number;
}

export interface CreateCommandRequest {
  phrase: string;
  action: string;
  description?: string;
}

// ── WebSocket Types ──────────────────────────────────────────────────────

export interface DictationServerMessage {
  type:
    | "partial_transcript"
    | "final_transcript"
    | "voice_command"
    | "error"
    | "session_metrics"
    | "session_paused"
    | "session_resumed"
    | "pong";
  text: string;
  confidence?: number;
  words?: Array<{
    word: string;
    start_ms: number;
    end_ms: number;
    confidence: number;
  }>;
  command: string;
  action: string;
  message: string;
  recoverable?: boolean;
  wpm: number;
  accuracy: number;
  duration: number;
}

// ── Pagination ───────────────────────────────────────────────────────────

export interface SessionListResponse {
  items: DictationSession[];
  total: number;
  page?: number;
  per_page?: number;
}
