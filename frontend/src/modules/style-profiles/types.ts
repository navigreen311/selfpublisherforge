/**
 * TypeScript types for the Style Cloning Engine.
 */

// ── Enums ───────────────────────────────────────────────────────

export type ProfileStatus = "pending" | "analyzing" | "ready" | "failed";

export type ManuscriptFormat = "docx" | "epub" | "pdf" | "txt";

// ── Voice Fingerprint sub-models ────────────────────────────────

export interface VocabularyMetrics {
  unique_word_count: number;
  total_word_count: number;
  lexical_density: number;
  type_token_ratio: number;
  rare_word_frequency: number;
  reading_level: number;
  avg_word_length: number;
  top_words: [string, number][];
}

export interface SentenceMetrics {
  avg_length: number;
  length_variance: number;
  min_length: number;
  max_length: number;
  simple_ratio: number;
  compound_ratio: number;
  complex_ratio: number;
  question_ratio: number;
  exclamation_ratio: number;
}

export interface ParagraphMetrics {
  avg_length: number;
  avg_word_count: number;
  transition_word_density: number;
  short_paragraph_ratio: number;
  long_paragraph_ratio: number;
}

export interface RhetoricalMetrics {
  metaphor_density: number;
  simile_density: number;
  humor_marker_density: number;
  emotional_intensity: number;
  alliteration_density: number;
  rhetorical_question_density: number;
}

export interface DialogueMetrics {
  dialogue_ratio: number;
  avg_dialogue_length: number;
  said_tag_ratio: number;
  action_beat_ratio: number;
  dialogue_to_narrative_ratio: number;
}

export interface VoiceFingerprint {
  vocabulary: VocabularyMetrics;
  sentence: SentenceMetrics;
  paragraph: ParagraphMetrics;
  rhetorical: RhetoricalMetrics;
  dialogue: DialogueMetrics;
  voice_vector: number[];
  dimension_labels: string[];
}

export interface StyleCard {
  summary: string;
  tone: string;
  pacing: string;
  vocabulary_level: string;
  sentence_style: string;
  paragraph_style: string;
  rhetorical_style: string;
  dialogue_style: string;
  example_prompts: string[];
  key_metrics: Record<string, number>;
}

// ── Request / Response ──────────────────────────────────────────

export interface CreateProfileRequest {
  name: string;
  description?: string;
  genre?: string;
  sample_texts?: string[];
  file_format?: ManuscriptFormat;
}

export interface AnalyzeRequest {
  sample_texts: string[];
}

export interface GenerateSampleRequest {
  prompt: string;
  max_words?: number;
}

export interface GenerateSampleResponse {
  profile_id: string;
  prompt: string;
  generated_text: string;
}

export interface ConformityCheckRequest {
  text: string;
}

export interface ConformityCheckResult {
  overall_score: number;
  vocabulary_score: number;
  sentence_score: number;
  paragraph_score: number;
  rhetorical_score: number;
  dialogue_score: number;
  feedback: string[];
}

export interface ProfileResponse {
  id: string;
  org_id: string;
  name: string;
  description: string;
  genre: string;
  status: ProfileStatus;
  word_count: number;
  sample_count: number;
  confidence: number;
  style_card: StyleCard | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileListResponse {
  items: ProfileResponse[];
  total: number;
}

export interface FingerprintResponse {
  profile_id: string;
  fingerprint: VoiceFingerprint;
}
