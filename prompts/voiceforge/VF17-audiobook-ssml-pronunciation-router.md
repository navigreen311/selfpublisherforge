# VF17: SSML & Pronunciation Router

## Task
Create endpoints for SSML generation/editing and pronunciation dictionary management.

## Files to Create/Modify

### Add to audiobook router

```
POST   /api/v1/audiobooks/{id}/chapters/{ch_id}/ssml          # Generate SSML from plain text
PATCH  /api/v1/audiobooks/{id}/chapters/{ch_id}/ssml          # Update SSML annotations
POST   /api/v1/audiobooks/pronunciation                       # Add pronunciation entry
GET    /api/v1/audiobooks/pronunciation                       # List pronunciation dictionary
DELETE /api/v1/audiobooks/pronunciation/{pron_id}              # Delete pronunciation entry
```

### Service functions

```python
async def generate_ssml(db, project_id, chapter_id, org_id, options=None) -> dict:
    """Generate SSML from chapter's plain text."""
    from app.services.voiceforge.ssml_generator import SSMLGenerator
    # 1. Get chapter source_text
    # 2. Get project's pronunciation dictionary
    # 3. Generate SSML via SSMLGenerator
    # 4. Save ssml_text to chapter
    # 5. Return SSML result with dialogue/emotion segments
    ...

async def update_ssml(db, project_id, chapter_id, org_id, ssml_text) -> dict:
    """Update chapter's SSML text (manual edits)."""
    # Validate SSML syntax
    # Save to chapter.ssml_text
    ...

async def add_pronunciation(db, org_id, request) -> dict:
    """Add a word to the pronunciation dictionary."""
    from app.models.audiobook import AudiobookPronunciation
    entry = AudiobookPronunciation(
        org_id=org_id,
        audiobook_project_id=request.audiobook_project_id,
        word=request.word,
        phonetic=request.phonetic,
        ssml_phoneme=request.ssml_phoneme,
        context=request.context,
    )
    db.add(entry)
    await db.flush()
    return entry

async def list_pronunciation(db, org_id, project_id=None) -> list:
    """List pronunciation entries for org (optionally filtered by project)."""
    from app.models.audiobook import AudiobookPronunciation
    from sqlalchemy import select
    query = select(AudiobookPronunciation).where(
        AudiobookPronunciation.org_id == org_id,
        AudiobookPronunciation.active == True,
    )
    if project_id:
        query = query.where(
            (AudiobookPronunciation.audiobook_project_id == project_id) |
            (AudiobookPronunciation.audiobook_project_id == None)
        )
    result = await db.execute(query)
    return list(result.scalars().all())

async def delete_pronunciation(db, pron_id, org_id) -> bool:
    """Soft-delete pronunciation entry."""
    ...
```
