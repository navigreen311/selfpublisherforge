"""Storage service — wraps an S3-compatible client for presigned URLs, asset CRUD, etc."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.models.content import ContentAsset
from app.modules.storage.schemas import (
    AssetResponse,
    AssetStatus,
    AssetType,
    UploadResponse,
)
from app.modules.storage.validators import validate_file

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# S3 client helper
# ---------------------------------------------------------------------------

def _get_s3_client():
    """Return a boto3 S3 client configured for the current settings."""
    return boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


async def check_s3_connectivity() -> bool:
    """Preflight check: verify the configured S3 bucket is accessible.

    Returns True if the bucket responds to a HEAD request, False otherwise.
    Intended to be called during application startup (e.g. from main.py).
    """
    try:
        s3_client = _get_s3_client()
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        logger.info("S3 connectivity check passed for bucket '%s'", settings.S3_BUCKET)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        logger.error(
            "S3 connectivity check failed for bucket '%s': ClientError %s — %s",
            settings.S3_BUCKET,
            error_code,
            exc,
        )
        return False
    except BotoCoreError as exc:
        logger.error(
            "S3 connectivity check failed for bucket '%s': BotoCoreError — %s",
            settings.S3_BUCKET,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class StorageService:
    """High-level storage operations."""

    def __init__(self, db: AsyncSession, s3_client=None):
        self.db = db
        self.s3 = s3_client or _get_s3_client()
        self.bucket = settings.S3_BUCKET

    # -- Presigned upload ---------------------------------------------------

    async def create_presigned_upload(
        self,
        *,
        org_id: uuid.UUID,
        file_name: str,
        content_type: str,
        size: int,
        asset_type: AssetType,
    ) -> UploadResponse:
        """Validate the incoming file metadata, create an asset record, and
        return a presigned PUT URL the client can use to upload directly to S3.
        """
        # 1. Validate
        validate_file(
            file_name=file_name,
            content_type=content_type,
            size=size,
            asset_type=asset_type,
        )

        # 2. Build S3 key
        asset_id = uuid.uuid4()
        s3_key = self._build_s3_key(org_id, asset_type, asset_id, file_name)

        # 3. Persist asset record in PENDING state
        asset = ContentAsset(
            id=asset_id,
            org_id=org_id,
            file_name=file_name,
            content_type=content_type,
            size=size,
            asset_type=asset_type.value,
            status=AssetStatus.PENDING.value,
            s3_key=s3_key,
        )
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)

        # 4. Generate presigned URL
        expires_in = 3600
        upload_url = self.s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

        return UploadResponse(
            upload_url=upload_url,
            asset_id=asset_id,
            expires_in=expires_in,
        )

    # -- Complete upload ----------------------------------------------------

    async def complete_upload(
        self, *, asset_id: uuid.UUID, org_id: uuid.UUID
    ) -> AssetResponse:
        """Called after S3 upload finishes.

        1. Verify the object exists in S3.
        2. Transition status from PENDING -> UPLOADED.
        3. Trigger post-upload processing (metadata extraction, etc.).
        """
        asset = await self._get_asset_or_404(asset_id, org_id)

        if asset.status != AssetStatus.PENDING.value:
            raise AppException(
                status_code=409,
                code="INVALID_ASSET_STATE",
                message=f"Asset is in '{asset.status}' state, expected 'pending'.",
            )

        # Verify the object actually exists in S3
        try:
            head = self.s3.head_object(Bucket=self.bucket, Key=asset.s3_key)
        except ClientError:
            raise AppException(
                status_code=400,
                code="UPLOAD_NOT_FOUND",
                message="The file has not been uploaded to storage yet.",
            )

        # Back-fill the actual file size from S3 if available
        actual_size = head.get("ContentLength")
        if actual_size is not None:
            asset.size = actual_size

        # Transition: PENDING -> UPLOADED
        asset.status = AssetStatus.UPLOADED.value
        await self.db.flush()
        await self.db.refresh(asset)

        # Automatically trigger post-upload processing
        return await self.trigger_processing(
            asset_id=asset_id,
            org_id=org_id,
        )

    # -- List assets --------------------------------------------------------

    async def list_assets(
        self,
        *,
        org_id: uuid.UUID,
        asset_type: AssetType | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return paginated assets for the organisation."""
        query = (
            select(ContentAsset)
            .where(ContentAsset.org_id == org_id)
            .where(ContentAsset.deleted_at.is_(None))
            .order_by(ContentAsset.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(ContentAsset)
            .where(ContentAsset.org_id == org_id)
            .where(ContentAsset.deleted_at.is_(None))
        )

        if asset_type is not None:
            query = query.where(ContentAsset.asset_type == asset_type.value)
            count_query = count_query.where(ContentAsset.asset_type == asset_type.value)

        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
            except ValueError:
                raise AppException(
                    status_code=400,
                    code="INVALID_CURSOR",
                    message="Cursor value is not a valid ISO-8601 datetime.",
                )
            query = query.where(ContentAsset.created_at < cursor_dt)

        query = query.limit(limit + 1)  # fetch one extra for has_more

        result = await self.db.execute(query)
        rows = list(result.scalars().all())

        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = rows[-1].created_at.isoformat() if rows and has_more else None

        items = [self._to_response(r) for r in rows]

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total_count": total_count,
        }

    # -- Get single asset ---------------------------------------------------

    async def get_asset(
        self, *, asset_id: uuid.UUID, org_id: uuid.UUID
    ) -> AssetResponse:
        asset = await self._get_asset_or_404(asset_id, org_id)
        download_url = self._generate_download_url(asset.s3_key)
        return self._to_response(asset, download_url=download_url)

    # -- Soft-delete --------------------------------------------------------

    async def delete_asset(
        self, *, asset_id: uuid.UUID, org_id: uuid.UUID
    ) -> None:
        asset = await self._get_asset_or_404(asset_id, org_id)
        asset.status = AssetStatus.DELETED.value
        asset.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(asset)

    # -- Trigger processing -------------------------------------------------

    async def trigger_processing(
        self,
        *,
        asset_id: uuid.UUID,
        org_id: uuid.UUID,
        action: str = "auto",
        options: dict | None = None,
    ) -> AssetResponse:
        """Process an uploaded file: update status, extract metadata, mark completed.

        Lifecycle:  UPLOADED | READY  -->  PROCESSING  -->  READY
        If anything goes wrong during processing the status is set to FAILED.
        """
        asset = await self._get_asset_or_404(asset_id, org_id)

        if asset.status not in (AssetStatus.UPLOADED.value, AssetStatus.READY.value):
            raise AppException(
                status_code=409,
                code="INVALID_ASSET_STATE",
                message=f"Cannot process asset in '{asset.status}' state.",
            )

        # 1. Transition to PROCESSING
        asset.status = AssetStatus.PROCESSING.value
        await self.db.flush()

        try:
            # 2. Extract metadata based on content type
            metadata = self._extract_metadata(asset, action=action, options=options)

            # 3. Populate legacy / convenience columns from extracted metadata
            if asset.content_type and not asset.mime_type:
                asset.mime_type = asset.content_type
            if asset.size and not asset.file_size:
                asset.file_size = asset.size
            if asset.s3_key and not asset.file_url:
                asset.file_url = self._generate_download_url(asset.s3_key)

            # 4. Persist extracted metadata on the asset record
            asset.metadata_ = metadata

            # 5. Mark as READY (processing complete)
            asset.status = AssetStatus.READY.value
            await self.db.flush()
            await self.db.refresh(asset)

        except ClientError as exc:
            logger.error("S3 client error during asset processing for %s: %s", asset_id, exc)
            asset.status = AssetStatus.FAILED.value
            await self.db.flush()
            await self.db.refresh(asset)
            raise AppException(
                status_code=500,
                code="PROCESSING_FAILED",
                message="Asset processing failed due to a storage service error.",
            )
        except IOError as exc:
            logger.error("I/O error during asset processing for %s: %s", asset_id, exc)
            asset.status = AssetStatus.FAILED.value
            await self.db.flush()
            await self.db.refresh(asset)
            raise AppException(
                status_code=500,
                code="PROCESSING_FAILED",
                message="Asset processing failed due to an I/O error.",
            )

        return self._to_response(asset)

    # -- Metadata extraction ------------------------------------------------

    @staticmethod
    def _extract_metadata(
        asset: ContentAsset,
        *,
        action: str = "auto",
        options: dict | None = None,
    ) -> dict[str, Any]:
        """Derive metadata dict from the asset's content_type and file_name.

        This runs synchronously for now (cheap heuristics).  When heavier
        processing is needed (e.g. PDF page-count extraction, image dimension
        detection) this would dispatch to a Celery worker instead.
        """
        metadata: dict[str, Any] = {
            "action": action,
            "file_name": asset.file_name,
            "content_type": asset.content_type,
            "size": asset.size,
        }

        if options:
            metadata["options"] = options

        ct = asset.content_type or ""

        if ct.startswith("image/"):
            metadata["type"] = "image"
            metadata["category"] = "visual"
            # Could be extended with Pillow to extract width/height/dpi
        elif ct == "application/pdf":
            metadata["type"] = "document"
            metadata["category"] = "manuscript"
        elif ct in ("application/epub+zip",):
            metadata["type"] = "ebook"
            metadata["category"] = "manuscript"
        elif ct in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/rtf",
            "text/rtf",
            "text/plain",
        ):
            metadata["type"] = "document"
            metadata["category"] = "manuscript"
        elif ct == "application/x-mobipocket-ebook":
            metadata["type"] = "ebook"
            metadata["category"] = "export"
        else:
            metadata["type"] = "unknown"

        return metadata

    # -- Private helpers ----------------------------------------------------

    async def _get_asset_or_404(
        self, asset_id: uuid.UUID, org_id: uuid.UUID
    ) -> ContentAsset:
        result = await self.db.execute(
            select(ContentAsset)
            .where(ContentAsset.id == asset_id)
            .where(ContentAsset.org_id == org_id)
            .where(ContentAsset.deleted_at.is_(None))
        )
        asset = result.scalar_one_or_none()
        if asset is None:
            raise AppException(
                status_code=404,
                code="ASSET_NOT_FOUND",
                message="The requested asset does not exist.",
            )
        return asset

    @staticmethod
    def _build_s3_key(
        org_id: uuid.UUID,
        asset_type: AssetType,
        asset_id: uuid.UUID,
        file_name: str,
    ) -> str:
        """Construct a deterministic S3 object key.

        Pattern: ``orgs/<org_id>/<asset_type>/<asset_id>/<file_name>``
        """
        safe_name = file_name.replace(" ", "_")
        return f"orgs/{org_id}/{asset_type.value}/{asset_id}/{safe_name}"

    def _generate_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )

    @staticmethod
    def _to_response(
        asset: ContentAsset, *, download_url: str | None = None
    ) -> AssetResponse:
        return AssetResponse(
            id=asset.id,
            org_id=asset.org_id,
            file_name=asset.file_name,
            content_type=asset.content_type,
            size=asset.size,
            asset_type=AssetType(asset.asset_type),
            status=AssetStatus(asset.status),
            s3_key=asset.s3_key,
            download_url=download_url,
            metadata=asset.metadata_,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )
