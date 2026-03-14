"""FastAPI router for the Puzzle Book Generator.

Endpoints:
    GET/POST   /api/v1/specialty/puzzle-books                              -- List / Create books
    GET/PATCH/DELETE /api/v1/specialty/puzzle-books/{id}                    -- Read / Update / Delete book
    GET        /api/v1/specialty/puzzle-books/{id}/puzzles                  -- List puzzles
    POST       /api/v1/specialty/puzzle-books/{id}/puzzles/generate         -- Generate puzzle
    POST       /api/v1/specialty/puzzle-books/{id}/puzzles/{puzzle_id}/regenerate -- Regenerate
    PATCH/DELETE /api/v1/specialty/puzzle-books/{id}/puzzles/{puzzle_id}    -- Update / Delete puzzle
    POST       /api/v1/specialty/puzzle-books/{id}/puzzles/{puzzle_id}/verify -- Verify solvable
    POST       /api/v1/specialty/puzzle-books/generate-word-list            -- AI generate word list
    POST       /api/v1/specialty/puzzle-books/sanitize-word-list            -- Run sanitization pipeline
    POST       .../{id}/puzzles/{puzzle_id}/generate-clues                  -- Generate clues
    POST       .../{id}/puzzles/{puzzle_id}/qa-clues                       -- QA clues
    POST       .../{id}/auto-fix-clues                                     -- AI fix ambiguous clues
    POST       .../{id}/generate-answer-key                                -- Generate answer key
    POST       .../{id}/verify-answer-key                                  -- Verify answer key
    POST       .../{id}/quality-check                                      -- Book-level QA
    POST       .../{id}/calibrate-difficulty                               -- Difficulty calibration
    POST       .../{id}/generate-large-print                               -- Large print variant
    POST       .../{id}/export                                             -- Export book
    POST       .../{id}/preflight                                          -- Run preflight
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.puzzles import service

router = APIRouter(prefix="/specialty/puzzle-books", tags=["puzzle-books"])


# ---------------------------------------------------------------------------
# Stats (must be defined before /{book_id} routes)
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Get puzzle book stats",
    description="Return aggregate statistics for puzzle books in the current organization.",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.get_stats(db, current_user["org_id"])
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[list[dict[str, Any]]],
    summary="List puzzle books",
    description="List all puzzle books for the current organisation.",
)
async def list_puzzle_books(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    books = await service.list_puzzle_books(db, current_user["org_id"])
    return SuccessResponse(data=books)


@router.post(
    "",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Create puzzle book",
    description="Create a new puzzle book with configuration.",
)
async def create_puzzle_book(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.create_puzzle_book(db, current_user["org_id"], payload)
    return SuccessResponse(data=book)


@router.get(
    "/{book_id}",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Get puzzle book by ID",
)
async def get_puzzle_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.get_puzzle_book(db, current_user["org_id"], book_id)
    return SuccessResponse(data=book)


@router.patch(
    "/{book_id}",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Update puzzle book",
)
async def update_puzzle_book(
    book_id: UUID,
    updates: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.update_puzzle_book(
        db, current_user["org_id"], book_id, updates
    )
    return SuccessResponse(data=book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete puzzle book (soft-delete)",
)
async def delete_puzzle_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await service.delete_puzzle_book(db, current_user["org_id"], book_id)
    return


# ---------------------------------------------------------------------------
# Individual Puzzle CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/{book_id}/puzzles",
    response_model=SuccessResponse[list[dict[str, Any]]],
    summary="List puzzles in a book",
)
async def list_puzzles(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    puzzles = await service.list_puzzles(db, current_user["org_id"], book_id)
    return SuccessResponse(data=puzzles)


@router.post(
    "/{book_id}/puzzles/generate",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new puzzle",
    description="Algorithmically generate a puzzle and add it to the book.",
)
async def generate_puzzle(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    puzzle = await service.generate_puzzle(
        db,
        current_user["org_id"],
        book_id,
        puzzle_type=payload.get("puzzle_type"),
        theme=payload.get("theme"),
        difficulty=payload.get("difficulty"),
        grid_size=payload.get("grid_size"),
        word_list=payload.get("word_list"),
    )
    return SuccessResponse(data=puzzle)


@router.post(
    "/{book_id}/puzzles/{puzzle_id}/regenerate",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Regenerate puzzle with same parameters",
)
async def regenerate_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    puzzle = await service.regenerate_puzzle(
        db, current_user["org_id"], book_id, puzzle_id
    )
    return SuccessResponse(data=puzzle)


@router.patch(
    "/{book_id}/puzzles/{puzzle_id}",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Update a puzzle",
)
async def update_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    updates: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    puzzle = await service.update_puzzle(
        db, current_user["org_id"], book_id, puzzle_id, updates
    )
    return SuccessResponse(data=puzzle)


@router.delete(
    "/{book_id}/puzzles/{puzzle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a puzzle",
)
async def delete_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await service.delete_puzzle(db, current_user["org_id"], book_id, puzzle_id)
    return


@router.post(
    "/{book_id}/puzzles/{puzzle_id}/verify",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Verify puzzle is solvable with unique solution",
)
async def verify_puzzle(
    book_id: UUID,
    puzzle_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.verify_puzzle(
        db, current_user["org_id"], book_id, puzzle_id
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Word List Utilities (book-independent)
# ---------------------------------------------------------------------------


@router.post(
    "/generate-word-list",
    response_model=SuccessResponse[dict[str, Any]],
    summary="AI generate themed word list",
)
async def generate_word_list(
    payload: dict[str, Any],
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_word_list(
        theme=payload.get("theme", "general"),
        count=payload.get("count", 20),
        difficulty=payload.get("difficulty", "standard"),
    )
    return SuccessResponse(data=result)


@router.post(
    "/sanitize-word-list",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Run word list sanitization pipeline",
)
async def sanitize_word_list(
    payload: dict[str, Any],
    current_user: dict = Depends(get_current_user),
):
    result = await service.sanitize_word_list(
        words=payload.get("words", []),
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Clue Management
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/puzzles/{puzzle_id}/generate-clues",
    response_model=SuccessResponse[dict[str, Any]],
    summary="AI generate clues in specified style",
)
async def generate_clues(
    book_id: UUID,
    puzzle_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_clues(
        db,
        current_user["org_id"],
        book_id,
        puzzle_id,
        style=payload.get("style", "standard"),
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/puzzles/{puzzle_id}/qa-clues",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Check clue quality for a puzzle",
)
async def qa_clues(
    book_id: UUID,
    puzzle_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.qa_clues(
        db, current_user["org_id"], book_id, puzzle_id
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/auto-fix-clues",
    response_model=SuccessResponse[dict[str, Any]],
    summary="AI fix ambiguous clues across the book",
)
async def auto_fix_clues(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.auto_fix_clues(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Answer Key
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/generate-answer-key",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Generate answer key section",
)
async def generate_answer_key(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_answer_key(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/verify-answer-key",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Verify answer keys match puzzles",
)
async def verify_answer_key(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.verify_answer_key(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Book-Level Quality & Calibration
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/quality-check",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Run book-level QA dashboard checks",
)
async def quality_check(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_quality_check(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/calibrate-difficulty",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Calculate difficulty scores and enforce pacing",
)
async def calibrate_difficulty(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.calibrate_difficulty(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Large Print Variant
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/generate-large-print",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Create large print variant of the book",
)
async def generate_large_print(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_large_print(
        db,
        current_user["org_id"],
        book_id,
        scale=payload.get("scale", 150),
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/export",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Export puzzle book as print-ready PDF",
)
async def export_book(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.export_book(
        db,
        current_user["org_id"],
        book_id,
        format=payload.get("format", "pdf"),
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/preflight",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Run full preflight checks",
)
async def preflight(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_preflight(
        db, current_user["org_id"], book_id
    )
    return SuccessResponse(data=result)
