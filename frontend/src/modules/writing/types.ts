export interface ChapterContent {
  id: string;
  book_id: string;
  title: string;
  content: string;
  order: number;
  synopsis: string;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface ManuscriptResponse {
  book_id: string;
  title: string;
  chapters: ChapterContent[];
  total_word_count: number;
}

export interface ReadabilityScore {
  flesch_kincaid_grade: number;
  flesch_reading_ease: number;
  gunning_fog: number;
  smog_index: number;
  word_count: number;
  sentence_count: number;
  syllable_count: number;
  avg_words_per_sentence: number;
  avg_syllables_per_word: number;
  reading_level: string;
}

export interface ManuscriptAnalysis {
  book_id: string;
  readability: ReadabilityScore;
  total_word_count: number;
  chapter_count: number;
  avg_chapter_word_count: number;
  pacing_notes: string[];
}

export interface OutlineChapter {
  title: string;
  synopsis: string;
  key_points: string[];
}

export interface OutlineResponse {
  book_id: string;
  chapters: OutlineChapter[];
  summary: string;
  generated_at: string;
}

export interface GenerateRequest {
  generation_type: string;
  project_id: string;
  style_profile_id?: string;
  instructions: string;
  context: Record<string, unknown>;
  model_preference?: string;
  stream?: boolean;
  quality_checks?: string[];
}

export interface WritingSessionCreate {
  book_id: string;
  words_written: number;
  duration_minutes: number;
  chapter_id?: string;
  notes?: string;
}

export interface SSEStreamState {
  content: string;
  isStreaming: boolean;
  error: string | null;
  qualityResults: Record<string, unknown> | null;
  completeMeta: Record<string, unknown> | null;
}

export interface StandaloneOutlineRequest {
  book_title: string;
  genre: string;
  target_audience?: string;
  num_chapters: number;
  premise?: string;
  tone: string;
}

export interface ChapterOutline {
  chapter_number: number;
  title: string;
  description: string;
  key_points: string[];
  estimated_word_count: number;
}

export interface StandaloneOutlineResponse {
  book_title: string;
  genre: string;
  total_chapters: number;
  chapters: ChapterOutline[];
  synopsis: string;
}

export interface BookEntry {
  id: string;
  title: string;
  subtitle?: string;
  status: string;
  format?: string;
  project_id?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
  /** Populated by the backend join or computed field */
  chapter_count?: number;
  word_count?: number;
}

export interface WritingSessionEntry {
  id: string;
  user_id: string;
  book_id: string;
  words_written: number;
  duration_minutes: number;
  chapter_id?: string | null;
  notes?: string;
  created_at: string;
  /** Populated via join or separate lookup */
  book_title?: string;
}

export type SaveStatus = "idle" | "saving" | "saved" | "error";
