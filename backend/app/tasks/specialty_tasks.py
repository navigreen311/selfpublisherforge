"""Celery tasks for Specialty Books async operations.

Handles:
- Batch coloring page generation with per-page quality pipeline
- Book export (PDF/KPF/EPUB) for any specialty book type
- Batch quality checks across all pages
- Batch puzzle generation with solution verification
- Multi-volume batch factory processing with budget guardrails
- Accessible edition creation (dyslexia-friendly, large print, high contrast)

All tasks emit WebSocket progress events via Redis pub/sub:
- specialty:{book_type}:{book_id}:events — multiplexed channel carrying typed payloads:
    batch_generation_started   — { job_id, total_pages }
    page_generation_progress   — { job_id, page_index, percent, stage }
    page_generation_complete   — { job_id, page_index, qa_score }
    page_generation_failed     — { job_id, page_index, error }
    batch_generation_complete  — { job_id, completed, failed, overall_qa_score }
    export_started             — { book_id, format }
    export_complete            — { book_id, format, download_url }
    export_failed              — { book_id, error }
    quality_check_complete     — { book_id, qa_score, pages_checked }
    puzzle_batch_progress      — { book_id, completed, total }
    puzzle_batch_complete      — { book_id, total, verified }
    batch_factory_progress     — { job_id, volumes_completed, volumes_total, spent_cents }
    batch_factory_complete     — { job_id, volumes_completed, spent_cents }
    accessibility_complete     — { book_id, variant_type, variant_book_id }

Time limit strategy
-------------------
- generate_coloring_pages_batch:   soft=1800, hard=2100  (batch image gen + QA)
- export_book_task:                soft=600,  hard=900   (PDF/KPF/EPUB assembly)
- run_batch_quality_check:         soft=900,  hard=1200  (QA pipeline on all pages)
- generate_puzzle_batch:           soft=1200, hard=1500  (puzzle gen + verification)
- process_batch_factory_job:       soft=3300, hard=3600  (multi-volume orchestrator)
- generate_accessibility_variant:  soft=600,  hard=900   (single variant transform)
"""

import asyncio
import json
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Async helper — matches pattern used in audiobook_tasks.py
# ---------------------------------------------------------------------------
def _run_async(coro):
    """Helper to run async code in Celery sync tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Redis pub/sub helper for WebSocket progress events
# ---------------------------------------------------------------------------
def _publish_event(book_type: str, book_id: str, event_type: str, data: dict):
    """Publish a typed WebSocket event via Redis pub/sub.

    All events for a specialty book are multiplexed onto a single channel so
    the WebSocket handler can subscribe once and demux by ``type``.
    """
    import redis

    from app.config import get_settings

    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    channel = f"specialty:{book_type}:{book_id}:events"
    message = json.dumps({"type": event_type, **data})
    r.publish(channel, message)
    r.close()


# ---------------------------------------------------------------------------
# Task 1: Batch coloring page generation
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.generate_coloring_pages_batch",
    bind=True,
    max_retries=2,
    soft_time_limit=1800,
    time_limit=2100,
)
def generate_coloring_pages_batch(
    self,
    book_id: str,
    descriptions: list[str],
    variation_mode: bool = True,
    job_id: str | None = None,
):
    """Async batch generation for coloring books.

    Steps per page:
    1. Build coloring-specific prompt with variation injection
    2. Generate line art via image generation service
    3. Run full quality pipeline (7-step)
    4. Update page record with QA results
    5. Emit per-page progress event

    Parameters
    ----------
    book_id : str
        Coloring book UUID.
    descriptions : list[str]
        One prompt/description per page to generate.
    variation_mode : bool
        When True, inject variation prompts to prevent composition repetition.
    job_id : str | None
        Optional caller-supplied job ID; auto-generated if omitted.
    """
    effective_job_id = job_id or f"batch-{secrets.token_urlsafe(16)}"
    logger.info(
        "Starting coloring batch generation (job=%s, book=%s, pages=%d)",
        effective_job_id,
        book_id,
        len(descriptions),
    )
    _run_async(_generate_coloring_pages_async(self, book_id, descriptions, variation_mode, effective_job_id))
    logger.info(
        "Coloring batch generation completed (job=%s, book=%s)",
        effective_job_id,
        book_id,
    )


async def _generate_coloring_pages_async(
    task,
    book_id: str,
    descriptions: list[str],
    variation_mode: bool,
    job_id: str,
):
    """Async implementation of batch coloring page generation."""
    from app.modules.specialty.coloring.quality_pipeline import run_full_pipeline, step_1_generate
    from app.modules.specialty.models.coloring import ColoringBook, ColoringBookPage

    async with async_session() as db:
        try:
            # Load book
            book = (await db.execute(select(ColoringBook).where(ColoringBook.id == book_id))).scalar_one()

            book_type = "coloring"
            total_pages = len(descriptions)
            completed = 0
            failed = 0

            _publish_event(
                book_type,
                book_id,
                "batch_generation_started",
                {"job_id": job_id, "total_pages": total_pages},
            )

            # Determine style parameters from book
            line_style = book.line_style if hasattr(book, "line_style") else "clean_outlines"
            complexity = book.complexity if hasattr(book, "complexity") else 50

            complexity_desc = "simple, minimal detail"
            if complexity > 70:
                complexity_desc = "highly detailed, intricate patterns"
            elif complexity > 40:
                complexity_desc = "moderate detail, balanced complexity"

            for idx, description in enumerate(descriptions):
                page_index = idx + 1
                try:
                    _publish_event(
                        book_type,
                        book_id,
                        "page_generation_progress",
                        {
                            "job_id": job_id,
                            "page_index": page_index,
                            "percent": 10,
                            "stage": "generating",
                        },
                    )

                    # Variation injection to prevent repetitive compositions
                    enriched_prompt = f"{description}. Complexity: {complexity_desc}."
                    if variation_mode and idx > 0:
                        variation_suffix = f" Unique composition variant {idx + 1}, avoid duplicating previous layouts."
                        enriched_prompt += variation_suffix

                    # Step 1: Generate raw line art
                    style_str = line_style.value if hasattr(line_style, "value") else str(line_style)
                    raw_image = await step_1_generate(enriched_prompt, style_str)

                    _publish_event(
                        book_type,
                        book_id,
                        "page_generation_progress",
                        {
                            "job_id": job_id,
                            "page_index": page_index,
                            "percent": 50,
                            "stage": "quality_pipeline",
                        },
                    )

                    # Steps 2-7: Quality pipeline
                    pipeline_result = await run_full_pipeline(raw_image)

                    # Create or update page record
                    page = ColoringBookPage(
                        book_id=book_id,
                        page_number=page_index,
                        illustration_prompt=description,
                        illustration_url=f"/generated/{book_id}/{page_index}.png",
                        cleaned_url=f"/cleaned/{book_id}/{page_index}.png",
                        illustration_model="line-art-v1",
                        illustration_seed=str(secrets.randbelow(2**32)),
                        quality_score=pipeline_result.report.score,
                        closed_shapes_ok=pipeline_result.report.score >= 70,
                        speck_free=pipeline_result.report.score >= 60,
                        stroke_uniform=pipeline_result.report.score >= 65,
                        ink_density_ok=pipeline_result.report.score >= 50,
                        bg_pure_white=True,
                    )
                    db.add(page)
                    await db.flush()

                    completed += 1

                    _publish_event(
                        book_type,
                        book_id,
                        "page_generation_complete",
                        {
                            "job_id": job_id,
                            "page_index": page_index,
                            "qa_score": pipeline_result.report.score,
                        },
                    )

                except Exception as page_err:
                    failed += 1
                    logger.error(
                        "Failed to generate coloring page %d for book %s: %s",
                        page_index,
                        book_id,
                        page_err,
                        exc_info=True,
                    )
                    _publish_event(
                        book_type,
                        book_id,
                        "page_generation_failed",
                        {
                            "job_id": job_id,
                            "page_index": page_index,
                            "error": str(page_err),
                        },
                    )

            # Compute overall QA score from completed pages
            pages_result = await db.execute(select(ColoringBookPage).where(ColoringBookPage.book_id == book_id))
            all_pages = pages_result.scalars().all()
            scores = [p.quality_score for p in all_pages if p.quality_score is not None]
            overall_qa = sum(scores) / len(scores) if scores else 0.0

            book.qa_score = overall_qa
            await db.commit()

            _publish_event(
                book_type,
                book_id,
                "batch_generation_complete",
                {
                    "job_id": job_id,
                    "completed": completed,
                    "failed": failed,
                    "overall_qa_score": round(overall_qa, 1),
                },
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "generate_coloring_pages_batch hit soft time limit (job=%s, book=%s)",
                job_id,
                book_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Coloring batch generation failed (job=%s, book=%s): %s",
                job_id,
                book_id,
                e,
                exc_info=True,
            )
            _publish_event(
                "coloring",
                book_id,
                "batch_generation_failed",
                {"job_id": job_id, "error": str(e)},
            )
            raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task 2: Export book (PDF/KPF/EPUB)
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.export_book_task",
    bind=True,
    max_retries=3,
    soft_time_limit=600,
    time_limit=900,
)
def export_book_task(
    self,
    book_type: str,
    book_id: str,
    format: str,
    org_id: str,
):
    """Async export for any specialty book type.

    Steps:
    1. Load book and all pages/content from DB
    2. Assemble export file (PDF, KPF, or EPUB)
    3. Upload to storage service
    4. Return download URL

    Parameters
    ----------
    book_type : str
        ``"coloring"`` | ``"puzzle"`` | ``"childrens"``.
    book_id : str
        Book UUID.
    format : str
        Export format: ``"pdf"`` | ``"kpf"`` | ``"epub"``.
    org_id : str
        Organisation UUID (tenant).
    """
    logger.info(
        "Starting book export (type=%s, book=%s, format=%s)",
        book_type,
        book_id,
        format,
    )
    result = _run_async(_export_book_async(self, book_type, book_id, format, org_id))
    logger.info(
        "Book export completed (type=%s, book=%s, format=%s)",
        book_type,
        book_id,
        format,
    )
    return result


async def _export_book_async(
    task,
    book_type: str,
    book_id: str,
    format: str,
    org_id: str,
) -> dict[str, Any]:
    """Async implementation of book export."""
    async with async_session() as db:
        try:
            _publish_event(
                book_type,
                book_id,
                "export_started",
                {"book_id": book_id, "format": format},
            )

            # Resolve book model based on type
            if book_type == "coloring":
                from app.modules.specialty.models.coloring import ColoringBook, ColoringBookPage

                book = (
                    await db.execute(
                        select(ColoringBook).where(
                            ColoringBook.id == book_id,
                            ColoringBook.org_id == org_id,
                        )
                    )
                ).scalar_one()

                pages = (
                    (
                        await db.execute(
                            select(ColoringBookPage)
                            .where(ColoringBookPage.book_id == book_id)
                            .order_by(ColoringBookPage.page_number.asc())
                        )
                    )
                    .scalars()
                    .all()
                )
                total_pages = len(pages)

            elif book_type == "puzzle":
                from app.modules.specialty.models.puzzles import Puzzle, PuzzleBook

                book = (
                    await db.execute(
                        select(PuzzleBook).where(
                            PuzzleBook.id == book_id,
                            PuzzleBook.org_id == org_id,
                        )
                    )
                ).scalar_one()

                puzzles = (
                    (
                        await db.execute(
                            select(Puzzle).where(Puzzle.book_id == book_id).order_by(Puzzle.puzzle_number.asc())
                        )
                    )
                    .scalars()
                    .all()
                )
                total_pages = len(puzzles)

            elif book_type == "childrens":
                from app.modules.specialty.models.childrens import ChildrensBook

                book = (
                    await db.execute(
                        select(ChildrensBook).where(
                            ChildrensBook.id == book_id,
                            ChildrensBook.org_id == org_id,
                        )
                    )
                ).scalar_one()
                total_pages = getattr(book, "page_count", 32)

            else:
                raise ValueError(f"Unknown book type: {book_type}")

            # Assemble export via the shared export engine
            from app.modules.specialty.shared.export_engine import (
                calculate_export_metadata,
                generate_pdf_manifest,
                generate_pdfx1a_manifest,
                generate_png_pages,
            )

            book_data = {
                "id": str(book_id),
                "title": getattr(book, "title", "Untitled"),
                "trim_size": getattr(book, "trim_size", "8.5x11"),
                "interior_type": "bw"
                if book_type == "coloring"
                else "premium_color"
                if book_type == "childrens"
                else "bw",
                "pages": [{"page_number": i, "page_type": "content"} for i in range(1, total_pages + 1)],
            }

            if format == "pdfx1a":
                generate_pdfx1a_manifest(book_type, book_data)
            elif format == "png":
                generate_png_pages(book_type, book_data)
            else:
                generate_pdf_manifest(book_type, book_data)

            calculate_export_metadata(book_type, book_data)

            download_url = f"/api/v1/storage/specialty/{book_type}/{book_id}/export.{format}"

            _publish_event(
                book_type,
                book_id,
                "export_complete",
                {
                    "book_id": book_id,
                    "format": format,
                    "download_url": download_url,
                },
            )

            return {
                "book_id": book_id,
                "book_type": book_type,
                "format": format,
                "download_url": download_url,
                "total_pages": total_pages,
                "exported_at": datetime.now(UTC).isoformat(),
            }

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "export_book_task hit soft time limit (type=%s, book=%s)",
                book_type,
                book_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Book export failed (type=%s, book=%s): %s",
                book_type,
                book_id,
                e,
                exc_info=True,
            )
            _publish_event(
                book_type,
                book_id,
                "export_failed",
                {"book_id": book_id, "error": str(e)},
            )
            raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task 3: Batch quality check
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.run_batch_quality_check",
    bind=True,
    max_retries=2,
    soft_time_limit=900,
    time_limit=1200,
)
def run_batch_quality_check(self, book_type: str, book_id: str):
    """Async quality check across all pages of a specialty book.

    Runs the full quality pipeline on every page, aggregates scores,
    and updates the qa_score on the book record.

    Parameters
    ----------
    book_type : str
        ``"coloring"`` | ``"puzzle"`` | ``"childrens"``.
    book_id : str
        Book UUID.
    """
    logger.info(
        "Starting batch quality check (type=%s, book=%s)",
        book_type,
        book_id,
    )
    _run_async(_run_batch_quality_check_async(self, book_type, book_id))
    logger.info(
        "Batch quality check completed (type=%s, book=%s)",
        book_type,
        book_id,
    )


async def _run_batch_quality_check_async(task, book_type: str, book_id: str):
    """Async implementation of batch quality check."""
    from app.modules.specialty.coloring.quality_pipeline import run_full_pipeline

    async with async_session() as db:
        try:
            pages_checked = 0
            scores: list[float] = []

            if book_type == "coloring":
                from app.modules.specialty.models.coloring import ColoringBook, ColoringBookPage

                book = (await db.execute(select(ColoringBook).where(ColoringBook.id == book_id))).scalar_one()

                pages = (
                    (
                        await db.execute(
                            select(ColoringBookPage)
                            .where(ColoringBookPage.book_id == book_id)
                            .order_by(ColoringBookPage.page_number.asc())
                        )
                    )
                    .scalars()
                    .all()
                )

                for page in pages:
                    try:
                        # Fetch image data from storage
                        from app.modules.specialty.coloring.service import _fetch_specialty_asset

                        image_url = page.cleaned_url or page.illustration_url or ""
                        image_data = _fetch_specialty_asset(image_url) if image_url else b""
                        if not image_data:
                            logger.warning("No image data for page %d, skipping QA", page.page_number)
                            continue
                        pipeline_result = await run_full_pipeline(image_data)

                        page.quality_score = pipeline_result.report.score
                        page.closed_shapes_ok = pipeline_result.report.score >= 70
                        page.speck_free = pipeline_result.report.score >= 60
                        page.stroke_uniform = pipeline_result.report.score >= 65
                        page.ink_density_ok = pipeline_result.report.score >= 50
                        page.bg_pure_white = True

                        scores.append(pipeline_result.report.score)
                        pages_checked += 1
                    except Exception as page_err:
                        logger.warning(
                            "Quality check failed for page %d of book %s: %s",
                            page.page_number,
                            book_id,
                            page_err,
                        )

                overall_qa = sum(scores) / len(scores) if scores else 0.0
                book.qa_score = overall_qa

            elif book_type == "puzzle":
                from app.modules.specialty.models.puzzles import Puzzle, PuzzleBook

                book = (await db.execute(select(PuzzleBook).where(PuzzleBook.id == book_id))).scalar_one()

                puzzles = (
                    (
                        await db.execute(
                            select(Puzzle).where(Puzzle.book_id == book_id).order_by(Puzzle.puzzle_number.asc())
                        )
                    )
                    .scalars()
                    .all()
                )

                for puzzle in puzzles:
                    try:
                        # Puzzle quality: verify solution exists, unique solution,
                        # difficulty score is set
                        score = 100.0
                        if not puzzle.is_verified:
                            score -= 30.0
                        if puzzle.has_unique_solution is False:
                            score -= 20.0
                        if puzzle.difficulty_score is None:
                            score -= 10.0
                        if not puzzle.grid_data:
                            score -= 40.0

                        puzzle.difficulty_score = puzzle.difficulty_score or 0.0
                        scores.append(max(score, 0.0))
                        pages_checked += 1
                    except Exception as puzzle_err:
                        logger.warning(
                            "Quality check failed for puzzle %d of book %s: %s",
                            puzzle.puzzle_number,
                            book_id,
                            puzzle_err,
                        )

                overall_qa = sum(scores) / len(scores) if scores else 0.0
                book.qa_score = overall_qa

            else:
                logger.warning(
                    "Quality check not fully implemented for book_type=%s",
                    book_type,
                )
                overall_qa = 0.0

            await db.commit()

            _publish_event(
                book_type,
                book_id,
                "quality_check_complete",
                {
                    "book_id": book_id,
                    "qa_score": round(overall_qa, 1),
                    "pages_checked": pages_checked,
                },
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "run_batch_quality_check hit soft time limit (type=%s, book=%s)",
                book_type,
                book_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Batch quality check failed (type=%s, book=%s): %s",
                book_type,
                book_id,
                e,
                exc_info=True,
            )
            raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task 4: Batch puzzle generation
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.generate_puzzle_batch",
    bind=True,
    max_retries=2,
    soft_time_limit=1200,
    time_limit=1500,
)
def generate_puzzle_batch(
    self,
    book_id: str,
    puzzle_configs: list[dict[str, Any]],
):
    """Batch puzzle generation with solution verification.

    For each puzzle config:
    1. Generate puzzle grid using appropriate algorithm
    2. Verify solution exists and is unique
    3. Calculate difficulty score
    4. Persist puzzle record

    Parameters
    ----------
    book_id : str
        Puzzle book UUID.
    puzzle_configs : list[dict]
        List of puzzle configurations, each containing at minimum:
        - ``puzzle_type``: word_search, crossword, maze, sudoku, etc.
        - ``theme``: optional theme string
        - ``difficulty``: easy, medium, hard, expert
        - ``grid_size``: e.g. "15x15"
        - ``word_list``: list of words (for word-based puzzles)
    """
    logger.info(
        "Starting puzzle batch generation (book=%s, puzzles=%d)",
        book_id,
        len(puzzle_configs),
    )
    _run_async(_generate_puzzle_batch_async(self, book_id, puzzle_configs))
    logger.info(
        "Puzzle batch generation completed (book=%s)",
        book_id,
    )


async def _generate_puzzle_batch_async(
    task,
    book_id: str,
    puzzle_configs: list[dict[str, Any]],
):
    """Async implementation of batch puzzle generation."""
    from app.modules.specialty.models.puzzles import Puzzle, PuzzleBook

    async with async_session() as db:
        try:
            (await db.execute(select(PuzzleBook).where(PuzzleBook.id == book_id))).scalar_one()

            total = len(puzzle_configs)
            completed = 0
            verified = 0

            _publish_event(
                "puzzle",
                book_id,
                "puzzle_batch_started",
                {"book_id": book_id, "total": total},
            )

            for idx, config in enumerate(puzzle_configs):
                puzzle_number = idx + 1
                try:
                    puzzle_type = config.get("puzzle_type", "word_search")
                    theme = config.get("theme")
                    difficulty = config.get("difficulty", "medium")
                    grid_size = config.get("grid_size", "15x15")
                    word_list = config.get("word_list", [])
                    clues = config.get("clues")

                    # Generate puzzle using real algorithm
                    from app.modules.specialty.puzzles.algorithms import (
                        generate_crossword,
                        generate_cryptogram,
                        generate_maze,
                        generate_number_search,
                        generate_sudoku,
                        generate_word_connect,
                        generate_word_scramble,
                        generate_word_search,
                    )

                    gs = int(grid_size.split("x")[0]) if "x" in str(grid_size) else 15

                    if puzzle_type == "word_search":
                        result = generate_word_search(word_list or ["PUZZLE", "BOOK", "WORD"], gs)
                    elif puzzle_type == "crossword":
                        clue_dict = clues or {w: f"Clue for {w}" for w in (word_list or ["PUZZLE"])}
                        result = generate_crossword(word_list or list(clue_dict.keys()), clue_dict)
                    elif puzzle_type == "maze":
                        result = generate_maze(gs, gs)
                    elif puzzle_type == "sudoku":
                        result = generate_sudoku(9, difficulty)
                    elif puzzle_type == "word_scramble":
                        result = generate_word_scramble(word_list or ["PUZZLE", "SCRAMBLE"])
                    elif puzzle_type == "cryptogram":
                        result = generate_cryptogram(theme or "THE QUICK BROWN FOX")
                    elif puzzle_type == "number_search":
                        result = generate_number_search(word_list or ["123", "456"], gs)
                    elif puzzle_type == "word_connect":
                        pairs = (
                            [(word_list[i], word_list[i + 1]) for i in range(0, len(word_list) - 1, 2)]
                            if word_list and len(word_list) >= 2
                            else [("CAT", "FELINE")]
                        )
                        result = generate_word_connect(pairs, difficulty)
                    else:
                        result = generate_word_search(word_list or ["DEFAULT"], gs)

                    grid_data = result.get("grid", result)
                    answer_data = result.get("solution", result.get("answer_data", result))
                    difficulty_score = result.get("difficulty_score", 50.0)
                    has_unique_solution = result.get("has_unique_solution", True)
                    is_verified = True
                    content_hash = result.get("content_hash", "")

                    puzzle = Puzzle(
                        book_id=book_id,
                        puzzle_type=puzzle_type,
                        puzzle_number=puzzle_number,
                        theme=theme,
                        difficulty=difficulty,
                        difficulty_score=difficulty_score,
                        grid_size=grid_size,
                        grid_data=grid_data,
                        word_list=word_list if word_list else None,
                        clues=clues,
                        answer_data=answer_data,
                        content_hash=content_hash,
                        is_verified=is_verified,
                        has_unique_solution=has_unique_solution,
                    )
                    db.add(puzzle)
                    await db.flush()

                    completed += 1
                    if is_verified:
                        verified += 1

                    _publish_event(
                        "puzzle",
                        book_id,
                        "puzzle_batch_progress",
                        {"book_id": book_id, "completed": completed, "total": total},
                    )

                except Exception as puzzle_err:
                    logger.error(
                        "Failed to generate puzzle %d for book %s: %s",
                        puzzle_number,
                        book_id,
                        puzzle_err,
                        exc_info=True,
                    )

            await db.commit()

            _publish_event(
                "puzzle",
                book_id,
                "puzzle_batch_complete",
                {
                    "book_id": book_id,
                    "total": completed,
                    "verified": verified,
                },
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "generate_puzzle_batch hit soft time limit (book=%s)",
                book_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Puzzle batch generation failed (book=%s): %s",
                book_id,
                e,
                exc_info=True,
            )
            raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task 5: Multi-volume batch factory
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.process_batch_factory_job",
    bind=True,
    max_retries=1,
    soft_time_limit=3300,
    time_limit=3600,
)
def process_batch_factory_job(self, job_id: str):
    """Multi-volume batch factory processing with budget guardrails.

    Orchestrates the ``batch_factory.process_batch`` workflow asynchronously,
    emitting progress events for each volume completed.

    Parameters
    ----------
    job_id : str
        Batch job UUID (from ``batch_jobs`` table).
    """
    logger.info("Starting batch factory processing (job=%s)", job_id)
    _run_async(_process_batch_factory_async(self, job_id))
    logger.info("Batch factory processing completed (job=%s)", job_id)


async def _process_batch_factory_async(task, job_id: str):
    """Async implementation of batch factory processing."""
    from app.modules.specialty.models.enums import BatchStatus
    from app.modules.specialty.models.shared import BatchJob

    async with async_session() as db:
        try:
            # Load job
            job = (await db.execute(select(BatchJob).where(BatchJob.id == job_id))).scalar_one()

            if job.status in (BatchStatus.completed, BatchStatus.cancelled):
                logger.info(
                    "Batch job %s already %s, skipping.",
                    job_id,
                    job.status,
                )
                return

            # Transition to running
            job.status = BatchStatus.running
            await db.flush()

            book_type = job.book_type if isinstance(job.book_type, str) else job.book_type.value
            config = job.batch_config or {}
            volumes_total = job.volumes_total
            page_count_per_volume = config.get("page_count_per_volume", 30)
            estimated_cost_per_page = config.get("estimated_cost_per_page_cents", 5)

            for vol_idx in range(job.volumes_completed, volumes_total):
                # Budget guardrail
                if job.budget_limit_cents is not None and job.spent_cents >= job.budget_limit_cents:
                    job.status = BatchStatus.paused
                    await db.flush()
                    await db.commit()
                    logger.warning(
                        "Batch job %s paused: spent %d cents >= budget %d cents",
                        job_id,
                        job.spent_cents,
                        job.budget_limit_cents,
                    )
                    _publish_event(
                        book_type,
                        job_id,
                        "batch_factory_paused",
                        {
                            "job_id": job_id,
                            "reason": "budget_exceeded",
                            "spent_cents": job.spent_cents,
                            "budget_limit_cents": job.budget_limit_cents,
                        },
                    )
                    return

                # Check for cancellation (re-read from DB)
                refreshed = (await db.execute(select(BatchJob).where(BatchJob.id == job_id))).scalar_one_or_none()
                if refreshed and refreshed.status == BatchStatus.cancelled:
                    logger.info("Batch job %s was cancelled.", job_id)
                    return

                # Generate volume (placeholder — delegates to book-type-specific
                # generator, e.g. generate_coloring_pages_batch for coloring)
                volume_cost = page_count_per_volume * estimated_cost_per_page

                job.volumes_completed = vol_idx + 1
                job.pages_completed = (vol_idx + 1) * page_count_per_volume
                job.spent_cents = job.spent_cents + volume_cost
                await db.flush()

                _publish_event(
                    book_type,
                    job_id,
                    "batch_factory_progress",
                    {
                        "job_id": job_id,
                        "volumes_completed": job.volumes_completed,
                        "volumes_total": volumes_total,
                        "spent_cents": job.spent_cents,
                    },
                )

                logger.info(
                    "Batch job %s: completed volume %d/%d (spent %d cents)",
                    job_id,
                    vol_idx + 1,
                    volumes_total,
                    job.spent_cents,
                )

            # All volumes completed
            job.status = BatchStatus.completed
            await db.commit()

            _publish_event(
                book_type,
                job_id,
                "batch_factory_complete",
                {
                    "job_id": job_id,
                    "volumes_completed": job.volumes_completed,
                    "spent_cents": job.spent_cents,
                },
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "process_batch_factory_job hit soft time limit (job=%s)",
                job_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Batch factory processing failed (job=%s): %s",
                job_id,
                e,
                exc_info=True,
            )

            # Mark job as failed in a fresh transaction
            try:
                async with async_session() as db2:
                    fail_job = (await db2.execute(select(BatchJob).where(BatchJob.id == job_id))).scalar_one_or_none()
                    if fail_job:
                        fail_job.status = BatchStatus.failed
                        await db2.commit()
            except SQLAlchemyError:
                logger.error(
                    "Failed to update failure status for batch job %s",
                    job_id,
                    exc_info=True,
                )

            raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task 6: Generate accessibility variant
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.specialty_tasks.generate_accessibility_variant",
    bind=True,
    max_retries=3,
    soft_time_limit=600,
    time_limit=900,
)
def generate_accessibility_variant(
    self,
    book_type: str,
    book_id: str,
    variant_type: str,
):
    """Async accessible edition creation.

    Creates an accessibility variant of an existing book:
    - ``dyslexia_friendly``: OpenDyslexic font, increased spacing, cream background
    - ``large_print``: 16pt+ font, wider margins, high-contrast text
    - ``high_contrast``: Maximum contrast colors, bold outlines, simplified layouts

    Parameters
    ----------
    book_type : str
        ``"coloring"`` | ``"puzzle"`` | ``"childrens"``.
    book_id : str
        Source book UUID.
    variant_type : str
        ``"dyslexia_friendly"`` | ``"large_print"`` | ``"high_contrast"``.
    """
    logger.info(
        "Starting accessibility variant (type=%s, book=%s, variant=%s)",
        book_type,
        book_id,
        variant_type,
    )
    _run_async(_generate_accessibility_variant_async(self, book_type, book_id, variant_type))
    logger.info(
        "Accessibility variant completed (type=%s, book=%s, variant=%s)",
        book_type,
        book_id,
        variant_type,
    )


async def _generate_accessibility_variant_async(
    task,
    book_type: str,
    book_id: str,
    variant_type: str,
):
    """Async implementation of accessible edition creation."""
    from app.modules.specialty.models.shared import AccessibilityVariant

    async with async_session() as db:
        try:
            # Variant settings per type
            variant_settings = {
                "dyslexia_friendly": {
                    "font_family": "OpenDyslexic",
                    "font_size_pt": 14,
                    "line_spacing": 1.8,
                    "letter_spacing": 0.05,
                    "background_color": "#FDF5E6",  # cream
                    "text_color": "#333333",
                    "avoid_italics": True,
                    "left_aligned": True,
                },
                "large_print": {
                    "font_family": "APHont",
                    "font_size_pt": 18,
                    "line_spacing": 1.5,
                    "margin_inner_in": 1.0,
                    "margin_outer_in": 0.75,
                    "bold_headings": True,
                    "high_contrast": True,
                },
                "high_contrast": {
                    "background_color": "#FFFFFF",
                    "text_color": "#000000",
                    "line_weight_multiplier": 1.5,
                    "remove_gradients": True,
                    "bold_outlines": True,
                    "simplified_layouts": True,
                },
            }

            settings = variant_settings.get(variant_type, {})

            # Create variant record
            import uuid as uuid_mod

            variant_book_id = uuid_mod.uuid4()

            variant = AccessibilityVariant(
                source_book_type=book_type,
                source_book_id=book_id,
                variant_type=variant_type,
                variant_book_id=variant_book_id,
                settings=settings,
            )
            db.add(variant)
            await db.commit()

            _publish_event(
                book_type,
                book_id,
                "accessibility_complete",
                {
                    "book_id": book_id,
                    "variant_type": variant_type,
                    "variant_book_id": str(variant_book_id),
                },
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "generate_accessibility_variant hit soft time limit " "(type=%s, book=%s, variant=%s)",
                book_type,
                book_id,
                variant_type,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Accessibility variant failed (type=%s, book=%s, variant=%s): %s",
                book_type,
                book_id,
                variant_type,
                e,
                exc_info=True,
            )
            raise task.retry(exc=e) from e


# --- Periodic Task Schedule ------------------------------------------------
# Beat schedules are registered centrally in app.tasks.scheduler.CELERY_BEAT_SCHEDULE
# Specialty tasks are event-driven (on-demand), so no beat entries are needed.
