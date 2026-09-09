"""Knowledge Vault API router — all /api/v1/knowledge endpoints."""

from __future__ import annotations

import logging
import uuid as _uuid
from uuid import UUID

import boto3
from botocore.config import Config as BotoConfig
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.knowledge_vault.models import KnowledgeAttachment
from app.modules.knowledge_vault.schemas import (
    AttachmentResponse,
    CreateEntryRequest,
    ImportRequest,
    ImportResponse,
    ImportURLRequest,
    KnowledgeEntryResponse,
    SearchRequest,
    SearchResult,
    SuggestionsResponse,
    SummarizeResponse,
    TagListResponse,
    UpdateEntryRequest,
)
from app.modules.knowledge_vault.service import KnowledgeService

logger = logging.getLogger(__name__)
_settings = get_settings()

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db=db)


def _org_id(current_user: dict) -> UUID:
    return current_user["org_id"]


# ── Full-text search ─────────────────────────────────────────────
# NOTE: Fixed-path routes (/search, /import, /tags, /suggestions) MUST be
# registered before the parameterised /{entry_id} routes.  FastAPI matches
# top-to-bottom, so a GET /tags would otherwise be captured by
# GET /{entry_id} and fail UUID validation with a 422.


@router.post(
    "/search",
    response_model=SearchResult,
    summary="Full-text search via Elasticsearch",
    description="Search knowledge entries using full-text search with optional tag and source filters.",
)
async def search_entries(
    payload: SearchRequest,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    result = await service.full_text_search(
        org_id=_org_id(current_user),
        query=payload.query,
        tags=payload.tags or None,
        source_type=payload.source_type,
        limit=payload.limit,
        offset=payload.offset,
    )
    return SearchResult(
        hits=result["hits"],
        total=result["total"],
        query=payload.query,
    )


# ── Import ───────────────────────────────────────────────────────


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import from URL or file with AI extraction",
    description="Import a knowledge entry from a URL or uploaded file with optional AI fact extraction.",
)
async def import_entry(
    payload: ImportRequest,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    try:
        entry = await service.import_entry(
            org_id=_org_id(current_user),
            url=payload.url,
            file_name=payload.file_name,
            file_content_base64=payload.file_content_base64,
            extract_facts=payload.extract_facts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ImportResponse(
        entry_id=entry.id,
        title=entry.title,
        content_preview=entry.content[:300] if entry.content else "",
        tags=entry.tags or [],
        source_type=entry.source_type,
    )


# ── Import from URL (simplified) ─────────────────────────────────


@router.post(
    "/import-url",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a web article as a knowledge entry",
    description="Fetch a URL, extract its text content (stripping HTML), and create a knowledge entry.",
)
async def import_from_url(
    body: ImportURLRequest,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    """Import a web article as a knowledge entry."""
    try:
        entry = await service.import_entry(
            org_id=_org_id(current_user),
            url=body.url,
            extract_facts=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {exc}") from exc

    return ImportResponse(
        entry_id=entry.id,
        title=entry.title,
        content_preview=entry.content[:300] if entry.content else "",
        tags=entry.tags or [],
        source_type=entry.source_type,
    )


# ── Tags ─────────────────────────────────────────────────────────


@router.get(
    "/tags",
    response_model=TagListResponse,
    summary="List all tags",
    description="List all unique tags used across the organization's knowledge entries.",
)
async def list_tags(
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    return await service.get_all_tags(_org_id(current_user))


# ── AI Suggestions ───────────────────────────────────────────────


@router.get(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="AI-suggested research topics",
    description="Get AI-suggested research topics based on existing knowledge entries.",
)
async def get_suggestions(
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    suggestions = await service.get_suggestions(_org_id(current_user))
    return SuggestionsResponse(suggestions=suggestions)


# ── Create ───────────────────────────────────────────────────────


@router.post(
    "",
    response_model=KnowledgeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a knowledge entry",
    description="Create a new knowledge entry with title, content, and tags.",
)
async def create_entry(
    payload: CreateEntryRequest,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    entry = await service.create_entry(_org_id(current_user), payload)
    return _entry_response(entry)


# ── List (paginated, filterable) ─────────────────────────────────


@router.get(
    "",
    response_model=PaginatedResponse[KnowledgeEntryResponse],
    summary="List knowledge entries",
    description="List knowledge entries with pagination and optional tag/source filters.",
)
async def list_entries(
    tag: list[str] | None = Query(default=None),
    source_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    result = await service.list_entries(
        _org_id(current_user),
        tags=tag,
        source_type=source_type,
        category=category,
        cursor=cursor,
        limit=limit,
    )
    return {
        "items": [_entry_response(e) for e in result["items"]],
        "next_cursor": result["next_cursor"],
        "has_more": result["has_more"],
        "total_count": result["total_count"],
    }


# ── Get detail ───────────────────────────────────────────────────


@router.get(
    "/{entry_id}",
    response_model=KnowledgeEntryResponse,
    summary="Get knowledge entry detail",
    description="Get full details of a specific knowledge entry by ID.",
)
async def get_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    entry = await service.get_entry(_org_id(current_user), entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return _entry_response(entry)


# ── Update ───────────────────────────────────────────────────────


@router.put(
    "/{entry_id}",
    response_model=KnowledgeEntryResponse,
    summary="Update a knowledge entry",
    description="Update the title, content, or tags of a knowledge entry.",
)
async def update_entry(
    entry_id: UUID,
    payload: UpdateEntryRequest,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    entry = await service.update_entry(_org_id(current_user), entry_id, payload)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return _entry_response(entry)


# ── Delete (soft) ────────────────────────────────────────────────


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a knowledge entry",
    description="Soft-delete a knowledge entry. The record is retained but hidden.",
)
async def delete_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    deleted = await service.delete_entry(_org_id(current_user), entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")


# ── Summarize ────────────────────────────────────────────────────


@router.post(
    "/{entry_id}/summarize",
    response_model=SummarizeResponse,
    summary="AI-summarize a knowledge entry",
    description="Generate an AI summary of a knowledge entry's content.",
)
async def summarize_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_service),
):
    result = await service.summarize_entry(_org_id(current_user), entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return result


# ── Attachments ──────────────────────────────────────────────────


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=_settings.S3_REGION,
        aws_access_key_id=_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=_settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


@router.post(
    "/{entry_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an attachment",
    description="Upload a file attachment to a knowledge entry.",
)
async def upload_attachment(
    entry_id: UUID,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file attachment to a knowledge entry."""
    # Verify the parent entry exists and belongs to the user's org
    service = KnowledgeService(db=db)
    entry = await service.get_entry(_org_id(current_user), entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    # Read the file content
    content = await file.read()
    file_size = len(content)
    mime_type = file.content_type or "application/octet-stream"
    file_name = file.filename or "untitled"

    # Build S3 key and upload
    attachment_id = _uuid.uuid4()
    org_id = _org_id(current_user)
    safe_name = file_name.replace(" ", "_")
    s3_key = f"orgs/{org_id}/knowledge/{entry_id}/attachments/{attachment_id}/{safe_name}"

    s3 = _get_s3_client()
    try:
        s3.put_object(
            Bucket=_settings.S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=mime_type,
        )
    except Exception as exc:
        logger.exception("Failed to upload attachment to S3")
        raise HTTPException(status_code=502, detail="Failed to upload file to storage") from exc

    # Generate a presigned download URL
    file_url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": _settings.S3_BUCKET, "Key": s3_key},
        ExpiresIn=3600,
    )

    # Persist the attachment record
    attachment = KnowledgeAttachment(
        id=attachment_id,
        entry_id=entry_id,
        file_name=file_name,
        file_url=file_url,
        file_size=file_size,
        mime_type=mime_type,
        s3_key=s3_key,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)

    return AttachmentResponse(
        id=attachment.id,
        entry_id=attachment.entry_id,
        file_name=attachment.file_name,
        file_url=attachment.file_url,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        created_at=attachment.created_at,
    )


@router.get(
    "/{entry_id}/attachments",
    response_model=list[AttachmentResponse],
    summary="List attachments",
    description="List all file attachments for a knowledge entry.",
)
async def list_attachments(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all file attachments for a knowledge entry."""
    # Verify the parent entry exists and belongs to the user's org
    service = KnowledgeService(db=db)
    entry = await service.get_entry(_org_id(current_user), entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    result = await db.execute(
        select(KnowledgeAttachment)
        .where(
            KnowledgeAttachment.entry_id == entry_id,
            KnowledgeAttachment.deleted_at.is_(None),
        )
        .order_by(KnowledgeAttachment.created_at.desc())
    )
    attachments = result.scalars().all()

    return [
        AttachmentResponse(
            id=a.id,
            entry_id=a.entry_id,
            file_name=a.file_name,
            file_url=a.file_url,
            file_size=a.file_size,
            mime_type=a.mime_type,
            created_at=a.created_at,
        )
        for a in attachments
    ]


@router.delete(
    "/{entry_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an attachment",
    description="Soft-delete a file attachment from a knowledge entry.",
)
async def delete_attachment(
    entry_id: UUID,
    attachment_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a file attachment from a knowledge entry."""
    # Verify the parent entry exists and belongs to the user's org
    service = KnowledgeService(db=db)
    entry = await service.get_entry(_org_id(current_user), entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    result = await db.execute(
        select(KnowledgeAttachment).where(
            KnowledgeAttachment.id == attachment_id,
            KnowledgeAttachment.entry_id == entry_id,
            KnowledgeAttachment.deleted_at.is_(None),
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    from datetime import UTC, datetime

    attachment.deleted_at = datetime.now(UTC)
    await db.flush()


# ── Helpers ──────────────────────────────────────────────────────


def _entry_response(entry) -> dict:
    """Convert a KnowledgeEntry ORM instance to a response dict."""
    return {
        "id": entry.id,
        "org_id": entry.org_id,
        "title": entry.title,
        "content": entry.content,
        "source_url": entry.source_url,
        "source_type": entry.source_type,
        "tags": entry.tags or [],
        "credibility_score": entry.credibility_score,
        "category": entry.category,
        "project_id": entry.project_id,
        "metadata": entry.metadata_ or {},
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "deleted_at": entry.deleted_at,
    }
