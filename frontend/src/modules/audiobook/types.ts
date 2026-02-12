// Audiobook module types
// Chapter audio statuses for the generation pipeline
export type ChapterAudioStatus =
  | "pending"
  | "preprocessing"
  | "generating"
  | "post_processing"
  | "review"
  | "approved"
  | "failed";

export interface QualityMetrics {
  naturalness_score?: number;
  clarity_score?: number;
  pace_consistency?: number;
  pronunciation_accuracy?: number;
  rms_db?: number;
  peak_db?: number;
}

export interface AudioEdit {
  id: string;
  segment_index: number;
  original_text: string;
  edited_text?: string;
  edit_type: "regenerate" | "trim" | "replace" | "insert_pause";
  status: "pending" | "processing" | "complete" | "failed";
  created_at: string;
}

export interface SentenceTiming {
  index: number;
  text: string;
  start_time: number;
  end_time: number;
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
  sentence_timings?: SentenceTiming[];
  cost_usd: number;
}

// Project-level types
export type ProjectStatus =
  | "draft"
  | "configuring"
  | "generating"
  | "reviewing"
  | "mastering"
  | "complete"
  | "published";

export interface AudiobookProject {
  id: string;
  title: string;
  status: ProjectStatus;
  target_platform: string;
  total_chapters: number;
  completed_chapters: number;
  total_duration_seconds: number;
  estimated_cost_usd: number;
  actual_cost_usd: number;
  narrator_voice_id?: string;
  output_format: string;
  sample_rate: number;
  created_at: string;
  updated_at: string;
}

export interface CreateAudiobookProjectPayload {
  title: string;
  target_platform?: string;
  narrator_voice_id?: string;
  output_format?: string;
  sample_rate?: number;
}

export interface UpdateAudiobookProjectPayload {
  title?: string;
  target_platform?: string;
  narrator_voice_id?: string;
  output_format?: string;
  sample_rate?: number;
  status?: ProjectStatus;
}

// Voice types
export interface Voice {
  id: string;
  name: string;
  provider: string;
  language: string;
  accent?: string;
  gender: string;
  preview_url?: string;
  styles?: string[];
}

// Generation types
export interface GenerationJob {
  id: string;
  status: "queued" | "processing" | "complete" | "failed";
  chapter_id?: string;
  progress: number;
  stage?: string;
  error?: string;
  created_at: string;
}

// Cost estimation
export interface CostBreakdown {
  total_usd: number;
  per_chapter: { chapter_id: string; cost_usd: number }[];
  provider: string;
  estimated_duration_seconds: number;
}

// ACX validation
export interface ACXValidationResult {
  valid: boolean;
  checks: {
    name: string;
    passed: boolean;
    message: string;
    value?: number;
    threshold?: number;
  }[];
}

// Pronunciation
export interface PronunciationEntry {
  id: string;
  word: string;
  phonetic: string;
  audiobook_project_id?: string;
}

// WebSocket events
export interface AudiobookWSEvent {
  type:
    | "chapter_generation_progress"
    | "chapter_generation_complete"
    | "chapter_generation_failed"
    | "mastering_progress"
    | "mastering_complete";
  chapter_id: string;
  percent: number;
  stage: string;
  error?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}
