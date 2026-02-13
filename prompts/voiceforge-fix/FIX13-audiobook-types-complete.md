# FIX13: Complete Audiobook TypeScript Type Definitions

## Task
Add all missing type definitions to the audiobook types file. The hooks file imports many types that don't exist yet.

## File to Modify: `frontend/src/modules/audiobook/types.ts`

### Current State
The file currently only defines: `ChapterAudioStatus`, `QualityMetrics`, `AudioEdit`, `SentenceTiming`, `AudiobookChapter`

### Missing Types to Add
Read `frontend/src/modules/audiobook/hooks.ts` first to see exactly which types are imported. Then add all of them.

```typescript
// ── Project Types ────────────────────────────────────────────────────────

export type AudiobookProjectStatus =
  | "draft" | "configuring" | "generating" | "reviewing"
  | "mastering" | "complete" | "published";

export interface AudiobookProject {
  id: string;
  org_id: string;
  book_id: string;
  title: string | null;
  status: AudiobookProjectStatus;
  narrator_voice_id: string | null;
  character_voices: Record<string, string> | null;
  narration_style: Record<string, unknown> | null;
  output_format: string;
  sample_rate: number;
  bit_rate: number;
  channels: number;
  target_platform: string;
  total_chapters: number;
  completed_chapters: number;
  total_duration_seconds: number;
  estimated_cost: number | null;
  actual_cost: number;
  master_audio_url: string | null;
  cover_audio_url: string | null;
  settings: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  chapters?: AudiobookChapter[];
}

export interface CreateAudiobookProjectPayload {
  book_id: string;
  title?: string;
  narrator_voice_id?: string;
  output_format?: string;
  target_platform?: string;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
}

export interface UpdateAudiobookProjectPayload {
  title?: string;
  narrator_voice_id?: string;
  character_voices?: Record<string, string>;
  narration_style?: Record<string, unknown>;
  output_format?: string;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
  target_platform?: string;
  settings?: Record<string, unknown>;
}

// ── Voice Types ──────────────────────────────────────────────────────────

export type VoiceProvider = "coqui_xtts" | "elevenlabs" | "piper" | "custom_clone";
export type VoiceType = "narrator" | "character" | "custom";

export interface Voice {
  id: string;
  name: string;
  provider: VoiceProvider;
  provider_voice_id: string | null;
  voice_type: VoiceType;
  gender: string | null;
  age_range: string | null;
  accent: string | null;
  language: string;
  sample_audio_url: string | null;
  quality_score: number | null;
  cost_per_minute: number | null;
  is_system_voice: boolean;
  active: boolean;
}

// ── Generation Types ─────────────────────────────────────────────────────

export type GenerationJobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled";
export type GenerationJobType =
  | "chapter_generate" | "chapter_regenerate" | "segment_regenerate"
  | "master_merge" | "quality_check" | "format_convert";

export interface GenerationJob {
  id: string;
  audiobook_project_id: string;
  chapter_id: string | null;
  job_type: GenerationJobType;
  status: GenerationJobStatus;
  priority: number;
  provider: string | null;
  progress_percent?: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  cost_usd: number;
  celery_task_id: string | null;
}

// ── Cost Types ───────────────────────────────────────────────────────────

export interface ProviderCost {
  provider: VoiceProvider;
  cost_per_minute: number;
  estimated_minutes: number;
  total_cost: number;
}

export interface CostBreakdown {
  total_words: number;
  estimated_minutes: number;
  providers: ProviderCost[];
  recommended_provider: VoiceProvider;
  total_estimated_cost: number;
}

// ── Validation Types ─────────────────────────────────────────────────────

export interface ACXChapterResult {
  chapter_id: string;
  chapter_number: number;
  passed: boolean;
  issues: string[];
  peak_db: number | null;
  rms_db: number | null;
  noise_floor_db: number | null;
}

export interface ACXValidationResult {
  project_id: string;
  passed: boolean;
  chapters: ACXChapterResult[];
  summary: string;
}

// ── Pronunciation Types ──────────────────────────────────────────────────

export interface PronunciationEntry {
  id: string;
  org_id: string;
  audiobook_project_id: string | null;
  word: string;
  phonetic: string;
  ssml_phoneme: string | null;
  audio_sample_url: string | null;
  context: string | null;
  active: boolean;
  created_at: string;
}

// ── WebSocket Types ──────────────────────────────────────────────────────

export type AudiobookWSEventType =
  | "chapter_generation_started" | "chapter_generation_progress"
  | "chapter_generation_complete" | "chapter_generation_failed"
  | "mastering_progress" | "mastering_complete"
  | "validation_complete" | "cost_update";

export interface AudiobookWSEvent {
  type: AudiobookWSEventType;
  project_id: string;
  chapter_id?: string;
  chapter_number?: number;
  percent?: number;
  stage?: string;
  duration_seconds?: number;
  audio_url?: string;
  error?: string;
  total_cost_usd?: number;
  passed?: boolean;
  issues?: string[];
}

// ── Pagination ───────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
```

## IMPORTANT
- Read the existing types.ts first — KEEP all existing definitions
- Add new types AFTER the existing ones
- Make sure every type imported in hooks.ts is defined
- Check the components too (AudiobookStudio, VoicePicker, etc.) for any types they import
