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

export type DictationStatus = "active" | "paused" | "ended";

export interface DictationSession {
  id: string;
  user_id: string;
  org_id: string;
  title?: string;
  project_id?: string;
  language: string;
  status: DictationStatus;
  raw_transcript?: string;
  refined_text?: string;
  refinement_applied: boolean;
  word_count: number;
  words_after_refinement?: number;
  duration_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface SessionListItem {
  id: string;
  title?: string;
  status: string;
  word_count: number;
  duration_seconds: number;
  refinement_applied: boolean;
  created_at: string;
}

export interface SessionListResponse {
  sessions: SessionListItem[];
  total: number;
}

export interface CreateSessionRequest {
  title?: string;
  project_id?: string;
  language?: string;
}

export interface UpdateSessionRequest {
  action: "pause" | "resume" | "end";
  raw_transcript?: string;
  duration_seconds?: number;
}

export interface RefineSessionRequest {
  style_profile_id?: string;
}

export interface RefineTextRequest {
  text: string;
  style_profile_id?: string;
}

export interface RefineTextResponse {
  refined_text: string;
  original_length: number;
  refined_length: number;
  style_profile_id?: string;
}

export interface CreateCommandRequest {
  trigger_phrase: string;
  action: string;
  description?: string;
}

export type DictationServerMessage =
  | { type: "partial_transcript"; text: string }
  | { type: "final_transcript"; text: string }
  | { type: "voice_command"; command: string; action: string }
  | { type: "session_metrics"; wpm: number; accuracy: number; duration: number }
  | { type: "error"; message: string }
  | { type: "session_paused" }
  | { type: "session_resumed" }
  | { type: "pong" };
