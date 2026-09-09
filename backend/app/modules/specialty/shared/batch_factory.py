"""Batch Factory Mode for Specialty Books.

Manages multi-volume batch generation jobs with cost tracking, budget
guardrails, and job lifecycle control (create, process, status, cancel).

Uses the ``batch_jobs`` table via SQLAlchemy async sessions.

Usage::

    job = await create_batch_job(db, org_id, "coloring", config, budget)
    status = await get_batch_status(db, job_id)
    await cancel_batch(db, job_id)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.enums import BatchStatus
from app.modules.specialty.models.shared import BatchJob

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default budget limit if none specified (in cents) — $100
DEFAULT_BUDGET_LIMIT_CENTS = 10_000


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_batch_job(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_type: str,
    config: dict[str, Any],
    budget_limit_cents: int | None = None,
) -> dict[str, Any]:
    """Create a new batch generation job.

    Parameters
    ----------
    db:
        Async database session.
    org_id:
        Organisation ID (tenant).
    book_type:
        ``"childrens"`` | ``"coloring"`` | ``"puzzle"``.
    config:
        Batch configuration dict — must include at least ``volumes_total``
        and optionally ``themes``, ``page_count_per_volume``, etc.
    budget_limit_cents:
        Maximum spend in cents.  ``None`` means no explicit limit (but
        the default ``DEFAULT_BUDGET_LIMIT_CENTS`` will be used internally
        as a safety net).

    Returns
    -------
    dict with ``job_id``, ``status``, ``volumes_total``, ``budget_limit_cents``.
    """
    volumes_total = config.get("volumes_total", 1)
    pages_total = config.get("pages_total", volumes_total * config.get("page_count_per_volume", 30))

    effective_budget = budget_limit_cents if budget_limit_cents is not None else DEFAULT_BUDGET_LIMIT_CENTS

    job = BatchJob(
        org_id=org_id,
        book_type=book_type,
        batch_config=config,
        budget_limit_cents=effective_budget,
        spent_cents=0,
        status=BatchStatus.pending,
        volumes_total=volumes_total,
        volumes_completed=0,
        pages_total=pages_total,
        pages_completed=0,
    )
    db.add(job)
    await db.flush()

    logger.info(
        "Created batch job %s for org %s: %d volumes, budget %d cents",
        job.id,
        org_id,
        volumes_total,
        effective_budget,
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "volumes_total": volumes_total,
        "pages_total": pages_total,
        "budget_limit_cents": effective_budget,
    }


# ---------------------------------------------------------------------------
# Process (orchestration skeleton)
# ---------------------------------------------------------------------------


async def process_batch(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> dict[str, Any]:
    """Begin or resume processing a batch job.

    This is the top-level orchestrator for multi-volume generation.
    It updates the job status and iterates over volumes.  Actual
    page-level generation is delegated to book-type-specific generators
    (not implemented here — this function provides the control loop
    and cost-guardrail enforcement).

    Parameters
    ----------
    db:
        Async database session.
    job_id:
        Batch job ID.

    Returns
    -------
    dict with current status snapshot.
    """
    job = await _get_job(db, job_id)
    if job is None:
        return {"error": f"Batch job {job_id} not found."}

    if job.status in (BatchStatus.completed, BatchStatus.cancelled):
        return {
            "job_id": job_id,
            "status": job.status,
            "message": f"Job already {job.status.value}.",
        }

    # Transition to running
    job.status = BatchStatus.running
    await db.flush()

    config = job.batch_config or {}
    volumes_total = job.volumes_total
    volumes_completed = job.volumes_completed

    for vol_idx in range(volumes_completed, volumes_total):
        # --- Budget guardrail ---
        if job.budget_limit_cents is not None and job.spent_cents >= job.budget_limit_cents:
            job.status = BatchStatus.paused
            await db.flush()
            logger.warning(
                "Batch job %s paused: spent %d cents >= budget %d cents",
                job_id,
                job.spent_cents,
                job.budget_limit_cents,
            )
            return {
                "job_id": job_id,
                "status": BatchStatus.paused.value,
                "message": "Budget limit reached. Job paused.",
                "spent_cents": job.spent_cents,
                "budget_limit_cents": job.budget_limit_cents,
                "volumes_completed": job.volumes_completed,
                "volumes_total": volumes_total,
            }

        # --- Check for cancellation ---
        refreshed = await _get_job(db, job_id)
        if refreshed and refreshed.status == BatchStatus.cancelled:
            return {
                "job_id": job_id,
                "status": BatchStatus.cancelled.value,
                "message": "Job was cancelled.",
            }

        # --- Generate volume (placeholder) ---
        # In a real implementation this would call the book-type-specific
        # generator (e.g., coloring page generator, puzzle generator).
        page_count_per_volume = config.get("page_count_per_volume", 30)
        estimated_cost_per_page = config.get("estimated_cost_per_page_cents", 5)
        volume_cost = page_count_per_volume * estimated_cost_per_page

        # Record progress
        job.volumes_completed = vol_idx + 1
        job.pages_completed = (vol_idx + 1) * page_count_per_volume
        job.spent_cents = job.spent_cents + volume_cost
        await db.flush()

        logger.info(
            "Batch job %s: completed volume %d/%d (spent %d cents)",
            job_id,
            vol_idx + 1,
            volumes_total,
            job.spent_cents,
        )

    # All volumes completed
    job.status = BatchStatus.completed
    await db.flush()

    return {
        "job_id": job_id,
        "status": BatchStatus.completed.value,
        "volumes_completed": job.volumes_completed,
        "volumes_total": volumes_total,
        "pages_completed": job.pages_completed,
        "spent_cents": job.spent_cents,
    }


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


async def get_batch_status(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the current status of a batch job.

    Returns
    -------
    dict with ``status``, ``progress``, ``completed``, ``failed``,
    ``cost_spent``, and other metadata.
    """
    job = await _get_job(db, job_id)
    if job is None:
        return {"error": f"Batch job {job_id} not found."}

    progress = 0.0
    if job.volumes_total > 0:
        progress = round(job.volumes_completed / job.volumes_total * 100, 1)

    return {
        "job_id": job.id,
        "status": job.status.value if isinstance(job.status, BatchStatus) else job.status,
        "progress": progress,
        "completed": job.volumes_completed,
        "failed": 0,  # placeholder — real impl tracks per-volume failures
        "cost_spent": job.spent_cents,
        "budget_limit_cents": job.budget_limit_cents,
        "volumes_total": job.volumes_total,
        "pages_total": job.pages_total,
        "pages_completed": job.pages_completed,
        "config": job.batch_config,
    }


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


async def cancel_batch(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> dict[str, Any]:
    """Cancel a running or pending batch job.

    Returns
    -------
    dict with ``job_id``, ``status``, ``message``.
    """
    job = await _get_job(db, job_id)
    if job is None:
        return {"error": f"Batch job {job_id} not found."}

    if job.status in (BatchStatus.completed, BatchStatus.cancelled):
        return {
            "job_id": job_id,
            "status": job.status.value if isinstance(job.status, BatchStatus) else job.status,
            "message": f"Job is already {job.status.value if isinstance(job.status, BatchStatus) else job.status}.",
        }

    job.status = BatchStatus.cancelled
    await db.flush()

    logger.info("Batch job %s cancelled.", job_id)

    return {
        "job_id": job_id,
        "status": BatchStatus.cancelled.value,
        "message": "Batch job cancelled successfully.",
        "volumes_completed": job.volumes_completed,
        "spent_cents": job.spent_cents,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_job(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> BatchJob | None:
    """Fetch a BatchJob by ID."""
    stmt = select(BatchJob).where(BatchJob.id == job_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
