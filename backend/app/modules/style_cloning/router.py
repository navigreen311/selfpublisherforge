"""FastAPI router for the Style Cloning Engine API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
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
)

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
    """Generate sample text using the voice profile.

    In production this calls the LLM orchestration layer with the style
    card injected as system context.  For now we return a placeholder.
    """
    org_id = current_user["org_id"]
    profile = await service.get_profile(db, profile_id, org_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.style_card is None:
        raise HTTPException(status_code=400, detail="Profile not analyzed yet")
    return {
        "profile_id": str(profile_id),
        "prompt": body.prompt,
        "generated_text": (
            f"[Sample generation placeholder — would use LLM with style card: "
            f"{profile.style_card.summary[:120]}...]"
        ),
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
    return None


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
