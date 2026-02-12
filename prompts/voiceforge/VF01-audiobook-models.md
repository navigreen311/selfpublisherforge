# VF01: Audiobook Database Models & Migration

## Task
Create SQLAlchemy ORM models and Alembic migration for the audiobook production system.

## Context
- This project uses SQLAlchemy 2.0 async with mapped_column pattern
- All models inherit from `BaseModel` (has id, created_at, updated_at, deleted_at) or `TenantModel` (adds org_id) from `app.database`
- Models live in `backend/app/models/` and are imported in `backend/app/models/__init__.py`
- UUID primary keys with `server_default=text("gen_random_uuid()")`
- JSONB columns use `from sqlalchemy.dialects.postgresql import JSONB`
- See `backend/app/models/content.py` for the pattern

## Files to Create

### 1. `backend/app/models/audiobook.py`

Create these models following the project's mapped_column pattern:

```python
"""Audiobook production models — voices, projects, chapters, pronunciation, jobs."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text, Numeric, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import BaseModel, TenantModel
```

**AudiobookVoice(TenantModel)** — `audiobook_voices` table:
- name: String(255), NOT NULL
- provider: String(50), NOT NULL — enum: 'coqui_xtts', 'elevenlabs', 'piper', 'custom_clone'
- provider_voice_id: String(255), nullable
- voice_type: String(50), NOT NULL — enum: 'narrator', 'character', 'custom'
- gender: String(20), nullable — 'male', 'female', 'neutral'
- age_range: String(30), nullable
- accent: String(100), nullable
- language: String(10), default 'en'
- sample_audio_url: Text, nullable
- clone_source_url: Text, nullable
- voice_settings: JSONB, default {}
- quality_score: Float, nullable
- cost_per_minute: Numeric(10,4), nullable
- is_system_voice: Boolean, default False
- active: Boolean, default True

**AudiobookProject(TenantModel)** — `audiobook_projects` table:
- book_id: UUID, FK to books.id, NOT NULL, indexed
- title: String(500), nullable
- status: String(50), default 'draft' — enum: draft, configuring, generating, reviewing, mastering, complete, published
- narrator_voice_id: UUID, FK to audiobook_voices.id, nullable
- character_voices: JSONB, default {}
- narration_style: JSONB, default {}
- output_format: String(20), default 'mp3'
- sample_rate: Integer, default 44100
- bit_rate: Integer, default 192
- channels: Integer, default 1
- target_platform: String(50), default 'acx'
- total_chapters: Integer, default 0
- completed_chapters: Integer, default 0
- total_duration_seconds: Integer, default 0
- estimated_cost: Numeric(10,2), nullable
- actual_cost: Numeric(10,2), default 0
- master_audio_url: Text, nullable
- cover_audio_url: Text, nullable
- metadata_: JSONB, default {} (use metadata_ to avoid conflict with SA metadata)
- settings: JSONB, default {}
- created_by: UUID, FK to users.id, nullable
- Relationships: narrator_voice, chapters (list), generation_jobs (list)

**AudiobookChapter(BaseModel)** — `audiobook_chapters` table:
- audiobook_project_id: UUID, FK to audiobook_projects.id ON DELETE CASCADE, NOT NULL, indexed
- chapter_id: UUID, FK to chapters.id, nullable
- chapter_number: Integer, NOT NULL
- chapter_title: String(500), nullable
- source_text: Text, NOT NULL
- word_count: Integer, default 0
- status: String(50), default 'pending' — enum: pending, preprocessing, generating, post_processing, review, approved, failed
- voice_id: UUID, FK to audiobook_voices.id, nullable
- ssml_text: Text, nullable
- audio_url: Text, nullable
- waveform_data: JSONB, nullable
- duration_seconds: Float, default 0
- file_size_bytes: BigInteger, default 0
- generation_attempts: Integer, default 0
- generation_params: JSONB, default {}
- quality_metrics: JSONB, default {}
- review_notes: Text, nullable
- audio_edits: JSONB, default []
- cost_tokens: Integer, default 0
- cost_usd: Numeric(10,4), default 0

**AudiobookPronunciation(TenantModel)** — `audiobook_pronunciation` table:
- audiobook_project_id: UUID, FK to audiobook_projects.id, nullable (NULL = org-wide)
- word: String(255), NOT NULL
- phonetic: String(500), NOT NULL
- ssml_phoneme: String(500), nullable
- audio_sample_url: Text, nullable
- context: Text, nullable
- active: Boolean, default True

**AudiobookGenerationJob(BaseModel)** — `audiobook_generation_jobs` table:
- audiobook_project_id: UUID, FK to audiobook_projects.id, NOT NULL, indexed
- chapter_id: UUID, FK to audiobook_chapters.id, nullable
- job_type: String(50), NOT NULL — enum: chapter_generate, chapter_regenerate, segment_regenerate, master_merge, quality_check, format_convert
- status: String(50), default 'queued' — enum: queued, processing, completed, failed, cancelled
- priority: Integer, default 5
- provider: String(50), nullable
- input_params: JSONB, default {}
- output: JSONB, default {}
- error_message: Text, nullable
- retry_count: Integer, default 0
- max_retries: Integer, default 3
- started_at: DateTime(timezone=True), nullable
- completed_at: DateTime(timezone=True), nullable
- cost_usd: Numeric(10,4), default 0
- celery_task_id: String(255), nullable

Add appropriate indexes and string enums as Python enums.

### 2. Update `backend/app/models/__init__.py`
Add imports for all new audiobook models so they're visible to Alembic.

### 3. Create Alembic migration
Run: `cd backend && alembic revision --autogenerate -m "add audiobook production tables"`
If alembic can't run, create a manual migration file at `backend/migrations/versions/` with the SQL from the blueprint.

## Conventions
- Use str enums (class VoiceProvider(str, enum.Enum))
- Follow existing model patterns exactly
- All JSONB defaults should use `default=dict` or `server_default=text("'{}'::jsonb")`
- Add `__table_args__` with relevant indexes
