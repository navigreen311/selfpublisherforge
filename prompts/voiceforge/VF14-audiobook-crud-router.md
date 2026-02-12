# VF14: Audiobook CRUD Router

## Task
Create the audiobook module with CRUD endpoints for audiobook projects and voices.

## Context
- Routers follow the pattern in `backend/app/modules/ai_writing/router.py`
- Use `APIRouter()`, `Depends(get_current_user)`, `Depends(get_db)`
- Auth returns `current_user: dict` with `id`, `org_id`, `email`, `tier`
- DB is `AsyncSession` from `app.database.get_db`

## Files to Create

### `backend/app/modules/audiobook/__init__.py`
```python
"""Audiobook Production Studio module."""
```

### `backend/app/modules/audiobook/router.py`

Implement these endpoints:

```
POST   /api/v1/audiobooks                    # Create audiobook project from book
GET    /api/v1/audiobooks                    # List audiobook projects (filtered by org)
GET    /api/v1/audiobooks/{id}               # Get audiobook project details with chapters
PATCH  /api/v1/audiobooks/{id}               # Update project settings
DELETE /api/v1/audiobooks/{id}               # Delete audiobook project

GET    /api/v1/audiobooks/voices             # List available voices (system + custom)
POST   /api/v1/audiobooks/voices             # Create custom voice (upload for cloning)
GET    /api/v1/audiobooks/voices/{id}/preview # Generate voice preview audio
DELETE /api/v1/audiobooks/voices/{id}        # Delete custom voice
```

Follow this pattern:
```python
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import schemas, service

router = APIRouter()

@router.post("", response_model=schemas.AudiobookProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_audiobook_project(
    request: schemas.AudiobookProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new audiobook project from an existing book."""
    return await service.create_project(db, current_user["org_id"], current_user["id"], request)

@router.get("", response_model=schemas.AudiobookProjectListResponse)
async def list_audiobook_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List audiobook projects for the current organization."""
    ...

# ... etc for all endpoints
```

### `backend/app/modules/audiobook/service.py`

Business logic layer:
```python
"""Business logic for audiobook projects and voices."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.audiobook import AudiobookProject, AudiobookVoice, AudiobookChapter
from app.modules.audiobook import schemas

async def create_project(db, org_id, user_id, request) -> AudiobookProject:
    # Create project, auto-populate chapters from book's manuscript
    ...

async def get_project(db, project_id, org_id) -> AudiobookProject:
    ...

async def list_projects(db, org_id, page, page_size, status_filter) -> dict:
    ...

async def update_project(db, project_id, org_id, request) -> AudiobookProject:
    ...

async def delete_project(db, project_id, org_id) -> bool:
    ...

async def list_voices(db, org_id) -> list:
    ...

async def create_voice_clone(db, org_id, name, files, provider) -> AudiobookVoice:
    ...

async def preview_voice(db, voice_id, sample_text) -> dict:
    ...

async def delete_voice(db, voice_id, org_id) -> bool:
    ...
```

When creating a project, auto-import chapters from the book's manuscript (query the `chapters` table for the book).

## Conventions
- Use schemas for request/response validation
- All queries filter by org_id for tenant isolation
- Return 404 with `HTTPException` for missing resources
- Use SQLAlchemy `select()` with `.where()` for queries
