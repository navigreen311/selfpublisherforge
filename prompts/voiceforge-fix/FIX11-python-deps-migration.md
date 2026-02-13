# FIX11: Add Missing Python Dependencies & Fix Migration

## Task
1. Add missing Python dependencies to requirements.txt
2. Rename the conflicting migration filename

## Files to Modify

### 1. `backend/requirements.txt`
Add these missing dependencies (append at the end of the VoiceForge section):
```
faster-whisper>=1.0.0
deepgram-sdk>=3.0.0
```

Read the file first to find where the VoiceForge deps section is (look for pydub, pyloudnorm, etc.) and add after them.

### 2. Rename migration file
The file `backend/migrations/versions/008_add_dictation_tables.py` uses the same "008" prefix as the audiobook migration. Rename it to `009_add_dictation_tables.py`.

Steps:
1. `git mv backend/migrations/versions/008_add_dictation_tables.py backend/migrations/versions/009_add_dictation_tables.py`
2. The content inside the file does NOT need to change (revision IDs are what Alembic uses, not filenames)

## Conventions
- Read files before modifying
- Only add/change what's specified
