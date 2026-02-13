# FIX10: Register All New Audiobook Sub-Routers in main.py

## Task
Update `backend/app/main.py` to register all new audiobook sub-routers that were created by workers FIX01, FIX03, FIX05, FIX07. Also register the existing `router_generation.py` that was never wired up.

## File to Modify: `backend/app/main.py`

### Current State
The file already has this VoiceForge section (around line 212):
```python
    # VoiceForge Integration
    from app.modules.audiobook.router import router as audiobook_router
    app.include_router(audiobook_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])
```

### Changes Needed
Add the following AFTER the existing `audiobook_router` registration, BEFORE the dictation routers:

```python
    from app.modules.audiobook.router_crud import router as audiobook_crud_router
    app.include_router(audiobook_crud_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_generation import router as audiobook_gen_router
    app.include_router(audiobook_gen_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_voices import router as audiobook_voices_router
    app.include_router(audiobook_voices_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_mastering import router as audiobook_mastering_router
    app.include_router(audiobook_mastering_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_export import router as audiobook_export_router
    app.include_router(audiobook_export_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])
```

## IMPORTANT
- Read main.py first to find the exact location
- Do NOT modify any other router registrations
- Keep the existing audiobook_router (SSML/pronunciation) as-is
- Keep the existing dictation routers as-is
- Keep the existing WebSocket routers as-is
- Make minimal, targeted edits only
