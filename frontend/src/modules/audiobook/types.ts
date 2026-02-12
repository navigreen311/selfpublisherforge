// ---------------------------------------------------------------------------
// Enums / Union Types
// ---------------------------------------------------------------------------

export type AudiobookStatus =
  | "draft"
  | "configuring"
  | "generating"
  | "reviewing"
  | "mastering"
  | "complete"
  | "published";

export type VoiceProvider = "coqui_xtts" | "elevenlabs" | "piper" | "custom_clone";

export type VoiceType = "narrator" | "character" | "custom";

export type ChapterAudioStatus =
  | "pending"
  | "preprocessing"
  | "generating"
  | "post_processing"
  | "review"
  | "approved"
  | "failed";

export type OutputFormat = "mp3" | "wav" | "flac" | "m4a" | "m4b";

export type TargetPlatform = "acx" | "findawayvoices" | "authors_republic" | "custom";

// ---------------------------------------------------------------------------
// Voice
// ---------------------------------------------------------------------------

export interface Voice {
  id: string;
  org_id: string;
  name: string;
  provider: VoiceProvider;
  voice_type: VoiceType;
  gender?: string;
  age_range?: string;
  accent?: string;
  language: string;
  sample_audio_url?: string;
  voice_settings: Record<string, unknown>;
  quality_score?: number;
  cost_per_minute?: number;
  is_system_voice: boolean;
  active: boolean;
}

// ---------------------------------------------------------------------------
// Project
// ---------------------------------------------------------------------------

export interface AudiobookProject {
  id: string;
  org_id: string;
  book_id: string;
  title?: string;
  status: AudiobookStatus;
  narrator_voice_id?: string;
  character_voices: Record<string, string>;
  narration_style: Record<string, unknown>;
  output_format: OutputFormat;
  sample_rate: number;
  bit_rate: number;
  channels: number;
  target_platform: TargetPlatform;
  total_chapters: number;
  completed_chapters: number;
  total_duration_seconds: number;
  estimated_cost?: number;
  actual_cost: number;
  master_audio_url?: string;
  cover_audio_url?: string;
  metadata: Record<string, unknown>;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Chapter
// ---------------------------------------------------------------------------

export interface QualityMetrics {
  naturalness_score?: number;
  clarity_score?: number;
  pace_consistency?: number;
  pronunciation_accuracy?: number;
  rms_db?: number;
  peak_db?: number;
}

export interface AudioEdit {
  start_ms: number;
  end_ms: number;
  type: string;
  replacement_text?: string;
  new_audio_url?: string;
}

export interface AudiobookChapter {
  id: string;
  audiobook_project_id: string;
  chapter_id?: string;
  chapter_number: number;
  chapter_title?: string;
  source_text: string;
  word_count: number;
  status: ChapterAudioStatus;
  voice_id?: string;
  ssml_text?: string;
  audio_url?: string;
  waveform_data?: { peaks: number[]; duration: number };
  duration_seconds: number;
  file_size_bytes: number;
  quality_metrics: QualityMetrics;
  review_notes?: string;
  audio_edits: AudioEdit[];
  cost_usd: number;
}

// ---------------------------------------------------------------------------
// Generation Job
// ---------------------------------------------------------------------------

export interface GenerationJob {
  id: string;
  audiobook_project_id: string;
  chapter_id?: string;
  job_type: string;
  status: string;
  priority: number;
  provider?: string;
  error_message?: string;
  cost_usd: number;
  celery_task_id?: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Cost
// ---------------------------------------------------------------------------

export interface CostEstimate {
  provider: string;
  estimated_duration_minutes: number;
  cost_per_minute: number;
  total_cost: number;
  word_count: number;
}

export interface CostBreakdown {
  estimates: CostEstimate[];
  recommended_provider: string;
  total_word_count: number;
  human_narrator_comparison: number;
}

// ---------------------------------------------------------------------------
// ACX Validation
// ---------------------------------------------------------------------------

export interface ACXCheck {
  name: string;
  passed: boolean;
  actual_value: string;
  expected_value: string;
  auto_fixable: boolean;
}

export interface ACXValidationResult {
  overall_pass: boolean;
  score: number;
  checks: ACXCheck[];
  auto_fixable_issues: string[];
}

// ---------------------------------------------------------------------------
// Pronunciation
// ---------------------------------------------------------------------------

export interface PronunciationEntry {
  id: string;
  word: string;
  phonetic: string;
  ssml_phoneme?: string;
  context?: string;
  audiobook_project_id?: string;
}

// ---------------------------------------------------------------------------
// SSML
// ---------------------------------------------------------------------------

export interface DialogueSegment {
  character: string;
  text: string;
  emotion?: string;
  start_index: number;
  end_index: number;
}

export interface SSMLResult {
  original_text: string;
  ssml_text: string;
  dialogue_segments: DialogueSegment[];
  emotion_segments: { text: string; emotion: string; intensity: number }[];
}

// ---------------------------------------------------------------------------
// WebSocket Events
// ---------------------------------------------------------------------------

export type AudiobookWSEvent =
  | {
      type: "chapter_generation_started";
      chapter_id: string;
      chapter_number: number;
    }
  | {
      type: "chapter_generation_progress";
      chapter_id: string;
      percent: number;
      stage: string;
      eta_seconds: number;
    }
  | {
      type: "chapter_generation_complete";
      chapter_id: string;
      audio_url: string;
      duration_seconds: number;
      cost_usd: number;
      quality_metrics: QualityMetrics;
    }
  | {
      type: "chapter_generation_failed";
      chapter_id: string;
      error: string;
      retry_available: boolean;
    }
  | {
      type: "mastering_progress";
      percent: number;
      stage: string;
    }
  | {
      type: "mastering_complete";
      master_url: string;
      total_duration: number;
      total_cost: number;
    }
  | {
      type: "validation_complete";
      results: ACXValidationResult;
    }
  | {
      type: "cost_update";
      chapter_id: string;
      cost_usd: number;
      total_cost: number;
      budget_remaining: number;
    };

// ---------------------------------------------------------------------------
// API Payloads
// ---------------------------------------------------------------------------

export interface CreateAudiobookProjectPayload {
  book_id: string;
  title?: string;
  narrator_voice_id?: string;
  output_format?: OutputFormat;
  target_platform?: TargetPlatform;
  settings?: Record<string, unknown>;
}

export interface UpdateAudiobookProjectPayload {
  title?: string;
  narrator_voice_id?: string;
  character_voices?: Record<string, string>;
  narration_style?: Record<string, unknown>;
  output_format?: OutputFormat;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
  target_platform?: TargetPlatform;
  settings?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
