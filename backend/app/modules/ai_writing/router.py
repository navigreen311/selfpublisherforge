"""API router for the AI Writing Studio module.

Endpoints:
  POST /generate                              -- Unified AI generation (SSE streaming)
  GET  /books/{id}/manuscript                 -- Get full manuscript
  GET  /books/{id}/manuscript/chapters        -- List chapters
  GET  /books/{id}/manuscript/chapters/{cid}  -- Get chapter
  POST /books/{id}/manuscript/chapters        -- Create chapter
  PUT  /books/{id}/manuscript/chapters/{cid}  -- Update chapter
  DELETE /books/{id}/manuscript/chapters/{cid} -- Delete chapter (stub)
  PATCH /books/{id}/manuscript/chapters/reorder -- Reorder chapters
  POST /books/{id}/manuscript/analyze         -- Analyze manuscript
  GET  /books/{id}/manuscript/readability-score -- Readability metrics
  POST /books/{id}/outline/generate           -- Generate outline (book-bound)
  POST /writing/outline/generate              -- Generate outline (standalone)
  POST /writing/readability                   -- Compute readability from raw text
  POST /writing-sessions                      -- Record writing session

  --- Writing Studio stubs ---
  GET    /manuscripts                         -- List manuscripts (stub)
  POST   /manuscripts                         -- Create manuscript (stub)
  GET    /manuscripts/{id}                    -- Get manuscript with chapters (stub)
  PATCH  /manuscripts/{id}                    -- Update manuscript metadata (stub)
  DELETE /manuscripts/{id}                    -- Delete manuscript (stub)
  POST   /manuscripts/{id}/export             -- Export manuscript (stub)
  POST   /writing/generate-outline            -- Generate enhanced outline (stub)
  POST   /writing/create-from-outline         -- Create manuscript from outline (stub)
  POST   /writing/generate                    -- AI writing generation (stub)
  GET    /writing/readability/{chapter_id}    -- Readability scores (stub)
  POST   /writing/sessions/start              -- Start writing session (stub)
  PATCH  /writing/sessions/{id}/end           -- End writing session (stub)
  GET    /writing/analytics                   -- Writing analytics (stub)
  GET    /manuscripts/{id}/chapters/{ch_id}/versions          -- Chapter versions (stub)
  POST   /manuscripts/{id}/chapters/{ch_id}/versions/{ver_id}/restore -- Restore version (stub)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
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
    return await service.generate_outline_standalone(data, db)


# ---------------------------------------------------------------------------
# Writing Sessions
# ---------------------------------------------------------------------------


@router.get(
    "/writing-sessions",
    summary="List writing sessions (stub)",
    description="Return recent writing sessions. Stub: returns sample data.",
)
async def list_writing_sessions_stub(
    book_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List writing sessions (stub with sample data)."""
    now = datetime.now(UTC)
    return [
        {
            "id": "session-001",
            "book_id": "book-001",
            "book_title": "The Art of Self-Publishing",
            "chapter_title": "Chapter 3: Marketing",
            "words_written": 1250,
            "duration_minutes": 45,
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "session-002",
            "book_id": "book-002",
            "book_title": "Midnight in the Garden of Words",
            "chapter_title": "Chapter 1: Prologue",
            "words_written": 800,
            "duration_minutes": 30,
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
    ]


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


# ===========================================================================
# Writing Studio – Stub Endpoints
# ===========================================================================
# These endpoints return placeholder data so the frontend can be developed
# against a stable API contract before the real implementation is wired up.
# ---------------------------------------------------------------------------

_STUB_MANUSCRIPT_ID = "00000000-0000-0000-0000-000000000001"
_STUB_CHAPTER_ID = "00000000-0000-0000-0000-000000000010"
_STUB_VERSION_ID = "00000000-0000-0000-0000-000000000100"
_STUB_SESSION_ID = "00000000-0000-0000-0000-000000001000"


def _stub_chapter(*, chapter_id: str = _STUB_CHAPTER_ID, order: int = 1) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "id": chapter_id,
        "manuscript_id": _STUB_MANUSCRIPT_ID,
        "title": f"Chapter {order} (stub)",
        "content": "",
        "order": order,
        "synopsis": "",
        "word_count": 0,
        "created_at": now,
        "updated_at": now,
    }


def _stub_manuscript(*, include_chapters: bool = False) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "id": _STUB_MANUSCRIPT_ID,
        "title": "Untitled Manuscript (stub)",
        "status": "draft",
        "chapters": [_stub_chapter()] if include_chapters else [],
        "total_word_count": 0,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Manuscripts CRUD (stub)
# ---------------------------------------------------------------------------


@router.get(
    "/books",
    summary="List books (stub)",
    description="Return all books for the current user. Stub: returns sample data.",
)
async def list_books_stub(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List books for the authenticated user (stub)."""
    now = datetime.now(UTC)
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
        {
            "id": "book-003",
            "title": "Marketing for Authors",
            "status": "editing",
            "chapter_count": 10,
            "word_count": 45000,
            "target_word_count": 50000,
            "genre": "Self-Help",
            "cover_url": None,
            "updated_at": (now - timedelta(days=5)).isoformat(),
            "created_at": now.isoformat(),
        },
    ]


@router.get(
    "/manuscripts",
    summary="List manuscripts (stub)",
    description="Return all manuscripts for the current user. Stub: returns empty list.",
)
async def list_manuscripts_stub(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List manuscripts for the authenticated user (stub)."""
    return []


@router.post(
    "/manuscripts",
    status_code=status.HTTP_201_CREATED,
    summary="Create manuscript (stub)",
    description="Create a new manuscript. Stub: returns placeholder manuscript.",
)
async def create_manuscript_stub(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new manuscript (stub)."""
    return _stub_manuscript()


@router.get(
    "/manuscripts/{manuscript_id}",
    summary="Get manuscript (stub)",
    description="Get a manuscript with its chapters. Stub: returns placeholder.",
)
async def get_manuscript_stub(
    manuscript_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single manuscript with chapters (stub)."""
    return _stub_manuscript(include_chapters=True)


@router.delete(
    "/manuscripts/{manuscript_id}",
    summary="Delete manuscript (stub)",
    description="Delete a manuscript. Stub: returns confirmation message.",
)
async def delete_manuscript_stub(
    manuscript_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a manuscript (stub)."""
    return {"message": "Deleted"}


@router.post(
    "/manuscripts/{manuscript_id}/export",
    summary="Export manuscript (stub)",
    description="Export a manuscript to the specified format. Stub: returns a download URL.",
)
async def export_manuscript_stub(
    manuscript_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Export manuscript (stub)."""
    fmt = body.get("format", "docx")
    return {"download_url": f"/exports/manuscript-{manuscript_id}.{fmt}", "format": fmt}


@router.patch(
    "/manuscripts/{manuscript_id}",
    summary="Update manuscript metadata (stub)",
    description="Update manuscript metadata such as title or status. Stub: echoes back the update.",
)
async def update_manuscript_stub(
    manuscript_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update manuscript metadata (stub)."""
    return {"id": str(manuscript_id), **body}


@router.delete(
    "/books/{book_id}/manuscript/chapters/{chapter_id}",
    summary="Delete chapter (stub)",
    description="Delete a chapter from a book's manuscript. Stub: returns confirmation.",
)
async def delete_chapter_stub(
    book_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a chapter (stub)."""
    return {"message": "Chapter deleted", "chapter_id": str(chapter_id)}


# ---------------------------------------------------------------------------
# Enhanced Outline (stub)
# ---------------------------------------------------------------------------


@router.post(
    "/writing/generate-outline",
    summary="Generate enhanced outline (stub)",
    description="AI-generate a detailed chapter outline for a book. Stub: returns empty chapters.",
)
async def generate_outline_enhanced_stub(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate an enhanced book outline (stub)."""
    return {"chapters": []}


@router.post(
    "/writing/create-from-outline",
    summary="Create manuscript from outline (stub)",
    description="Create a full manuscript scaffold from an outline. Stub: returns placeholder.",
)
async def create_from_outline_stub(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a manuscript from an outline (stub)."""
    return _stub_manuscript(include_chapters=True)


# ---------------------------------------------------------------------------
# AI Writing (stub)
# ---------------------------------------------------------------------------


@router.post(
    "/writing/generate",
    summary="AI writing generation (stub)",
    description="Generate AI-written content for a chapter or section. Stub: returns empty content.",
)
async def generate_writing_stub(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """AI content generation for Writing Studio (stub)."""
    return {"content": ""}


# ---------------------------------------------------------------------------
# Readability (stub)
# ---------------------------------------------------------------------------


@router.get(
    "/writing/readability/{chapter_id}",
    summary="Get chapter readability scores (stub)",
    description="Get readability metrics for a specific chapter. Stub: returns placeholder scores.",
)
async def get_chapter_readability_stub(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Readability scores for a chapter (stub)."""
    return {
        "chapter_id": str(chapter_id),
        "flesch_kincaid_grade": 0.0,
        "flesch_reading_ease": 0.0,
        "gunning_fog": 0.0,
        "smog_index": 0.0,
        "word_count": 0,
        "sentence_count": 0,
        "syllable_count": 0,
        "avg_words_per_sentence": 0.0,
        "avg_syllables_per_word": 0.0,
        "reading_level": "N/A",
    }


@router.post(
    "/writing/readability",
    summary="Compute readability metrics",
    description="Compute readability metrics for arbitrary text using textstat.",
)
async def compute_readability(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Compute readability metrics for arbitrary text."""
    import re

    import textstat

    text = body.get("text", "")
    if not text.strip():
        return {
            "grade_level": 0,
            "flesch_ease": 0,
            "flesch_label": "N/A",
            "passive_voice_pct": 0,
            "avg_sentence_length": 0,
            "word_count": 0,
            "suggestions": [],
        }

    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    sentence_count = max(len(sentences), 1)
    avg_sentence_length = round(word_count / sentence_count, 1)

    grade = round(textstat.flesch_kincaid_grade(text), 1)
    flesch = round(textstat.flesch_reading_ease(text), 1)

    # Flesch label
    if flesch >= 90:
        flesch_label = "Very Easy"
    elif flesch >= 80:
        flesch_label = "Easy"
    elif flesch >= 70:
        flesch_label = "Fairly Easy"
    elif flesch >= 60:
        flesch_label = "Standard"
    elif flesch >= 50:
        flesch_label = "Fairly Difficult"
    elif flesch >= 30:
        flesch_label = "Difficult"
    else:
        flesch_label = "Very Confusing"

    # Passive voice detection (simple heuristic)
    passive_patterns = re.findall(r"\b(was|were|been|being|is|are|am)\b\s+\w+ed\b", text, re.IGNORECASE)
    passive_pct = round(len(passive_patterns) / max(sentence_count, 1) * 100, 1)

    # Suggestions
    suggestions: list[str] = []
    if grade > 12:
        suggestions.append("Consider simplifying sentences for a broader audience.")
    if avg_sentence_length > 25:
        suggestions.append("Try breaking up longer sentences.")
    if passive_pct > 15:
        suggestions.append("Reduce passive voice for more engaging writing.")
    if flesch < 50:
        suggestions.append("The text may be difficult to read. Consider using simpler words.")

    return {
        "grade_level": grade,
        "flesch_ease": flesch,
        "flesch_label": flesch_label,
        "passive_voice_pct": passive_pct,
        "avg_sentence_length": avg_sentence_length,
        "word_count": word_count,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Writing Sessions (stub)
# ---------------------------------------------------------------------------


@router.post(
    "/writing/sessions/start",
    summary="Start writing session (stub)",
    description="Start a timed writing session for productivity tracking. Stub: returns session ID.",
)
async def start_writing_session_stub(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start a writing session (stub)."""
    return {"session_id": "stub"}


@router.patch(
    "/writing/sessions/{session_id}/end",
    summary="End writing session (stub)",
    description="End an active writing session. Stub: returns confirmation.",
)
async def end_writing_session_stub(
    session_id: UUID,
    body: dict | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """End a writing session (stub)."""
    return {"message": "Session ended"}


# ---------------------------------------------------------------------------
# Analytics (stub)
# ---------------------------------------------------------------------------


@router.get(
    "/writing/analytics",
    summary="Get writing analytics (stub)",
    description="Get writing productivity and progress analytics. Stub: returns placeholder data.",
)
async def get_writing_analytics_stub(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Writing analytics dashboard data (stub)."""
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


# ---------------------------------------------------------------------------
# Chapter Versions (stub)
# ---------------------------------------------------------------------------


@router.get(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/versions",
    summary="List chapter versions (stub)",
    description="List saved versions / snapshots of a chapter. Stub: returns empty list.",
)
async def list_chapter_versions_stub(
    manuscript_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List chapter versions (stub)."""
    return []


@router.post(
    "/manuscripts/{manuscript_id}/chapters/{chapter_id}/versions/{version_id}/restore",
    summary="Restore chapter version (stub)",
    description="Restore a chapter to a previous version. Stub: returns placeholder chapter.",
)
async def restore_chapter_version_stub(
    manuscript_id: UUID,
    chapter_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Restore a chapter to a previous version (stub)."""
    return _stub_chapter(chapter_id=str(chapter_id))
