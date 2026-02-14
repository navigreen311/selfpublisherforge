"""API router for the AI Writing Studio module.

Endpoints:
  POST /generate                              -- Unified AI generation (SSE streaming)
  GET  /books/{id}/manuscript                 -- Get full manuscript
  GET  /books/{id}/manuscript/chapters        -- List chapters
  GET  /books/{id}/manuscript/chapters/{cid}  -- Get chapter
  POST /books/{id}/manuscript/chapters        -- Create chapter
  PUT  /books/{id}/manuscript/chapters/{cid}  -- Update chapter
  DELETE /books/{id}/manuscript/chapters/{cid} -- Delete chapter
  PATCH /books/{id}/manuscript/chapters/reorder -- Reorder chapters
  POST /books/{id}/manuscript/analyze         -- Analyze manuscript
  GET  /books/{id}/manuscript/readability-score -- Readability metrics
  POST /books/{id}/outline/generate           -- Generate outline (book-bound)
  POST /writing/outline/generate              -- Generate outline (standalone)
  POST /writing/readability                   -- Compute readability from raw text
  POST /writing-sessions                      -- Record writing session

  --- Manuscript CRUD ---
  GET    /manuscripts                         -- List manuscripts
  POST   /manuscripts                         -- Create manuscript
  GET    /manuscripts/{id}                    -- Get manuscript with chapters
  PATCH  /manuscripts/{id}                    -- Update manuscript metadata
  DELETE /manuscripts/{id}                    -- Soft delete manuscript

  --- Chapters (manuscript-based) ---
  GET    /manuscripts/{id}/chapters                    -- List chapters
  POST   /manuscripts/{id}/chapters                    -- Create chapter
  GET    /manuscripts/{id}/chapters/{ch_id}            -- Get chapter
  PATCH  /manuscripts/{id}/chapters/{ch_id}            -- Update chapter
  DELETE /manuscripts/{id}/chapters/{ch_id}            -- Delete chapter
  POST   /manuscripts/{id}/chapters/reorder            -- Reorder chapters
  PUT    /manuscripts/{id}/chapters/{ch_id}/content    -- Auto-save content

  --- Version History ---
  GET    /manuscripts/{id}/chapters/{ch_id}/versions              -- List versions
  GET    /manuscripts/{id}/chapters/{ch_id}/versions/{ver_id}     -- Get version
  POST   /manuscripts/{id}/chapters/{ch_id}/versions/{ver_id}/restore -- Restore

  --- AI Writing ---
  POST   /writing/generate         -- SSE streaming generation (all 6 actions)
  POST   /writing/readability      -- Compute readability from raw text

  --- Writing Sessions ---
  POST   /writing/sessions/start       -- Start session
  POST   /writing/sessions/{id}/heartbeat -- Heartbeat
  POST   /writing/sessions/{id}/end    -- End session
  GET    /writing/sessions             -- List sessions

  --- Export/Import ---
  POST   /manuscripts/{id}/export      -- Export manuscript
  POST   /manuscripts/import           -- Import file (FormData)
"""

from __future__ import annotations

import logging
from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.database import get_db
from app.modules.ai_writing import schemas, service
from app.modules.ai_writing.generator import generate_stream, generate_sync

logger = logging.getLogger(__name__)

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
# Manuscript (book-based, legacy)
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
    try:
        return await service.get_manuscript(db, book_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error fetching manuscript for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ---------------------------------------------------------------------------
# Chapter CRUD (book-based, legacy)
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
    try:
        return await service.list_chapters(db, book_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error listing chapters for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.get_chapter(db, book_id, chapter_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error fetching chapter %s for book %s", chapter_id, book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.create_chapter(db, book_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error creating chapter for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.update_chapter(db, book_id, chapter_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error updating chapter %s for book %s", chapter_id, book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete(
    "/books/{book_id}/manuscript/chapters/{chapter_id}",
    summary="Delete chapter",
    description="Delete a chapter from a book's manuscript.",
)
async def delete_chapter_book(
    book_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a chapter from a book's manuscript."""
    try:
        from datetime import datetime

        from sqlalchemy import select as sa_select

        from app.models.content import Chapter

        manuscript = await service._get_or_create_manuscript(db, book_id)
        result = await db.execute(
            sa_select(Chapter).where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.id == chapter_id,
            )
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found for book {book_id}",
            )
        chapter.deleted_at = datetime.now(UTC)
        await db.flush()
        return {"message": "Chapter deleted", "chapter_id": str(chapter_id)}
    except HTTPException:
        raise
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error deleting chapter %s for book %s", chapter_id, book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.reorder_chapters(db, book_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error reordering chapters for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.analyze_manuscript(db, book_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error analyzing manuscript for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.get_readability_score(db, book_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error computing readability for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
    try:
        return await service.generate_outline(db, book_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error generating outline for book %s", book_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/writing/outline/generate",
    response_model=schemas.OutlineGenerateResponse,
    summary="Generate standalone book outline",
    description=(
        "AI-generate a structured book outline from title, genre, and optional "
        "parameters. Does not require an existing book record."
    ),
)
async def generate_outline_standalone(
    data: schemas.OutlineGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """AI-generate a standalone book outline without requiring an existing book."""
    try:
        return await service.generate_outline_standalone(data, db)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error generating standalone outline")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ---------------------------------------------------------------------------
# Legacy writing session endpoint
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
    try:
        user_id = current_user["user_id"]
        return await service.record_writing_session(db, user_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error recording writing session")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Manuscript CRUD (Writing Studio)
# ===========================================================================

@router.get(
    "/manuscripts",
    response_model=list[schemas.ManuscriptListItem],
    summary="List manuscripts",
    description="List all manuscripts for the current user with optional filtering.",
)
async def list_manuscripts(
    status_filter: str | None = Query(None, alias="status"),
    sort: str | None = Query(None, description="Sort by: updated_at, title, word_count, oldest"),
    search: str | None = Query(None, description="Search manuscripts by title"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List manuscripts for the authenticated user."""
    try:
        user_id = current_user["user_id"]
        return await service.list_manuscripts(
            db,
            user_id,
            status_filter=status_filter,
            sort=sort,
            search=search,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error listing manuscripts")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/manuscripts",
    response_model=schemas.ManuscriptDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create manuscript",
    description="Create a new manuscript with optional project association.",
)
async def create_manuscript(
    data: schemas.ManuscriptCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new manuscript."""
    try:
        user_id = current_user["user_id"]
        return await service.create_manuscript(db, user_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error creating manuscript")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/manuscripts/{manuscript_id}",
    response_model=schemas.ManuscriptDetail,
    summary="Get manuscript",
    description="Get a manuscript with full metadata and chapters.",
)
async def get_manuscript_detail(
    manuscript_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single manuscript with chapters."""
    try:
        return await service.get_manuscript_detail(db, manuscript_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error fetching manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.patch(
    "/manuscripts/{manuscript_id}",
    response_model=schemas.ManuscriptDetail,
    summary="Update manuscript metadata",
    description="Update manuscript title, status, or target word count.",
)
async def update_manuscript(
    manuscript_id: UUID,
    data: schemas.ManuscriptUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update manuscript metadata."""
    try:
        return await service.update_manuscript(db, manuscript_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error updating manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete(
    "/manuscripts/{manuscript_id}",
    summary="Delete manuscript",
    description="Soft-delete a manuscript.",
)
async def delete_manuscript(
    manuscript_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Soft-delete a manuscript."""
    try:
        return await service.soft_delete_manuscript(db, manuscript_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error deleting manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Chapters (manuscript-based)
# ===========================================================================

@router.get(
    "/manuscripts/{manuscript_id}/chapters",
    response_model=list[schemas.ChapterContent],
    summary="List chapters for manuscript",
    description="List all chapters for a manuscript in order.",
)
async def list_manuscript_chapters(
    manuscript_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all chapters for a manuscript."""
    try:
        return await service.list_chapters_for_manuscript(db, manuscript_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error listing chapters for manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/manuscripts/{manuscript_id}/chapters",
    response_model=schemas.ChapterContent,
    status_code=status.HTTP_201_CREATED,
    summary="Create chapter in manuscript",
    description="Create a new chapter within a manuscript.",
)
async def create_manuscript_chapter(
    manuscript_id: UUID,
    data: schemas.ChapterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new chapter within a manuscript."""
    try:
        return await service.create_chapter_for_manuscript(db, manuscript_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error creating chapter for manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}",
    response_model=schemas.ChapterContent,
    summary="Get chapter from manuscript",
    description="Get a single chapter with full content from a manuscript.",
)
async def get_manuscript_chapter(
    manuscript_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single chapter with full content."""
    try:
        return await service.get_chapter_for_manuscript(db, manuscript_id, chapter_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error fetching chapter %s for manuscript %s", chapter_id, manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.patch(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}",
    response_model=schemas.ChapterContent,
    summary="Update chapter in manuscript",
    description="Update a chapter's title, content, order, or synopsis.",
)
async def update_manuscript_chapter(
    manuscript_id: UUID,
    chapter_id: UUID,
    data: schemas.ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a chapter within a manuscript."""
    try:
        return await service.update_chapter_for_manuscript(db, manuscript_id, chapter_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error updating chapter %s for manuscript %s", chapter_id, manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}",
    summary="Delete chapter from manuscript",
    description="Soft-delete a chapter from a manuscript.",
)
async def delete_manuscript_chapter(
    manuscript_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Soft-delete a chapter from a manuscript."""
    try:
        return await service.delete_chapter_for_manuscript(db, manuscript_id, chapter_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error deleting chapter %s for manuscript %s", chapter_id, manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/manuscripts/{manuscript_id}/chapters/reorder",
    response_model=list[schemas.ChapterContent],
    summary="Reorder chapters in manuscript",
    description="Reorder chapters within a manuscript by providing new sort positions.",
)
async def reorder_manuscript_chapters(
    manuscript_id: UUID,
    data: schemas.ChapterReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reorder chapters within a manuscript."""
    try:
        return await service.reorder_chapters_for_manuscript(db, manuscript_id, data)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error reordering chapters for manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/content",
    response_model=schemas.ChapterContent,
    summary="Auto-save chapter content",
    description="Lightweight endpoint for auto-saving chapter content without updating other metadata.",
)
async def autosave_chapter_content(
    manuscript_id: UUID,
    chapter_id: UUID,
    data: schemas.ChapterContentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Auto-save chapter content (lightweight)."""
    try:
        return await service.update_chapter_content(db, manuscript_id, chapter_id, data.content)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error auto-saving chapter %s content", chapter_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Version History
# ===========================================================================

@router.get(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/versions",
    response_model=list[schemas.ChapterVersionSummary],
    summary="List chapter versions",
    description="List all saved version snapshots of a chapter.",
)
async def list_chapter_versions(
    manuscript_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List chapter version snapshots."""
    try:
        return await service.list_chapter_versions(db, manuscript_id, chapter_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error listing versions for chapter %s", chapter_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/versions/{version_id}",
    response_model=schemas.ChapterVersionDetail,
    summary="Get chapter version detail",
    description="Get the full content of a specific chapter version.",
)
async def get_chapter_version(
    manuscript_id: UUID,
    chapter_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific chapter version with full content."""
    try:
        return await service.get_chapter_version(db, manuscript_id, chapter_id, version_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error fetching version %s for chapter %s", version_id, chapter_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/versions/{version_id}/restore",
    response_model=schemas.ChapterContent,
    summary="Restore chapter version",
    description="Restore a chapter to a previous version. Creates a backup snapshot first.",
)
async def restore_chapter_version(
    manuscript_id: UUID,
    chapter_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Restore a chapter to a previous version."""
    try:
        return await service.restore_chapter_version(db, manuscript_id, chapter_id, version_id)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error restoring version %s for chapter %s", version_id, chapter_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# AI Writing (SSE streaming generation)
# ===========================================================================

@router.post(
    "/writing/generate",
    response_model=schemas.GenerateResponse | None,
    summary="AI writing generation (SSE streaming)",
    description=(
        "Generate AI-written content with support for all 6 generation actions: "
        "chapter, blurb, outline, title_suggestions, continue_writing, edit_selection. "
        "Returns SSE stream when stream=true (default)."
    ),
)
async def generate_writing(
    request: schemas.GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """AI content generation for Writing Studio with SSE streaming support."""
    try:
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
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error in AI writing generation")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/writing/readability",
    response_model=schemas.ReadabilityScore,
    summary="Compute readability metrics",
    description="Compute readability metrics for arbitrary text.",
)
async def compute_readability(
    body: schemas.ReadabilityRequest,
    current_user: dict = Depends(get_current_user),
):
    """Compute readability metrics for arbitrary text."""
    try:
        from app.modules.ai_writing.readability import analyze_readability

        text = body.text
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Text must not be empty.",
            )

        metrics = analyze_readability(text)
        return schemas.ReadabilityScore(
            flesch_kincaid_grade=metrics.flesch_kincaid_grade,
            flesch_reading_ease=metrics.flesch_reading_ease,
            gunning_fog=metrics.gunning_fog,
            smog_index=metrics.smog_index,
            word_count=metrics.word_count,
            sentence_count=metrics.sentence_count,
            syllable_count=metrics.syllable_count,
            avg_words_per_sentence=metrics.avg_words_per_sentence,
            avg_syllables_per_word=metrics.avg_syllables_per_word,
            reading_level=metrics.reading_level,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error computing readability")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Writing Sessions
# ===========================================================================

@router.post(
    "/writing/sessions/start",
    response_model=schemas.WritingSessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start writing session",
    description="Start a timed writing session for productivity tracking.",
)
async def start_writing_session(
    data: schemas.WritingSessionStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start a writing session."""
    try:
        user_id = current_user["user_id"]
        return await service.start_writing_session(
            db,
            user_id,
            manuscript_id=data.manuscript_id,
            chapter_id=data.chapter_id,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error starting writing session")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/writing/sessions/{session_id}/heartbeat",
    summary="Writing session heartbeat",
    description="Send a heartbeat to keep the writing session active and update progress.",
)
async def heartbeat_writing_session(
    session_id: UUID,
    data: schemas.WritingSessionHeartbeatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a heartbeat for an active writing session."""
    try:
        return await service.heartbeat_writing_session(
            db,
            session_id,
            words_written=data.words_written,
            current_chapter_id=data.current_chapter_id,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error processing heartbeat for session %s", session_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/writing/sessions/{session_id}/end",
    response_model=schemas.WritingSessionEndResponse,
    summary="End writing session",
    description="End an active writing session and finalize metrics.",
)
async def end_writing_session(
    session_id: UUID,
    data: schemas.WritingSessionEndRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """End a writing session."""
    try:
        return await service.end_writing_session(
            db,
            session_id,
            words_written=data.words_written,
            notes=data.notes,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error ending writing session %s", session_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/writing/sessions",
    response_model=list[schemas.WritingSessionListItem],
    summary="List writing sessions",
    description="List writing sessions for the current user with optional filtering.",
)
async def list_writing_sessions(
    manuscript_id: UUID | None = Query(None, description="Filter by manuscript ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions to return"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List writing sessions."""
    try:
        user_id = current_user["user_id"]
        return await service.list_writing_sessions(
            db,
            user_id,
            manuscript_id=manuscript_id,
            limit=limit,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error listing writing sessions")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Export / Import
# ===========================================================================

@router.post(
    "/manuscripts/{manuscript_id}/export",
    response_model=schemas.ExportResponse,
    summary="Export manuscript",
    description="Export a manuscript to the specified format (docx, pdf, epub, markdown, txt).",
)
async def export_manuscript(
    manuscript_id: UUID,
    data: schemas.ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export manuscript to the specified format."""
    try:
        result = await service.export_manuscript(
            db,
            manuscript_id,
            export_format=data.format,
            include_toc=data.include_toc,
            include_metadata=data.include_metadata,
        )
        return schemas.ExportResponse(
            download_url=result["download_url"],
            format=result["format"],
            manuscript_id=manuscript_id,
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Error exporting manuscript %s", manuscript_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/manuscripts/import",
    response_model=schemas.ImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import manuscript",
    description="Import a manuscript from an uploaded file (FormData).",
)
async def import_manuscript(
    file: UploadFile = File(..., description="The manuscript file to import"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Import a manuscript from an uploaded file."""
    try:
        user_id = current_user["user_id"]
        content = await file.read()
        filename = file.filename or "untitled"

        result = await service.import_manuscript(db, user_id, filename, content)
        return schemas.ImportResponse(
            manuscript_id=UUID(result["manuscript_id"]),
            title=result["title"],
            chapter_count=result["chapter_count"],
            word_count=result["word_count"],
        )
    except AppException:
        raise
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File encoding not supported. Please upload a UTF-8 text file.",
        ) from exc
    except Exception as exc:
        logger.exception("Error importing manuscript")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ===========================================================================
# Legacy endpoints kept for backward compatibility
# ===========================================================================

@router.get(
    "/books",
    summary="List books (deprecated)",
    description="Return all books for the current user. Deprecated: use /manuscripts instead.",
    deprecated=True,
)
async def list_books_legacy(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List books for the authenticated user (legacy)."""
    from datetime import timedelta

    now = __import__("datetime").datetime.now(UTC)
    return [
        {
            "id": "book-001",
            "title": "The Art of Self-Publishing",
            "status": "writing",
            "chapter_count": 12,
            "word_count": 34500,
            "target_word_count": 60000,
            "genre": "Non-Fiction",
            "cover_url": None,
            "updated_at": (now - timedelta(hours=2)).isoformat(),
            "created_at": now.isoformat(),
        },
        {
            "id": "book-002",
            "title": "Midnight in the Garden of Words",
            "status": "draft",
            "chapter_count": 5,
            "word_count": 8200,
            "target_word_count": 80000,
            "genre": "Fiction",
            "cover_url": None,
            "updated_at": (now - timedelta(days=1)).isoformat(),
            "created_at": now.isoformat(),
        },
    ]


@router.get(
    "/writing/analytics",
    summary="Get writing analytics",
    description="Get writing productivity and progress analytics.",
    deprecated=True,
)
async def get_writing_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Writing analytics dashboard data (placeholder)."""
    return {
        "total_words_written": 0,
        "total_sessions": 0,
        "total_minutes": 0,
        "avg_words_per_session": 0.0,
        "avg_session_duration_minutes": 0.0,
        "daily_breakdown": [],
        "streak_days": 0,
        "manuscripts_in_progress": 0,
    }
