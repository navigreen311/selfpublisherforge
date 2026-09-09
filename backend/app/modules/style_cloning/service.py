"""Style Cloning Service — orchestrates profile CRUD and the NLP pipeline."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models.content import StyleProfile
from app.modules.style_cloning.analyzers import (
    RhythmAnalyzer,
    SyntaxAnalyzer,
    ToneAnalyzer,
    VocabularyAnalyzer,
)
from app.modules.style_cloning.conformity import check_conformity
from app.modules.style_cloning.features import extract_all_features
from app.modules.style_cloning.ingestion import (
    SegmentedText,
    ingest_text,
    merge_segmented,
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
    TuneRequest,
    UpdateProfileRequest,
    VoiceFingerprint,
)

# ---------------------------------------------------------------------------
# ORM -> Response conversion
# ---------------------------------------------------------------------------


def _to_response(profile: StyleProfile) -> ProfileResponse:
    """Convert an ORM StyleProfile instance to a ProfileResponse schema."""
    # Reconstruct StyleCard from the stored dict if present
    style_card: StyleCard | None = None
    if profile.style_card is not None:
        style_card = StyleCard(**profile.style_card)

    return ProfileResponse(
        id=profile.id,
        org_id=profile.org_id,
        name=profile.name,
        description=profile.description or "",
        genre=profile.genre or "",
        status=ProfileStatus(profile.status),
        word_count=profile.word_count,
        sample_count=profile.sample_count,
        confidence=profile.confidence,
        style_card=style_card,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def _run_analysis(profile: StyleProfile) -> None:
    """Run the full NLP pipeline on accumulated samples.

    Mutates the ORM instance in place with analysis results.
    """
    sample_texts = profile.sample_texts or []
    segments: list[SegmentedText] = []
    for text in sample_texts:
        segments.append(ingest_text(text))
    if not segments:
        profile.status = ProfileStatus.failed.value
        return

    merged = merge_segmented(segments)
    profile.word_count = merged.word_count
    profile.sample_count = len(sample_texts)
    profile.confidence = compute_confidence(merged.word_count)

    try:
        # Extract traditional features
        features = extract_all_features(merged)

        # Run deep NLP analyzers
        syntax_analyzer = SyntaxAnalyzer()
        rhythm_analyzer = RhythmAnalyzer()
        vocabulary_analyzer = VocabularyAnalyzer()
        tone_analyzer = ToneAnalyzer()

        syntax_metrics = syntax_analyzer.analyze(merged.raw_text)
        rhythm_metrics = rhythm_analyzer.analyze(merged.raw_text)
        vocabulary_metrics = vocabulary_analyzer.analyze(merged.raw_text)
        tone_metrics = tone_analyzer.analyze(merged.raw_text)

        # Generate fingerprint and style card
        fingerprint = generate_voice_fingerprint(features, merged)
        style_card = generate_style_card(features, merged)

        # Enhance fingerprint with deep NLP metrics
        fingerprint_dict = fingerprint.model_dump()
        fingerprint_dict["deep_analysis"] = {
            "syntax": syntax_metrics,
            "rhythm": rhythm_metrics,
            "vocabulary": vocabulary_metrics,
            "tone": tone_metrics,
        }

        # Store as dicts in JSONB columns
        profile.voice_fingerprint = fingerprint_dict
        profile.style_card = style_card.model_dump()
        profile.status = ProfileStatus.ready.value

        logger.info(
            "Style analysis complete for profile %s: %d words, confidence %.2f",
            profile.id,
            merged.word_count,
            profile.confidence,
        )
    except (ValueError, TypeError, KeyError) as exc:
        logger.error("Style analysis pipeline failed: %s", exc, exc_info=True)
        profile.status = ProfileStatus.failed.value
        raise
    finally:
        profile.updated_at = datetime.now(UTC)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def create_profile(
    db: AsyncSession,
    org_id: uuid.UUID,
    request: CreateProfileRequest,
) -> ProfileResponse:
    """Create a new style profile and optionally begin analysis."""
    profile = StyleProfile(
        org_id=org_id,
        name=request.name,
        description=request.description,
        genre=request.genre,
        status=ProfileStatus.pending.value,
        sample_texts=request.sample_texts if request.sample_texts else None,
    )

    if request.sample_texts:
        profile.status = ProfileStatus.analyzing.value
        _run_analysis(profile)

    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return _to_response(profile)


async def list_profiles(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> ProfileListResponse:
    """List all non-deleted profiles for an org."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
        .order_by(StyleProfile.created_at.desc())
    )
    result = await db.execute(stmt)
    profiles = result.scalars().all()
    items = [_to_response(p) for p in profiles]
    return ProfileListResponse(items=items, total=len(items))


async def get_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
) -> ProfileResponse | None:
    """Get a single profile by ID."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None
    return _to_response(profile)


async def get_fingerprint(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
) -> FingerprintResponse | None:
    """Get the full voice fingerprint for a profile."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None
    if profile.voice_fingerprint is None:
        return None
    # Reconstruct VoiceFingerprint from the stored dict
    fingerprint = VoiceFingerprint(**profile.voice_fingerprint)
    return FingerprintResponse(
        profile_id=profile.id,
        fingerprint=fingerprint,
    )


async def analyze_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    sample_texts: list[str],
) -> ProfileResponse | None:
    """Add samples and re-analyze."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None

    # Append new sample texts to existing ones
    existing_samples = profile.sample_texts or []
    profile.sample_texts = existing_samples + sample_texts
    profile.status = ProfileStatus.analyzing.value
    _run_analysis(profile)

    await db.flush()
    await db.refresh(profile)
    return _to_response(profile)


async def delete_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
) -> bool:
    """Soft delete a profile."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return False

    now = datetime.now(UTC)
    profile.deleted_at = now
    profile.updated_at = now
    await db.flush()
    return True


async def conformity_check(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    text: str,
) -> ConformityCheckResult | None:
    """Check text conformity against a profile's fingerprint."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None
    if profile.voice_fingerprint is None:
        return None

    # Reconstruct VoiceFingerprint from the stored dict
    fingerprint = VoiceFingerprint(**profile.voice_fingerprint)
    return check_conformity(fingerprint, text)


async def tune_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    request: TuneRequest,
) -> ProfileResponse | None:
    """Update tuning adjustment parameters for a profile."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None

    profile.tuning_adjustments = request.model_dump()
    profile.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(profile)
    return _to_response(profile)


async def update_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    org_id: uuid.UUID,
    request: UpdateProfileRequest,
) -> ProfileResponse | None:
    """Update basic profile info (name, description, genre)."""
    stmt = (
        select(StyleProfile)
        .where(StyleProfile.id == profile_id)
        .where(StyleProfile.org_id == org_id)
        .where(StyleProfile.deleted_at == None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    profile.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(profile)
    return _to_response(profile)
