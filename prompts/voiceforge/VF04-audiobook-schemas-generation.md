# VF04: Pydantic Schemas — Audiobook Generation, Export, & Validation

## Task
Create Pydantic v2 schemas for audiobook generation jobs, SSML, pronunciation, mastering, export, and ACX validation.

## Context
- Add to `backend/app/modules/audiobook/schemas.py` created by VF03 OR create a separate `backend/app/modules/audiobook/schemas_generation.py`
- Follow same patterns as VF03

## Schemas to Create

**Generation Schemas:**
- GenerateChapterRequest: voice_id?: UUID (override narrator), generation_params?: dict
- GenerateAllRequest: parallel: bool = False, voice_overrides?: dict[int, UUID] (chapter_number -> voice_id)
- RegenerateSegmentRequest: segment_index: int, replacement_text?: str, voice_id?: UUID
- ChapterApproveRequest: approved: bool, review_notes?: str
- GenerationJobResponse: id, audiobook_project_id, chapter_id?, job_type, status, priority, provider?, input_params, output, error_message?, retry_count, max_retries, started_at?, completed_at?, cost_usd, celery_task_id?, created_at (from_attributes)

**SSML Schemas:**
- SSMLGenerateRequest: chapter text is pulled from DB, options?: dict (emphasis_level, pause_duration, etc.)
- SSMLUpdateRequest: ssml_text: str
- SSMLResponse: chapter_id: UUID, original_text: str, ssml_text: str, dialogue_segments: list[DialogueSegment], emotion_segments: list[EmotionSegment]
- DialogueSegment: character: str, text: str, emotion?: str, start_index: int, end_index: int
- EmotionSegment: text: str, emotion: str, intensity: float, start_index: int, end_index: int

**Pronunciation Schemas:**
- PronunciationCreate: word: str, phonetic: str, ssml_phoneme?: str, context?: str, audiobook_project_id?: UUID
- PronunciationResponse: id, org_id, audiobook_project_id?, word, phonetic, ssml_phoneme?, audio_sample_url?, context?, active, created_at (from_attributes)
- PronunciationListResponse: items: list[PronunciationResponse], total: int

**Mastering & Export Schemas:**
- MasterRequest: normalize: bool = True, noise_gate: bool = True, compression: bool = True, eq: bool = True, room_tone: bool = True, target_rms_db: float = -20.0, target_peak_db: float = -3.0
- ExportRequest: format: OutputFormat = 'mp3', platform: TargetPlatform = 'acx', include_cover_art: bool = True, include_retail_sample: bool = True
- ExportResponse: id: UUID, status: str, download_url?: str, format: str, platform: str, file_size_bytes?: int, created_at: datetime
- ACXValidationResult: overall_pass: bool, score: int, checks: list[ACXCheck], auto_fixable_issues: list[str]
- ACXCheck: name: str, passed: bool, actual_value: str, expected_value: str, auto_fixable: bool

**Cost Schemas:**
- CostEstimate: provider: str, estimated_duration_minutes: float, cost_per_minute: float, total_cost: float, word_count: int
- CostBreakdown: estimates: list[CostEstimate], recommended_provider: str, total_word_count: int, human_narrator_comparison: float

**WebSocket Event Schemas:**
- AudiobookWSEvent: type: str (discriminator), chapter_id?: UUID, percent?: float, stage?: str, eta_seconds?: float, audio_url?: str, duration_seconds?: float, cost_usd?: float, quality_metrics?: dict, error?: str, retry_available?: bool, master_url?: str, total_duration?: float, total_cost?: float, results?: ACXValidationResult, budget_remaining?: float
- QualityMetrics: naturalness_score: float, clarity_score: float, pace_consistency: float, pronunciation_accuracy: float

## Conventions
- Use Pydantic Field validators where appropriate (e.g., target_rms_db between -30 and -10)
- All response schemas need `model_config = ConfigDict(from_attributes=True)`
