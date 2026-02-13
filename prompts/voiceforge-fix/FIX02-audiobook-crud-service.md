# FIX02: Audiobook Project CRUD Service

## Task
Create the service layer for audiobook project CRUD operations.

## File to Create: `backend/app/modules/audiobook/service_crud.py`

### Patterns to Follow
- Look at `backend/app/modules/audiobook/service.py` for import/style conventions
- Functional style (no classes), async functions, `db: AsyncSession` + `org_id: UUID` params
- Use `from sqlalchemy import select, func` and `from sqlalchemy.ext.asyncio import AsyncSession`
- Import models from `app.models.audiobook`
- Soft delete pattern: set `deleted_at = datetime.now(UTC)`, filter `where(Model.deleted_at.is_(None))`

### Functions to Implement

```python
async def create_project(db: AsyncSession, org_id: UUID, data) -> AudiobookProject:
    """Create a new audiobook project linked to a book.
    - Validate book_id belongs to org
    - Auto-populate chapters from the book's manuscript chapters
    - Set initial status to 'draft'
    - Calculate estimated word count from chapters
    """

async def list_projects(db: AsyncSession, org_id: UUID, page: int, per_page: int, status: str | None) -> dict:
    """List audiobook projects for an org with pagination.
    - Filter by org_id, optional status filter
    - Exclude soft-deleted
    - Order by created_at desc
    - Return {items: [...], total: int, page: int, per_page: int}
    """

async def get_project(db: AsyncSession, project_id: UUID, org_id: UUID) -> AudiobookProject | None:
    """Get a single project with its chapters loaded.
    - Use selectinload for chapters relationship
    - Filter by org_id for tenant isolation
    """

async def update_project(db: AsyncSession, project_id: UUID, org_id: UUID, data) -> AudiobookProject | None:
    """Update project settings.
    - Only update fields that are provided (partial update)
    - Can update: title, narrator_voice_id, character_voices, narration_style,
      output_format, sample_rate, bit_rate, channels, target_platform, settings
    """

async def delete_project(db: AsyncSession, project_id: UUID, org_id: UUID) -> bool:
    """Soft-delete a project.
    - Set deleted_at timestamp
    - Return True if found and deleted, False if not found
    """
```

### Models to Import
```python
from app.models.audiobook import AudiobookProject, AudiobookChapter
from app.models.content import Chapter, Manuscript
```

## Conventions
- Read existing service.py first to match style
- Always scope queries by org_id
- Use `await db.commit()` and `await db.refresh(obj)` after mutations
- Use `from datetime import UTC, datetime` for timestamps
