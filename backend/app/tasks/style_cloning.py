"""Celery tasks for asynchronous style profile analysis.

Large manuscripts can take minutes to analyze — these tasks allow the
analysis to run in the background while the API returns immediately.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from app.tasks import celery_app
from app.modules.style_cloning.ingestion import ingest_text, merge_segmented, SegmentedText
from app.modules.style_cloning.features import extract_all_features
from app.modules.style_cloning.profile_generator import (
    compute_confidence,
    generate_style_card,
    generate_voice_fingerprint,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name="style_cloning.analyze_profile",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def analyze_profile_task(self, profile_id: str, sample_texts: list[str]) -> dict:
    """Run the full NLP pipeline on the given sample texts.

    Parameters
    ----------
    profile_id : str
        UUID of the style profile (as string for JSON serialization).
    sample_texts : list[str]
        Raw text samples to analyze.

    Returns
    -------
    dict
        Analysis results including fingerprint, style card, word count,
        confidence, and status.
    """
    try:
        self.update_state(state="ANALYZING", meta={"profile_id": profile_id})

        # Ingest all samples
        segments: list[SegmentedText] = []
        for text in sample_texts:
            segments.append(ingest_text(text))

        if not segments:
            return {
                "profile_id": profile_id,
                "status": "failed",
                "error": "No sample texts provided",
            }

        merged = merge_segmented(segments)

        # Extract features
        features = extract_all_features(merged)

        # Generate fingerprint and style card
        fingerprint = generate_voice_fingerprint(features, merged)
        style_card = generate_style_card(features, merged)
        confidence = compute_confidence(merged.word_count)

        return {
            "profile_id": profile_id,
            "status": "ready",
            "word_count": merged.word_count,
            "sample_count": len(sample_texts),
            "confidence": confidence,
            "fingerprint": fingerprint.model_dump(),
            "style_card": style_card.model_dump(),
        }

    except (ValueError, TypeError) as exc:
        logger.error("Data error in style analysis for profile %s: %s", profile_id, exc, exc_info=True)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "profile_id": profile_id,
                "status": "failed",
                "error": str(exc),
            }
    except Exception as exc:
        logger.error("Unexpected error in style analysis for profile %s: %s", profile_id, exc, exc_info=True)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "profile_id": profile_id,
                "status": "failed",
                "error": str(exc),
            }


@celery_app.task(
    name="style_cloning.conformity_check",
    bind=True,
    acks_late=True,
)
def conformity_check_task(self, profile_id: str, fingerprint_data: dict, text: str) -> dict:
    """Run a conformity check asynchronously.

    Parameters
    ----------
    profile_id : str
        UUID of the style profile.
    fingerprint_data : dict
        Serialized VoiceFingerprint data.
    text : str
        Text to check against the profile.

    Returns
    -------
    dict
        Conformity check results.
    """
    from app.modules.style_cloning.schemas import VoiceFingerprint
    from app.modules.style_cloning.conformity import check_conformity

    fingerprint = VoiceFingerprint(**fingerprint_data)
    result = check_conformity(fingerprint, text)
    return {
        "profile_id": profile_id,
        **result.model_dump(),
    }
