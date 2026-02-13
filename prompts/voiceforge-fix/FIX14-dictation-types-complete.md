# FIX14: Complete Dictation TypeScript Type Definitions

## Task
Add the missing `DictationSession` type and any other missing types to the dictation types file.

## File to Modify: `frontend/src/modules/dictation/types.ts`

### Current State
The file currently defines: `DictationSettings`, `DictationCommand`, `DiffSegment`, `LowConfidenceWord`, `VoiceCommandEvent`

### Missing Types to Add
Read `frontend/src/modules/dictation/hooks.ts` first to see which types are imported. Then add all missing ones.

```typescript
// ── Session Types ────────────────────────────────────────────────────────

export type DictationSessionStatus = "active" | "paused" | "completed" | "cancelled";

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

export interface CreateDictationSessionPayload {
  manuscript_id?: string;
  chapter_id?: string;
  language?: string;
  settings?: Partial<DictationSettings>;
}

export interface UpdateDictationSessionPayload {
  status?: DictationSessionStatus;
  raw_transcript?: string;
  refined_transcript?: string;
  word_count?: number;
}

export interface RefineSessionPayload {
  style_profile_id?: string;
  options?: {
    restore_punctuation?: boolean;
    remove_fillers?: boolean;
    match_style?: boolean;
  };
}

export interface RefineTextPayload {
  text: string;
  style_profile_id?: string;
}

export interface RefinementResult {
  original_text: string;
  refined_text: string;
  diff: DiffSegment[];
  style_match_score: number;
}

export interface CreateDictationCommandPayload {
  phrase: string;
  action: string;
  description?: string;
}

// ── WebSocket Types ──────────────────────────────────────────────────────

export interface DictationWSMessage {
  type: "partial_transcript" | "final_transcript" | "voice_command" | "error" | "session_metrics" | "session_paused" | "session_resumed" | "pong";
  text?: string;
  confidence?: number;
  words?: Array<{ word: string; start_ms: number; end_ms: number; confidence: number }>;
  command?: string;
  action?: string;
  message?: string;
  recoverable?: boolean;
  wpm?: number;
  accuracy?: number;
  duration?: number;
}

// ── Pagination ───────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  per_page?: number;
}
```

## IMPORTANT
- Read the existing types.ts first — KEEP all existing definitions
- Add new types AFTER the existing ones
- Verify every type imported in hooks.ts is defined
