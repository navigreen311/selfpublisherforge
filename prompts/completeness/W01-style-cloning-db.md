# W01: Style Cloning — Full DB Persistence

## Files to modify
- `backend/app/models/content.py` — Add columns to StyleProfile
- `backend/app/modules/style_cloning/service.py` — Rewrite for DB
- `backend/app/modules/style_cloning/router.py` — Add auth + db deps

## Task

### 1. Add missing columns to StyleProfile in `app/models/content.py`

The existing StyleProfile model only has: name, voice_fingerprint, vocabulary_stats, sentence_patterns, sample_sources. Add these columns after the existing ones:

```python
description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
genre: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
sample_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
style_card: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
sample_texts: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
```

### 2. Rewrite service.py to use DB

Remove `_store`, `_ProfileRecord`, `_reset_store` entirely. Import StyleProfile from app.models.content. Change all functions to require `db: AsyncSession` as first parameter. Use ORM queries:

- `create_profile(db, org_id, request)` → create StyleProfile ORM instance, db.add(), db.flush(), db.refresh()
- `list_profiles(db, org_id)` → select(StyleProfile).where(org_id==, deleted_at==None)
- `get_profile(db, profile_id, org_id)` → select + scalar_one_or_none
- `get_fingerprint(db, profile_id, org_id)` → same, return fingerprint dict
- `analyze_profile(db, profile_id, org_id, sample_texts)` → update model, run NLP
- `delete_profile(db, profile_id, org_id)` → set deleted_at
- `conformity_check(db, profile_id, org_id, text)` → load profile, run check

Keep the NLP pipeline functions (ingest_text, merge_segmented, extract_all_features, etc.) unchanged.

For `_to_response()`, convert ORM to ProfileResponse. Store style_card as dict in JSONB, reconstruct StyleCard from dict in response.

For voice_fingerprint, store the VoiceFingerprint as dict in the existing JSONB column.

### 3. Update router.py

Replace `_get_org_id` with proper auth:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user

# In each endpoint:
async def create_profile(
    body: CreateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    return await service.create_profile(db, org_id, body)
```

Do this for ALL endpoints. Remove the `_get_org_id` helper entirely.
