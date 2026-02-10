"""FastAPI router for the Style Cloning Engine API endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status

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
# Helpers
# ---------------------------------------------------------------------------

def _get_org_id(x_org_id: str = Header(..., alias="X-Org-Id")) -> uuid.UUID:
    """Extract the org ID from the request header.

    In production this would be derived from the authenticated user/token.
    """
    try:
        return uuid.UUID(x_org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Org-Id header",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new style profile",
)
async def create_profile(
    body: CreateProfileRequest,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    """Upload sample manuscripts to create a new voice profile."""
    return await service.create_profile(org_id, body)


@router.get(
    "",
    response_model=ProfileListResponse,
    summary="List org style profiles",
)
async def list_profiles(
    org_id: uuid.UUID = Depends(_get_org_id),
):
    return await service.list_profiles(org_id)


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get profile details",
)
async def get_profile(
    profile_id: uuid.UUID,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    result = await service.get_profile(profile_id, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.get(
    "/{profile_id}/fingerprint",
    response_model=FingerprintResponse,
    summary="Get full voice fingerprint",
)
async def get_fingerprint(
    profile_id: uuid.UUID,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    result = await service.get_fingerprint(profile_id, org_id)
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
)
async def analyze_profile(
    profile_id: uuid.UUID,
    body: AnalyzeRequest,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    result = await service.analyze_profile(profile_id, org_id, body.sample_texts)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post(
    "/{profile_id}/generate-sample",
    summary="Generate a sample text matching the profile",
)
async def generate_sample(
    profile_id: uuid.UUID,
    body: GenerateSampleRequest,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    """Generate sample text using the voice profile.

    In production this calls the LLM orchestration layer with the style
    card injected as system context.  For now we return a placeholder.
    """
    profile = await service.get_profile(profile_id, org_id)
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
)
async def delete_profile(
    profile_id: uuid.UUID,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    success = await service.delete_profile(profile_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return None


@router.post(
    "/{profile_id}/conformity-check",
    response_model=ConformityCheckResult,
    summary="Check text conformity against a profile",
)
async def conformity_check(
    profile_id: uuid.UUID,
    body: ConformityCheckRequest,
    org_id: uuid.UUID = Depends(_get_org_id),
):
    """Check how well *text* matches the profile's voice fingerprint (0-100)."""
    result = await service.conformity_check(profile_id, org_id, body.text)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found or not yet analyzed",
        )
    return result
