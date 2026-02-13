# VF05: Pydantic Schemas — Dictation

## Task
Create Pydantic v2 schemas for voice dictation sessions, commands, refinement, and WebSocket messages.

## Context
- Create `backend/app/modules/dictation/schemas.py`
- Follow same patterns as other module schemas

## Schemas to Create

**Session Schemas:**
- DictationSessionCreate: book_id?: UUID, chapter_id?: UUID, language: str = 'en', asr_provider: str = 'faster_whisper', asr_model: str = 'large-v3'
- DictationSessionUpdate: status?: DictationStatus (active, paused, completed, abandoned)
- DictationSessionResponse: id, org_id, user_id, book_id?, chapter_id?, status, duration_seconds, words_dictated, words_after_refinement, raw_transcript?, refined_text?, asr_provider, asr_model, language, audio_recording_url?, refinement_applied, refinement_style_profile_id?, session_metrics, created_at, ended_at? (from_attributes)
- DictationSessionList: id, user_id, book_id?, chapter_id?, status, duration_seconds, words_dictated, created_at, ended_at?
- DictationSessionListResponse: items: list[DictationSessionList], total: int, page: int, page_size: int

**Refinement Schemas:**
- RefineRequest: style_profile_id?: UUID, options?: dict (auto_punctuate: bool = True, remove_fillers: bool = True, structure_paragraphs: bool = True, apply_style: bool = True)
- RefineTextRequest: text: str, style_profile_id?: UUID, options?: dict
- RefineResponse: raw_text: str, refined_text: str, diff: list[DiffSegment], style_match_score?: float, changes_summary: dict
- DiffSegment: type: str ('added', 'removed', 'unchanged', 'changed'), original_text: str, new_text: str, start_index: int, end_index: int

**Command Schemas:**
- DictationCommandCreate: command_phrase: str, action: str
- DictationCommandResponse: id, org_id, command_phrase, action, is_system, active, created_at (from_attributes)
- DictationCommandList: items: list[DictationCommandResponse], total: int

**Settings Schemas:**
- DictationSettings: language: str = 'en', auto_refine: bool = False, voice_commands_enabled: bool = True, auto_punctuate: bool = True, remove_fillers: bool = True, confidence_threshold: float = 0.7, default_style_profile_id?: UUID
- DictationSettingsUpdate: same as above, all optional

**WebSocket Message Schemas:**
- DictationClientMessage: type: str ('audio_chunk', 'pause', 'resume', 'end_session', 'set_language'), data?: bytes, language?: str
- DictationPartialTranscript: type: str = 'partial_transcript', text: str, confidence: float
- DictationFinalTranscript: type: str = 'final_transcript', text: str, confidence: float, words: list[WordTiming]
- DictationVoiceCommand: type: str = 'voice_command', command: str, action: str
- DictationError: type: str = 'error', message: str, recoverable: bool
- DictationMetrics: type: str = 'session_metrics', wpm: float, accuracy: float, duration: int
- DictationRefinementReady: type: str = 'refinement_ready', raw_text: str, refined_text: str, diff: list[DiffSegment]
- WordTiming: word: str, start_ms: int, end_ms: int, confidence: float

**Enums:**
- DictationStatus: active, paused, completed, abandoned
- DictationAction: new_paragraph, new_line, insert_period, insert_comma, insert_question_mark, delete_last_sentence, undo, apply_bold, apply_italic, chapter_break, stop_dictation, read_back
