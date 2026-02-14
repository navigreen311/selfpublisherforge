"""FastAPI router for the Style Cloning Engine API endpoints."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.llm_orchestration.providers.anthropic import AnthropicProvider
from app.modules.llm_orchestration.providers.base import LLMRequest
from app.modules.llm_orchestration.router_config import ModelID
from app.modules.style_cloning import service
from app.modules.style_cloning.schemas import (
    AnalyzeRequest,
    ConformityCheckRequest,
    ConformityCheckResult,
    CreateProfileRequest,
    FingerprintResponse,
    GenerateSampleRequest,
    ProfileListResponse,
    ProfileResponse,
    TuneRequest,
    UpdateProfileRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new style profile",
    description="Upload sample manuscripts to create a new voice profile for style cloning.",
)
async def create_profile(
    body: CreateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload sample manuscripts to create a new voice profile."""
    org_id = current_user["org_id"]
    return await service.create_profile(db, org_id, body)


@router.get(
    "",
    response_model=ProfileListResponse,
    summary="List org style profiles",
    description="List all style profiles belonging to the organization.",
)
async def list_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    return await service.list_profiles(db, org_id)


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get profile details",
    description="Get full details of a style profile including style card data.",
)
async def get_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    result = await service.get_profile(db, profile_id, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.get(
    "/{profile_id}/fingerprint",
    response_model=FingerprintResponse,
    summary="Get full voice fingerprint",
    description="Get the detailed voice fingerprint analysis for a style profile.",
)
async def get_fingerprint(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    result = await service.get_fingerprint(db, profile_id, org_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Fingerprint not available — profile may not be analyzed yet",
        )
    return result


@router.patch(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Update profile basic info",
    description="Update a style profile's name, description, or genre.",
)
async def update_profile(
    profile_id: uuid.UUID,
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update basic profile info (name, description, genre)."""
    org_id = current_user["org_id"]
    result = await service.update_profile(db, profile_id, org_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.patch(
    "/{profile_id}/tune",
    response_model=ProfileResponse,
    summary="Adjust style tuning parameters",
    description="Adjust style tuning parameters such as formality, warmth, sentence length, and complexity.",
)
async def tune_profile(
    profile_id: uuid.UUID,
    body: TuneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Adjust style tuning parameters."""
    org_id = current_user["org_id"]
    result = await service.tune_profile(db, profile_id, org_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post(
    "/{profile_id}/analyze",
    response_model=ProfileResponse,
    summary="Add samples and re-analyze",
    description="Add new sample texts and re-analyze the style profile.",
)
async def analyze_profile(
    profile_id: uuid.UUID,
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    result = await service.analyze_profile(db, profile_id, org_id, body.sample_texts)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post(
    "/{profile_id}/generate-sample",
    summary="Generate a sample text matching the profile",
    description="Generate sample text using the voice profile's style card as context.",
)
async def generate_sample(
    profile_id: uuid.UUID,
    body: GenerateSampleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate sample text using the voice profile's style card as LLM context."""
    org_id = current_user["org_id"]
    profile = await service.get_profile(db, profile_id, org_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.style_card is None:
        raise HTTPException(status_code=400, detail="Profile not analyzed yet")

    # Build system prompt from style card fields
    card = profile.style_card
    system_parts = [
        "You are a ghostwriter. Your task is to write text that precisely matches "
        "the following author's voice and style.",
        f"\nStyle summary: {card.summary}",
    ]
    if card.tone:
        system_parts.append(f"Tone: {card.tone}")
    if card.pacing:
        system_parts.append(f"Pacing: {card.pacing}")
    if card.vocabulary_level:
        system_parts.append(f"Vocabulary level: {card.vocabulary_level}")
    if card.sentence_style:
        system_parts.append(f"Sentence style: {card.sentence_style}")
    if card.paragraph_style:
        system_parts.append(f"Paragraph style: {card.paragraph_style}")
    if card.rhetorical_style:
        system_parts.append(f"Rhetorical style: {card.rhetorical_style}")
    if card.dialogue_style:
        system_parts.append(f"Dialogue style: {card.dialogue_style}")
    system_parts.append(
        f"\nWrite approximately {body.max_words} words. "
        "Stay faithful to the described voice. Do not add meta-commentary."
    )
    system_prompt = "\n".join(system_parts)

    # Call the LLM via the Anthropic provider
    try:
        provider = AnthropicProvider()
        request = LLMRequest(
            prompt=body.prompt,
            system_prompt=system_prompt,
            model_id=ModelID.CLAUDE_SONNET.value,
            max_tokens=body.max_words * 6,  # generous token budget (~1.5 tokens/word * 4x margin)
            temperature=0.7,
        )
        response = await provider.generate(request)

        if not response.succeeded:
            error_detail = response.metadata.get("error", "LLM generation failed")
            logger.error(
                "LLM generation failed for profile %s: %s", profile_id, error_detail
            )
            raise HTTPException(
                status_code=502,
                detail=f"Text generation failed: {error_detail}",
            )

        generated_text = response.content

    except HTTPException:
        raise
    except (ConnectionError, TimeoutError) as exc:
        logger.error("LLM network error for profile %s: %s", profile_id, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Text generation failed: {exc}",
        )
    except ValueError as exc:
        logger.error("LLM value error for profile %s: %s", profile_id, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Text generation failed: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during LLM generation for profile %s", profile_id)
        raise HTTPException(
            status_code=502,
            detail=f"Text generation failed: {exc}",
        )

    return {
        "profile_id": str(profile_id),
        "prompt": body.prompt,
        "generated_text": generated_text,
    }


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a profile",
    description="Soft-delete a style profile. The record is retained but hidden.",
)
async def delete_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    success = await service.delete_profile(db, profile_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return


@router.post(
    "/{profile_id}/conformity-check",
    response_model=ConformityCheckResult,
    summary="Check text conformity against a profile",
    description="Check how well a text matches the profile's voice fingerprint (0-100 score).",
)
async def conformity_check(
    profile_id: uuid.UUID,
    body: ConformityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check how well *text* matches the profile's voice fingerprint (0-100)."""
    org_id = current_user["org_id"]
    result = await service.conformity_check(db, profile_id, org_id, body.text)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found or not yet analyzed",
        )
    return result
