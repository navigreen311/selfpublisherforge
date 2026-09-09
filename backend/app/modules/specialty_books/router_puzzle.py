"""FastAPI router for Puzzle Book CRUD endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books import service_puzzle

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas (co-located for simplicity)
# ---------------------------------------------------------------------------
class PuzzleBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    template: str | None = None
    audience: str | None = None
    puzzle_config: dict[str, Any] | None = None
    difficulty_mode: str | None = None
    themes: list[str] | None = None
    seasonal_theme: str | None = None
    word_difficulty: str | None = None
    clue_style: str | None = None
    settings: dict[str, Any] | None = None


class PuzzleBookUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    audience: str | None = None
    puzzle_config: dict[str, Any] | None = None
    difficulty_mode: str | None = None
    themes: list[str] | None = None
    seasonal_theme: str | None = None
    word_difficulty: str | None = None
    clue_style: str | None = None
    status: str | None = None
    settings: dict[str, Any] | None = None


class PuzzleBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    org_id: UUID
    title: str
    audience: str | None = None
    puzzle_config: dict[str, Any] | None = None
    difficulty_mode: str | None = None
    themes: list[str] | None = None
    seasonal_theme: str | None = None
    word_difficulty: str | None = None
    clue_style: str | None = None
    status: str | None = None
    settings: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PuzzleCreate(BaseModel):
    puzzle_type: str = Field(..., min_length=1, max_length=50)
    puzzle_number: int = Field(..., ge=1)
    theme: str | None = None
    difficulty: str | None = None
    grid_size: str | None = None
    settings: dict[str, Any] | None = None


class PuzzleUpdate(BaseModel):
    theme: str | None = None
    difficulty: str | None = None
    grid_size: str | None = None
    settings: dict[str, Any] | None = None


class PuzzleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    book_id: UUID
    puzzle_type: str
    puzzle_number: int
    theme: str | None = None
    difficulty: str | None = None
    difficulty_score: float | None = None
    grid_size: str | None = None
    grid_data: dict[str, Any] | None = None
    word_list: list[str] | None = None
    clues: dict[str, Any] | None = None
    solution_data: dict[str, Any] | None = None
    qa_scores: dict[str, Any] | None = None
    qa_passed: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WordListGenerateRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    count: int = Field(default=20, ge=5, le=100)
    difficulty: str = Field(default="medium")


class SanitizeWordListRequest(BaseModel):
    words: list[str]


class PuzzleExportRequest(BaseModel):
    format: str = Field(default="print_pdf")


# ---------------------------------------------------------------------------
# Book CRUD endpoints
# ---------------------------------------------------------------------------
@router.get("", summary="List puzzle books")
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    books, total = await service_puzzle.list_puzzle_books(db, user.org_id, skip=skip, limit=limit)
    return {"items": [PuzzleBookResponse.model_validate(b) for b in books], "total": total}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create puzzle book")
async def create_book(
    body: PuzzleBookCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.create_puzzle_book(db, user.org_id, body.model_dump())
    await db.commit()
    return PuzzleBookResponse.model_validate(book)


@router.get("/{book_id}", summary="Get puzzle book")
async def get_book(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return PuzzleBookResponse.model_validate(book)


@router.patch("/{book_id}", summary="Update puzzle book")
async def update_book(
    book_id: UUID,
    body: PuzzleBookUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    updated = await service_puzzle.update_puzzle_book(db, book, body.model_dump(exclude_unset=True))
    await db.commit()
    return PuzzleBookResponse.model_validate(updated)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete puzzle book")
async def delete_book(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    await service_puzzle.delete_puzzle_book(db, book)
    await db.commit()


# ---------------------------------------------------------------------------
# Puzzle CRUD endpoints
# ---------------------------------------------------------------------------
@router.get("/{book_id}/puzzles", summary="List puzzles in book")
async def list_puzzles(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzles = await service_puzzle.list_puzzles(db, book_id)
    return {"items": [PuzzleResponse.model_validate(p) for p in puzzles]}


@router.post("/{book_id}/puzzles", status_code=status.HTTP_201_CREATED, summary="Create puzzle")
async def create_puzzle(
    book_id: UUID,
    body: PuzzleCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzle = await service_puzzle.create_puzzle(db, user.org_id, book_id, body.model_dump())
    await db.commit()
    return PuzzleResponse.model_validate(puzzle)


@router.post("/{book_id}/puzzles/{puzzle_id}/regenerate", summary="Regenerate puzzle")
async def regenerate_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzle = await service_puzzle.get_puzzle(db, puzzle_id)
    if not puzzle or puzzle.book_id != book_id:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    updated = await service_puzzle.regenerate_puzzle(db, puzzle)
    await db.commit()
    return PuzzleResponse.model_validate(updated)


@router.patch("/{book_id}/puzzles/{puzzle_id}", summary="Update puzzle")
async def update_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    body: PuzzleUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzle = await service_puzzle.get_puzzle(db, puzzle_id)
    if not puzzle or puzzle.book_id != book_id:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    updated = await service_puzzle.update_puzzle(db, puzzle, body.model_dump(exclude_unset=True))
    await db.commit()
    return PuzzleResponse.model_validate(updated)


@router.delete("/{book_id}/puzzles/{puzzle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete puzzle")
async def delete_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzle = await service_puzzle.get_puzzle(db, puzzle_id)
    if not puzzle or puzzle.book_id != book_id:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    await service_puzzle.delete_puzzle(db, puzzle)
    await db.commit()


# ---------------------------------------------------------------------------
# Word list endpoints
# ---------------------------------------------------------------------------
@router.post("/word-lists/generate", summary="Generate themed word list")
async def generate_word_list(
    body: WordListGenerateRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    words = await service_puzzle.generate_word_list(body.theme, body.count, body.difficulty)
    return {"theme": body.theme, "words": words, "count": len(words)}


@router.post("/word-lists/sanitize", summary="Sanitize word list")
async def sanitize_word_list(
    body: SanitizeWordListRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = service_puzzle.sanitize_word_list(body.words)
    return result


# ---------------------------------------------------------------------------
# Verification / QA endpoints
# ---------------------------------------------------------------------------
@router.post("/{book_id}/puzzles/{puzzle_id}/verify", summary="Verify puzzle quality")
async def verify_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    puzzle = await service_puzzle.get_puzzle(db, puzzle_id)
    if not puzzle or puzzle.book_id != book_id:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    result = await service_puzzle.verify_puzzle(db, puzzle)
    await db.commit()
    return result


@router.get("/{book_id}/quality-check", summary="Book quality check")
async def quality_check(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return await service_puzzle.book_quality_check(db, book)


# ---------------------------------------------------------------------------
# Answer key endpoints
# ---------------------------------------------------------------------------
@router.get("/{book_id}/answer-key", summary="Generate answer key")
async def answer_key(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return await service_puzzle.generate_answer_key(db, book)


@router.post("/{book_id}/answer-key/verify", summary="Verify answer key")
async def verify_answer_key(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return await service_puzzle.verify_answer_key(db, book)


# ---------------------------------------------------------------------------
# Export & preflight
# ---------------------------------------------------------------------------
@router.post("/{book_id}/export", summary="Export puzzle book")
async def export_book(
    book_id: UUID,
    body: PuzzleExportRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return await service_puzzle.export_book(db, book, body.format)


@router.get("/{book_id}/preflight", summary="Run preflight checks")
async def preflight(
    book_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    book = await service_puzzle.get_puzzle_book(db, user.org_id, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Puzzle book not found")
    return await service_puzzle.run_preflight(db, book)


# ---------------------------------------------------------------------------
# Templates endpoint
# ---------------------------------------------------------------------------
@router.get("/templates", summary="List puzzle book templates")
async def list_templates(user=Depends(get_current_user)):
    return {"templates": service_puzzle.PUZZLE_BOOK_TEMPLATES}
