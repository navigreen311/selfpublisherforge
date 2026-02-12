# VF02: Dictation Database Models & Migration

## Task
Create SQLAlchemy ORM models and Alembic migration for the voice dictation system.

## Context
- Same patterns as VF01 — see `backend/app/models/content.py` and `backend/app/database.py`
- Models inherit from `BaseModel` (id, created_at, updated_at, deleted_at) or `TenantModel` (adds org_id)
- UUID PKs, JSONB columns, DateTime(timezone=True)

## Files to Create

### 1. `backend/app/models/dictation.py`

```python
"""Voice dictation models — sessions, commands."""
import enum
import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import BaseModel, TenantModel
```

**DictationSession(TenantModel)** — `dictation_sessions` table:
- user_id: UUID, FK to users.id, NOT NULL, indexed
- book_id: UUID, FK to books.id, nullable
- chapter_id: UUID, FK to chapters.id, nullable, indexed
- status: String(50), default 'active' — enum: active, paused, completed, abandoned
- duration_seconds: Integer, default 0
- words_dictated: Integer, default 0
- words_after_refinement: Integer, default 0
- raw_transcript: Text, nullable
- refined_text: Text, nullable
- asr_provider: String(50), default 'faster_whisper'
- asr_model: String(100), default 'large-v3'
- language: String(10), default 'en'
- audio_recording_url: Text, nullable
- refinement_applied: Boolean, default False
- refinement_style_profile_id: UUID, FK to style_profiles.id, nullable
- session_metrics: JSONB, default {}
- ended_at: DateTime(timezone=True), nullable

**DictationCommand(TenantModel)** — `dictation_commands` table:
- command_phrase: String(255), NOT NULL
- action: String(100), NOT NULL — e.g., 'new_paragraph', 'delete_last_sentence', 'apply_bold'
- is_system: Boolean, default True
- active: Boolean, default True

Use Python str enums for status values.

### 2. Update `backend/app/models/__init__.py`
Add imports for DictationSession and DictationCommand.

### 3. Create Alembic migration
`cd backend && alembic revision --autogenerate -m "add dictation tables"`
If alembic can't run, create manual migration SQL.

## Conventions
- Follow exact same patterns as existing models in `backend/app/models/content.py`
- Index on user_id, chapter_id for dictation_sessions
- Index on command_phrase for dictation_commands
