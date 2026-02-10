"""Style Cloning Service — orchestrates profile CRUD and the NLP pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.style_cloning.conformity import check_conformity
from app.modules.style_cloning.features import extract_all_features
from app.modules.style_cloning.ingestion import (
    SegmentedText,
    ingest_text,
    merge_segmented,
    MIN_WORDS,
)
from app.modules.style_cloning.profile_generator import (
    compute_confidence,
    generate_style_card,
    generate_voice_fingerprint,
)
from app.modules.style_cloning.schemas import (
    ConformityCheckResult,
    CreateProfileRequest,
    FingerprintResponse,
    ProfileListResponse,
    ProfileResponse,
    ProfileStatus,
    StyleCard,
    VoiceFingerprint,
)


# ---------------------------------------------------------------------------
# In-memory store (production would use the DB model from W02)
# ---------------------------------------------------------------------------

class _ProfileRecord:
    """Lightweight in-memory representation of a style_profile row."""

    def __init__(
        self,
        *,
        id: uuid.UUID,
        org_id: uuid.UUID,
        name: str,
        description: str = "",
        genre: str = "",
    ):
        self.id = id
        self.org_id = org_id
        self.name = name
        self.description = description
        self.genre = genre
        self.status: ProfileStatus = ProfileStatus.pending
        self.word_count: int = 0
        self.sample_count: int = 0
        self.confidence: float = 0.0
        self.style_card: Optional[StyleCard] = None
        self.fingerprint: Optional[VoiceFingerprint] = None
        self.sample_texts: list[str] = []
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)
        self.deleted_at: Optional[datetime] = None


# Module-level store — replaced by real DB in production
_store: dict[uuid.UUID, _ProfileRecord] = {}


def _reset_store() -> None:
    """Reset the in-memory store (used in tests)."""
    _store.clear()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def _to_response(rec: _ProfileRecord) -> ProfileResponse:
    return ProfileResponse(
        id=rec.id,
        org_id=rec.org_id,
        name=rec.name,
        description=rec.description,
        genre=rec.genre,
        status=rec.status,
        word_count=rec.word_count,
        sample_count=rec.sample_count,
        confidence=rec.confidence,
        style_card=rec.style_card,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

def _run_analysis(rec: _ProfileRecord) -> None:
    """Run the full NLP pipeline on accumulated samples."""
    segments: list[SegmentedText] = []
    for text in rec.sample_texts:
        segments.append(ingest_text(text))
    if not segments:
        rec.status = ProfileStatus.failed
        return

    merged = merge_segmented(segments)
    rec.word_count = merged.word_count
    rec.sample_count = len(rec.sample_texts)
    rec.confidence = compute_confidence(merged.word_count)

    try:
        features = extract_all_features(merged)
        rec.fingerprint = generate_voice_fingerprint(features, merged)
        rec.style_card = generate_style_card(features, merged)
        rec.status = ProfileStatus.ready
    except Exception:
        rec.status = ProfileStatus.failed
        raise
    finally:
        rec.updated_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def create_profile(
    org_id: uuid.UUID,
    request: CreateProfileRequest,
    db: Optional[AsyncSession] = None,
) -> ProfileResponse:
    """Create a new style profile and optionally begin analysis."""
    profile_id = uuid.uuid4()
    rec = _ProfileRecord(
        id=profile_id,
        org_id=org_id,
        name=request.name,
        description=request.description,
        genre=request.genre,
    )

    if request.sample_texts:
        rec.sample_texts.extend(request.sample_texts)
        rec.status = ProfileStatus.analyzing
        _run_analysis(rec)
    else:
        rec.status = ProfileStatus.pending

    _store[profile_id] = rec
    return _to_response(rec)


async def list_profiles(
    org_id: uuid.UUID,
    db: Optional[AsyncSession] = None,
) -> ProfileListResponse:
    """List all non-deleted profiles for an org."""
    items = [
        _to_response(r)
        for r in _store.values()
        if r.org_id == org_id and r.deleted_at is None
    ]
    return ProfileListResponse(items=items, total=len(items))


async def get_profile(
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Optional[AsyncSession] = None,
) -> Optional[ProfileResponse]:
    """Get a single profile by ID."""
    rec = _store.get(profile_id)
    if rec is None or rec.org_id != org_id or rec.deleted_at is not None:
        return None
    return _to_response(rec)


async def get_fingerprint(
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Optional[AsyncSession] = None,
) -> Optional[FingerprintResponse]:
    """Get the full voice fingerprint for a profile."""
    rec = _store.get(profile_id)
    if rec is None or rec.org_id != org_id or rec.deleted_at is not None:
        return None
    if rec.fingerprint is None:
        return None
    return FingerprintResponse(
        profile_id=rec.id,
        fingerprint=rec.fingerprint,
    )


async def analyze_profile(
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    sample_texts: list[str],
    db: Optional[AsyncSession] = None,
) -> Optional[ProfileResponse]:
    """Add samples and re-analyze."""
    rec = _store.get(profile_id)
    if rec is None or rec.org_id != org_id or rec.deleted_at is not None:
        return None
    rec.sample_texts.extend(sample_texts)
    rec.status = ProfileStatus.analyzing
    _run_analysis(rec)
    return _to_response(rec)


async def delete_profile(
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Optional[AsyncSession] = None,
) -> bool:
    """Soft delete a profile."""
    rec = _store.get(profile_id)
    if rec is None or rec.org_id != org_id or rec.deleted_at is not None:
        return False
    rec.deleted_at = datetime.now(timezone.utc)
    rec.updated_at = rec.deleted_at
    return True


async def conformity_check(
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    text: str,
    db: Optional[AsyncSession] = None,
) -> Optional[ConformityCheckResult]:
    """Check text conformity against a profile's fingerprint."""
    rec = _store.get(profile_id)
    if rec is None or rec.org_id != org_id or rec.deleted_at is not None:
        return None
    if rec.fingerprint is None:
        return None
    return check_conformity(rec.fingerprint, text)
