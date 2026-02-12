# VF18: Dictation Router & Service

## Task
Create the dictation module with session CRUD, voice commands, settings, and refinement endpoints.

## Files to Create

### `backend/app/modules/dictation/__init__.py`
```python
"""Voice Dictation module for the AI Writing Studio."""
```

### `backend/app/modules/dictation/router.py`

```
POST   /api/v1/dictation/sessions                    # Start new dictation session
PATCH  /api/v1/dictation/sessions/{id}               # Update session (pause, resume, end)
GET    /api/v1/dictation/sessions/{id}                # Get session details & transcript
GET    /api/v1/dictation/sessions                     # List user's sessions

POST   /api/v1/dictation/sessions/{id}/refine         # Apply style refinement to raw transcript
POST   /api/v1/dictation/refine-text                  # One-off: refine arbitrary text

GET    /api/v1/dictation/commands                     # List available voice commands
POST   /api/v1/dictation/commands                     # Create custom voice command
DELETE /api/v1/dictation/commands/{id}                # Delete custom voice command

GET    /api/v1/dictation/settings                     # Get user dictation preferences
PATCH  /api/v1/dictation/settings                     # Update preferences
```

### `backend/app/modules/dictation/service.py`

```python
"""Business logic for dictation sessions and voice commands."""

async def create_session(db, org_id, user_id, request) -> DictationSession:
    ...

async def update_session(db, session_id, user_id, request) -> DictationSession:
    """Update session status, save transcript, etc."""
    ...

async def get_session(db, session_id, user_id) -> DictationSession:
    ...

async def list_sessions(db, user_id, page, page_size) -> dict:
    ...

async def refine_session(db, session_id, user_id, request) -> dict:
    """Apply DictationRefiner to session's raw transcript."""
    from app.services.voiceforge.dictation_refiner import DictationRefiner
    refiner = DictationRefiner()
    session = await get_session(db, session_id, user_id)
    result = await refiner.refine_transcript(
        session.raw_transcript or "",
        style_profile_id=str(request.style_profile_id) if request.style_profile_id else None,
    )
    session.refined_text = result.refined_text
    session.refinement_applied = True
    session.words_after_refinement = len(result.refined_text.split())
    await db.flush()
    return result

async def refine_text(text, style_profile_id=None) -> dict:
    """One-off refinement of arbitrary text."""
    from app.services.voiceforge.dictation_refiner import DictationRefiner
    refiner = DictationRefiner()
    return await refiner.refine_transcript(text, style_profile_id)

async def list_commands(db, org_id) -> list:
    """List all voice commands (system + custom for org)."""
    ...

async def create_command(db, org_id, request) -> DictationCommand:
    ...

async def delete_command(db, command_id, org_id) -> bool:
    ...

# Seed default system commands on first access
SYSTEM_COMMANDS = [
    ("new paragraph", "new_paragraph"),
    ("new line", "new_line"),
    ("period", "insert_period"),
    ("comma", "insert_comma"),
    ("question mark", "insert_question_mark"),
    ("delete that", "delete_last_sentence"),
    ("undo", "undo"),
    ("bold that", "apply_bold"),
    ("italic that", "apply_italic"),
    ("chapter break", "chapter_break"),
    ("stop dictation", "stop_dictation"),
    ("read that back", "read_back"),
]
```

## Conventions
- Sessions are user-scoped (filter by user_id)
- Commands are org-scoped (system + org-custom)
- Settings stored in Redis or user preferences JSON
