"""Asset Provenance & Rights Ledger.

Every AI-generated asset (illustration, line art, puzzle grid, cover) is
recorded with full generation metadata so publishers can demonstrate
provenance for legal and KDP compliance purposes.

Blueprint refs: 6.2, 7.1
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import AssetProvenance


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceRecord:
    """Lightweight representation of a single provenance entry."""

    id: uuid.UUID
    org_id: uuid.UUID
    book_type: str
    book_id: uuid.UUID
    page_id: uuid.UUID | None
    asset_type: str
    model: str | None
    prompt_hash: str | None
    seed: str | None
    settings: dict[str, Any] | None
    generation_date: datetime
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_prompt(prompt_text: str | None) -> str | None:
    """Return the SHA-256 hex digest of *prompt_text*, or ``None``."""
    if not prompt_text:
        return None
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def _row_to_record(row: AssetProvenance) -> ProvenanceRecord:
    return ProvenanceRecord(
        id=row.id,
        org_id=row.org_id,
        book_type=row.book_type,
        book_id=row.book_id,
        page_id=row.page_id,
        asset_type=row.asset_type,
        model=row.model,
        prompt_hash=row.prompt_hash,
        seed=row.seed,
        settings=row.settings,
        generation_date=row.created_at,
        status="recorded",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_provenance_record(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_type: str,
    book_id: uuid.UUID,
    page_id: uuid.UUID | None,
    asset_type: str,
    model: str | None,
    prompt_text: str | None,
    seed: str | None,
    settings: dict[str, Any] | None = None,
) -> ProvenanceRecord:
    """Create and persist a new provenance record for a generated asset.

    The *prompt_text* is hashed (SHA-256) before storage -- the raw prompt
    is stored separately for audit but the hash is the canonical identifier.
    """
    prompt_hash = _sha256_prompt(prompt_text)

    row = AssetProvenance(
        org_id=org_id,
        book_type=book_type,
        book_id=book_id,
        page_id=page_id,
        asset_type=asset_type,
        model=model,
        prompt_text=prompt_text,
        prompt_hash=prompt_hash,
        seed=seed,
        settings=settings,
    )
    db.add(row)
    await db.flush()

    return _row_to_record(row)


async def get_provenance(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
) -> list[ProvenanceRecord]:
    """Return all provenance records for a given book, ordered by creation."""
    stmt = (
        select(AssetProvenance)
        .where(
            AssetProvenance.book_type == book_type,
            AssetProvenance.book_id == book_id,
        )
        .order_by(AssetProvenance.created_at.asc())
    )
    result = await db.execute(stmt)
    return [_row_to_record(row) for row in result.scalars().all()]


async def export_provenance_report(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
) -> dict[str, Any]:
    """Build a structured provenance report suitable for PDF generation.

    Returns a dict with top-level metadata and a list of per-asset entries
    containing model, prompt hash, seed, generation date, and status.
    """
    records = await get_provenance(db, book_type, book_id)

    assets: list[dict[str, Any]] = []
    models_used: set[str] = set()

    for rec in records:
        if rec.model:
            models_used.add(rec.model)
        assets.append(
            {
                "id": str(rec.id),
                "page_id": str(rec.page_id) if rec.page_id else None,
                "asset_type": rec.asset_type,
                "model": rec.model,
                "prompt_hash": rec.prompt_hash,
                "seed": rec.seed,
                "generation_date": rec.generation_date.isoformat(),
                "status": rec.status,
                "settings": rec.settings,
            }
        )

    return {
        "report_type": "provenance",
        "book_type": book_type,
        "book_id": str(book_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_assets": len(assets),
        "models_used": sorted(models_used),
        "assets": assets,
    }
