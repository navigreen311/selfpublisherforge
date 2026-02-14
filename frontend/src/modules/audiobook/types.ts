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

export type AudiobookProjectStatus =
  | "draft"
  | "configuring"
  | "generating"
  | "recording"
  | "reviewing"
  | "mastering"
  | "mastered"
  | "exporting"
  | "complete"
  | "completed"
  | "archived";

export interface AudiobookProject {
  id: string;
  org_id: string;
  project_id: string;
  title: string;
  author?: string;
  narrator?: string;
  status: AudiobookProjectStatus;
  voice_id?: string;
  total_chapters: number;
  completed_chapters: number;
  total_duration_seconds: number;
  total_cost_usd: number;
  target_platform: string;
  created_at: string;
  updated_at: string;
}

// List item for audiobook projects overview/dashboard
export interface AudiobookProjectListItem {
  id: string;
  title: string;
  chapter_count: number;
  total_duration: number; // seconds
  narrator_name?: string;
  narrator_voice?: string;
  status: AudiobookProjectStatus;
  progress_percent: number; // 0-100
  cost_spent: number; // USD
  cost_budget?: number; // USD
  created_at: string;
}

export interface Voice {
  id: string;
  name: string;
  provider: string;
  gender: string;
  language: string;
  preview_url?: string;
  sample_url?: string | null;
  accent?: string;
  cost_tier?: string;
  cost_per_minute?: number;
}

// Voice sample for voice selection UI
export interface VoiceSample {
  id: string;
  name: string;
  gender: string;
  accent: string;
  description?: string;
  sample_url: string;
  tier: string; // e.g., "standard", "premium", "ultra"
}

export interface GenerationJob {
  id: string;
  audiobook_project_id: string;
  chapter_id?: string;
  job_type: string;
  status: string;
  priority: number;
  provider?: string;
  input_params: Record<string, unknown>;
  output: Record<string, unknown>;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  started_at?: string;
  completed_at?: string;
  cost_usd: number;
  celery_task_id?: string;
  created_at: string;
}

export interface CostBreakdown {
  total_cost_usd: number;
  per_chapter: { chapter_id: string; cost_usd: number }[];
  provider: string;
  estimated_duration_minutes: number;
}

export interface ACXValidationResult {
  valid: boolean;
  errors: { field: string; message: string }[];
  warnings: { field: string; message: string }[];
}

export interface PronunciationEntry {
  id: string;
  org_id: string;
  audiobook_project_id?: string;
  word: string;
  phonetic: string;
  ssml_phoneme?: string;
  audio_sample_url?: string;
  context?: string;
  active: boolean;
  created_at: string;
}

export interface AudiobookWSEvent {
  type: string;
  chapter_id: string;
  percent: number;
  stage: string;
  [key: string]: unknown;
}

export interface CreateAudiobookProjectPayload {
  title?: string;
  project_id?: string;
  book_id?: string;
  voice_id?: string;
  author?: string;
  narrator?: string;
  target_platform?: string;
  output_format?: string;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
  narration_style?: {
    pacing?: number;
    paragraph_pause?: number;
    chapter_pause?: number;
    emphasis?: string;
  };
  narration_speed?: number;
  budget_limit?: number;
}

// Request payload for creating an audiobook from creation wizard
export interface AudiobookCreateRequest {
  manuscript_id: string;
  voice_id: string;
  tier: string; // e.g., "standard", "premium", "ultra"
  target_platform?: string; // e.g., "ACX", "Findaway", "general"
  narration_speed?: number; // 0.75 - 1.5
  narration_style?: string; // e.g., "conversational", "dramatic", "neutral"
  budget_limit?: number; // USD
}

export interface NarrationStyle {
  pacing?: number;
  paragraph_pause?: number;
  chapter_pause?: number;
  emphasis?: string;
}

export interface UpdateAudiobookProjectPayload {
  title?: string;
  voice_id?: string;
  author?: string;
  narrator?: string;
  status?: AudiobookProjectStatus;
  output_format?: string;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
  target_platform?: string;
  narration_style?: NarrationStyle;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
