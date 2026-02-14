"""API router for the Audiobook module — Voice management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import service_voices
from app.modules.audiobook.schemas_extended import (
    VoiceCloneRequest,
    VoiceListResponse,
    VoicePreviewRequest,
    VoicePreviewResponse,
    VoiceResponse,
)

router = APIRouter()


# ── Voice endpoints ───────────────────────────────────────────────────────


@router.get(
    "/voices",
    response_model=VoiceListResponse,
    summary="List available voices",
    description="List all available TTS voices (system + organization custom voices).",
)
async def list_voices(
    provider: str | None = Query(None, description="Filter by provider"),
    voice_type: str | None = Query(None, description="Filter: narrator, character, custom"),
    gender: str | None = Query(None, description="Filter by gender"),
    language: str | None = Query(None, description="Filter by language code"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service_voices.list_voices(
        db,
        current_user["org_id"],
        provider=provider,
        voice_type=voice_type,
        gender=gender,
        language=language,
    )


@router.get(
    "/voices/{voice_id}",
    response_model=VoiceResponse,
    summary="Get voice details",
    description="Get detailed information about a specific TTS voice.",
)
async def get_voice(
    voice_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    voice = await service_voices.get_voice(db, voice_id, current_user["org_id"])
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found.",
        )
    return voice


@router.get(
    "/voices/{voice_id}/preview",
    response_model=VoicePreviewResponse,
    summary="Preview a voice",
    description="Get a preview audio URL for a voice with the given text.",
)
async def preview_voice(
    voice_id: UUID,
    text: str = Query("The quick brown fox jumps over the lazy dog.", max_length=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service_voices.preview_voice(db, voice_id, current_user["org_id"], text)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found.",
        )
    return result


@router.post(
    "/voices/clone",
    response_model=VoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a voice",
    description="Clone a voice from audio samples and register it as a custom voice.",
)
async def clone_voice(
    body: VoiceCloneRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service_voices.clone_voice(db, current_user["org_id"], body)


@router.delete(
    "/voices/{voice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom voice",
    description="Soft-delete a custom voice. System voices cannot be deleted.",
)
async def delete_voice(
    voice_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service_voices.delete_voice(db, voice_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found or is a system voice.",
        )


@router.post(
    "/voices/preview",
    response_model=VoicePreviewResponse,
    summary="Generate voice preview",
    description="Generate a preview audio clip for a voice with custom text.",
)
async def generate_voice_preview(
    body: VoicePreviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service_voices.preview_voice(
        db, body.voice_id, current_user["org_id"], body.text
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found.",
        )
    return result
