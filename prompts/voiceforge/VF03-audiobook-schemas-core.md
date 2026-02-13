# VF03: Pydantic Schemas — Audiobook Core (Projects & Voices)

## Task
Create Pydantic v2 schemas for audiobook projects and voices CRUD operations.

## Context
- Schemas live in `backend/app/modules/<module>/schemas.py`
- Use `from pydantic import BaseModel, ConfigDict, Field`
- Use `from uuid import UUID` and `from datetime import datetime`
- See `backend/app/modules/ai_writing/schemas.py` for the pattern
- All response schemas should have `model_config = ConfigDict(from_attributes=True)`

## Files to Create

### `backend/app/modules/audiobook/schemas.py`

Create these Pydantic models:

**Enums:**
- AudiobookStatus: draft, configuring, generating, reviewing, mastering, complete, published
- VoiceProvider: coqui_xtts, elevenlabs, piper, custom_clone
- VoiceType: narrator, character, custom
- OutputFormat: mp3, wav, flac, m4a, m4b
- TargetPlatform: acx, findawayvoices, authors_republic, custom
- ChapterAudioStatus: pending, preprocessing, generating, post_processing, review, approved, failed

**Voice Schemas:**
- VoiceBase: name, provider, voice_type, gender?, age_range?, accent?, language='en', voice_settings={}
- VoiceCreate(VoiceBase): pass (for creating custom voices)
- VoiceResponse(VoiceBase): id, org_id, provider_voice_id?, sample_audio_url?, clone_source_url?, quality_score?, cost_per_minute?, is_system_voice, active, created_at, updated_at (model_config from_attributes)
- VoicePreviewRequest: voice_id: UUID, sample_text: str = Field(max_length=500)
- VoiceCloneRequest: name: str, provider: VoiceProvider = VoiceProvider.coqui_xtts

**Project Schemas:**
- AudiobookProjectCreate: book_id: UUID, title?: str, narrator_voice_id?: UUID, output_format: OutputFormat = 'mp3', sample_rate: int = 44100, bit_rate: int = 192, channels: int = 1, target_platform: TargetPlatform = 'acx', narration_style: dict = {}, settings: dict = {}
- AudiobookProjectUpdate: title?: str, narrator_voice_id?: UUID, character_voices?: dict, narration_style?: dict, output_format?: OutputFormat, sample_rate?: int, bit_rate?: int, channels?: int, target_platform?: TargetPlatform, settings?: dict
- AudiobookProjectResponse: id, org_id, book_id, title, status, narrator_voice_id?, character_voices, narration_style, output_format, sample_rate, bit_rate, channels, target_platform, total_chapters, completed_chapters, total_duration_seconds, estimated_cost?, actual_cost, master_audio_url?, cover_audio_url?, metadata, settings, created_at, updated_at, created_by? (from_attributes)
- AudiobookProjectList: id, book_id, title, status, total_chapters, completed_chapters, total_duration_seconds, estimated_cost?, actual_cost, created_at

**Chapter Schemas:**
- ChapterAudioResponse: id, audiobook_project_id, chapter_id?, chapter_number, chapter_title?, source_text, word_count, status, voice_id?, ssml_text?, audio_url?, waveform_data?, duration_seconds, file_size_bytes, generation_attempts, quality_metrics, review_notes?, audio_edits, cost_usd, created_at, updated_at (from_attributes)

**Pagination:**
- AudiobookProjectListResponse: items: list[AudiobookProjectList], total: int, page: int, page_size: int
- VoiceListResponse: items: list[VoiceResponse], total: int

## Conventions
- All Optional fields use `X | None = None` pattern (not Optional[X])
- UUID fields as `UUID` type
- Use `Field(default_factory=dict)` for dict defaults
- Keep schemas in a single file, well-organized with section comments
