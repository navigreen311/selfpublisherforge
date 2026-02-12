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
