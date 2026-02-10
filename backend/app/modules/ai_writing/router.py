"""API router for the AI Writing Studio module.

Endpoints:
  POST /generate                              -- Unified AI generation (SSE streaming)
  GET  /books/{id}/manuscript                 -- Get full manuscript
  GET  /books/{id}/manuscript/chapters        -- List chapters
  GET  /books/{id}/manuscript/chapters/{cid}  -- Get chapter
  POST /books/{id}/manuscript/chapters        -- Create chapter
  PUT  /books/{id}/manuscript/chapters/{cid}  -- Update chapter
  PATCH /books/{id}/manuscript/chapters/reorder -- Reorder chapters
  POST /books/{id}/manuscript/analyze         -- Analyze manuscript
  GET  /books/{id}/manuscript/readability-score -- Readability metrics
  POST /books/{id}/outline/generate           -- Generate outline
  POST /writing-sessions                      -- Record writing session
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.modules.ai_writing import schemas, service
from app.modules.ai_writing.generator import generate_stream, generate_sync

router = APIRouter()


# ---------------------------------------------------------------------------
# Unified Generation Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=schemas.GenerateResponse | None,
    summary="AI content generation",
    description="Unified AI content generation endpoint. Supports SSE streaming and synchronous modes.",
)
async def generate(
    request: schemas.GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Unified AI content generation endpoint.

    When `stream=true` (default), returns SSE events:
      - event:token   -- incremental text chunks
      - event:quality -- quality check results
      - event:complete -- final metadata

    When `stream=false`, returns a complete GenerateResponse JSON.
    """
    if request.stream:
        return StreamingResponse(
            generate_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    return await generate_sync(request)


# ---------------------------------------------------------------------------
# Manuscript
# ---------------------------------------------------------------------------

@router.get(
    "/books/{book_id}/manuscript",
    response_model=schemas.ManuscriptResponse,
    summary="Get full manuscript",
    description="Get the full manuscript for a book, including all chapters.",
)
async def get_manuscript(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the full manuscript for a book, including all chapters."""
    return await service.get_manuscript(db, book_id)


# ---------------------------------------------------------------------------
# Chapter CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/books/{book_id}/manuscript/chapters",
    response_model=list[schemas.ChapterContent],
    summary="List chapters",
    description="List all chapters for a book in order.",
)
async def list_chapters(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all chapters for a book."""
    return await service.list_chapters(db, book_id)


@router.get(
    "/books/{book_id}/manuscript/chapters/{chapter_id}",
    response_model=schemas.ChapterContent,
    summary="Get chapter",
    description="Get a single chapter by ID.",
)
async def get_chapter(
    book_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single chapter."""
    chapter = await service.get_chapter(db, book_id, chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter


@router.post(
    "/books/{book_id}/manuscript/chapters",
    response_model=schemas.ChapterContent,
    status_code=status.HTTP_201_CREATED,
    summary="Create chapter",
    description="Create a new chapter for a book.",
)
async def create_chapter(
    book_id: UUID,
    data: schemas.ChapterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new chapter for a book."""
    return await service.create_chapter(db, book_id, data)


@router.put(
    "/books/{book_id}/manuscript/chapters/{chapter_id}",
    response_model=schemas.ChapterContent,
    summary="Update chapter",
    description="Update an existing chapter's title or content.",
)
async def update_chapter(
    book_id: UUID,
    chapter_id: UUID,
    data: schemas.ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing chapter."""
    chapter = await service.update_chapter(db, book_id, chapter_id, data)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter


@router.patch(
    "/books/{book_id}/manuscript/chapters/reorder",
    response_model=list[schemas.ChapterContent],
    summary="Reorder chapters",
    description="Reorder chapters within a manuscript by providing new sort positions.",
)
async def reorder_chapters(
    book_id: UUID,
    data: schemas.ChapterReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reorder chapters within a manuscript."""
    return await service.reorder_chapters(db, book_id, data)


# ---------------------------------------------------------------------------
# Analysis / Readability
# ---------------------------------------------------------------------------

@router.post(
    "/books/{book_id}/manuscript/analyze",
    response_model=schemas.ManuscriptAnalysis,
    summary="Analyze manuscript",
    description="Analyze manuscript for readability, pacing, and word count metrics.",
)
async def analyze_manuscript(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analyze manuscript: readability, pacing, word count."""
    return await service.analyze_manuscript(db, book_id)


@router.get(
    "/books/{book_id}/manuscript/readability-score",
    response_model=schemas.ReadabilityScore,
    summary="Get readability score",
    description="Get readability metrics (Flesch-Kincaid, grade level) for a manuscript.",
)
async def get_readability_score(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get readability metrics for a manuscript."""
    return await service.get_readability_score(db, book_id)


# ---------------------------------------------------------------------------
# Outline
# ---------------------------------------------------------------------------

@router.post(
    "/books/{book_id}/outline/generate",
    response_model=schemas.OutlineResponse,
    summary="Generate book outline",
    description="AI-generate a book outline based on genre, topic, and audience parameters.",
)
async def generate_outline(
    book_id: UUID,
    data: schemas.OutlineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """AI-generate a book outline."""
    return await service.generate_outline(db, book_id, data)


# ---------------------------------------------------------------------------
# Writing Sessions
# ---------------------------------------------------------------------------

@router.post(
    "/writing-sessions",
    response_model=schemas.WritingSessionRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Record writing session",
    description="Record a writing session with word count and duration for productivity tracking.",
)
async def record_writing_session(
    data: schemas.WritingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a writing session."""
    user_id = current_user["user_id"]
    return await service.record_writing_session(db, user_id, data)
