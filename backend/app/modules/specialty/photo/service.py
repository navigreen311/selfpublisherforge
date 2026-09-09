"""Photo Integration service layer."""
from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.modules.specialty.models.enums import PhotoUsageType
from app.modules.specialty.models.photo import PhotoReference

logger = logging.getLogger(__name__)


async def list_photos(
    db: AsyncSession,
    org_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    book_type: str | None = None,
    book_id: UUID | None = None,
    usage_type: PhotoUsageType | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """List photo references with pagination and filters."""
    query = select(PhotoReference).where(
        PhotoReference.org_id == org_id,
        PhotoReference.is_active.is_(True),
    )

    if book_type:
        query = query.where(PhotoReference.book_type == book_type)
    if book_id:
        query = query.where(PhotoReference.book_id == book_id)
    if usage_type:
        query = query.where(PhotoReference.usage_type == usage_type.value)
    if search:
        query = query.where(PhotoReference.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(PhotoReference.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    photos = result.scalars().all()

    return {
        "items": [_photo_to_dict(p) for p in photos],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def upload_photo(
    db: AsyncSession,
    org_id: UUID,
    file: UploadFile,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Upload a new photo reference."""
    # In production: save file to S3/storage, generate thumbnail
    # Stub: create record with placeholder URLs
    photo_id = _uuid.uuid4()
    stub_url = f"/storage/photos/{photo_id}/{file.filename}"
    stub_thumb = f"/storage/photos/{photo_id}/thumb_{file.filename}"

    file_content = await file.read()
    file_size = len(file_content)

    usage = payload.get("usage_type", "style_reference")
    book_id_raw = payload.get("book_id")

    photo = PhotoReference(
        id=photo_id,
        org_id=org_id,
        name=payload.get("name", file.filename or "Untitled"),
        description=payload.get("description"),
        file_url=stub_url,
        thumbnail_url=stub_thumb,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        usage_type=usage,
        book_type=payload.get("book_type"),
        book_id=_uuid.UUID(book_id_raw) if book_id_raw else None,
        is_active=True,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return _photo_to_dict(photo)


async def get_photo(db: AsyncSession, org_id: UUID, photo_id: UUID) -> dict[str, Any]:
    """Get photo reference detail."""
    photo = await _get_or_404(db, org_id, photo_id)
    return _photo_to_dict(photo)


async def update_photo(
    db: AsyncSession, org_id: UUID, photo_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update photo reference metadata."""
    photo = await _get_or_404(db, org_id, photo_id)

    updatable = {"name", "description", "usage_type", "tags", "metadata_json", "book_type", "book_id"}
    for key, value in payload.items():
        if key in updatable:
            setattr(photo, key, value)

    await db.commit()
    await db.refresh(photo)
    return _photo_to_dict(photo)


async def delete_photo(db: AsyncSession, org_id: UUID, photo_id: UUID) -> bool:
    """Delete a photo reference (soft-delete)."""
    query = select(PhotoReference).where(
        PhotoReference.id == photo_id,
        PhotoReference.org_id == org_id,
        PhotoReference.is_active.is_(True),
    )
    result = await db.execute(query)
    photo = result.scalar_one_or_none()
    if not photo:
        return False

    photo.is_active = False
    await db.commit()
    return True


async def generate_with_references(
    db: AsyncSession,
    org_id: UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Generate an image using photo references as style/composition guides.

    payload: {"reference_ids": [...], "prompt": "...", "usage_types": [...]}
    Stub: return mock generated image URL.
    """
    reference_ids = payload.get("reference_ids", [])
    prompt = payload.get("prompt", "")
    usage_types = payload.get("usage_types", [])

    # Validate that referenced photos exist and belong to this org
    references = []
    for ref_id in reference_ids:
        uid = _uuid.UUID(str(ref_id)) if not isinstance(ref_id, UUID) else ref_id
        query = select(PhotoReference).where(
            PhotoReference.id == uid,
            PhotoReference.org_id == org_id,
            PhotoReference.is_active.is_(True),
        )
        result = await db.execute(query)
        photo = result.scalar_one_or_none()
        if photo:
            references.append(_photo_to_dict(photo))

    if not references:
        raise AppException("No valid photo references found for the given IDs.")

    # Stub: in production this would call an AI image generation API
    generated_id = _uuid.uuid4()
    return {
        "generated_id": str(generated_id),
        "generated_url": f"/storage/generated/{generated_id}.png",
        "prompt": prompt,
        "usage_types": usage_types,
        "reference_count": len(references),
        "references": references,
        "status": "completed",
        "message": "Stub: image generation would happen here in production.",
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_or_404(db: AsyncSession, org_id: UUID, photo_id: UUID) -> PhotoReference:
    query = select(PhotoReference).where(
        PhotoReference.id == photo_id,
        PhotoReference.org_id == org_id,
        PhotoReference.is_active.is_(True),
    )
    result = await db.execute(query)
    photo = result.scalar_one_or_none()
    if not photo:
        raise NotFoundError("PhotoReference", str(photo_id))
    return photo


def _photo_to_dict(photo: PhotoReference) -> dict[str, Any]:
    return {
        "id": str(photo.id),
        "name": photo.name,
        "description": photo.description,
        "file_url": photo.file_url,
        "thumbnail_url": photo.thumbnail_url,
        "file_size_bytes": photo.file_size_bytes,
        "mime_type": photo.mime_type,
        "width": photo.width,
        "height": photo.height,
        "usage_type": photo.usage_type if isinstance(photo.usage_type, str) else photo.usage_type.value,
        "tags": photo.tags,
        "metadata_json": photo.metadata_json,
        "book_type": photo.book_type,
        "book_id": str(photo.book_id) if photo.book_id else None,
        "is_active": photo.is_active,
        "created_at": photo.created_at.isoformat() if photo.created_at else None,
        "updated_at": photo.updated_at.isoformat() if photo.updated_at else None,
    }
