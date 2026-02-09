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

@router.post("/generate", response_model=schemas.GenerateResponse | None)
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

@router.get("/books/{book_id}/manuscript", response_model=schemas.ManuscriptResponse)
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
)
async def record_writing_session(
    data: schemas.WritingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a writing session."""
    user_id = current_user["user_id"]
    return await service.record_writing_session(db, user_id, data)
