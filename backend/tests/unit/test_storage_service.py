"""Unit tests for the storage service — presigned URL generation, file validation, size limits."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.modules.storage.schemas import AssetStatus, AssetType
from app.modules.storage.service import StorageService
from app.modules.storage.validators import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    validate_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fake_s3_client() -> MagicMock:
    """Return a mock boto3 S3 client."""
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://s3.example.com/presigned-put"
    client.head_object.return_value = {"ContentLength": 1024}
    return client


def _fake_db() -> AsyncMock:
    """Return a mock AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


ORG_ID = uuid.uuid4()


# ===========================================================================
# Validator tests
# ===========================================================================

class TestValidateFile:
    """Tests for the validate_file helper."""

    def test_valid_manuscript_pdf(self):
        """A valid PDF manuscript should pass."""
        validate_file(
            file_name="my_book.pdf",
            content_type="application/pdf",
            size=1024,
            asset_type=AssetType.MANUSCRIPT,
        )

    def test_valid_image_jpeg(self):
        """A valid JPEG image should pass."""
        validate_file(
            file_name="photo.jpg",
            content_type="image/jpeg",
            size=5 * 1024 * 1024,
            asset_type=AssetType.IMAGE,
        )

    def test_invalid_content_type_raises(self):
        """An unsupported MIME type should raise AppException."""
        with pytest.raises(AppException) as exc_info:
            validate_file(
                file_name="hack.exe",
                content_type="application/x-msdownload",
                size=1024,
                asset_type=AssetType.MANUSCRIPT,
            )
        assert exc_info.value.code == "INVALID_CONTENT_TYPE"
        assert exc_info.value.status_code == 400

    def test_image_mime_not_allowed_for_manuscript(self):
        """image/jpeg is valid for IMAGE but not MANUSCRIPT."""
        with pytest.raises(AppException) as exc_info:
            validate_file(
                file_name="photo.jpg",
                content_type="image/jpeg",
                size=1024,
                asset_type=AssetType.MANUSCRIPT,
            )
        assert exc_info.value.code == "INVALID_CONTENT_TYPE"

    def test_file_too_large_manuscript(self):
        """A manuscript exceeding 50 MB should be rejected."""
        over_limit = MAX_FILE_SIZE[AssetType.MANUSCRIPT] + 1
        with pytest.raises(AppException) as exc_info:
            validate_file(
                file_name="big_book.pdf",
                content_type="application/pdf",
                size=over_limit,
                asset_type=AssetType.MANUSCRIPT,
            )
        assert exc_info.value.code == "FILE_TOO_LARGE"
        assert exc_info.value.status_code == 400

    def test_file_too_large_image(self):
        """An image exceeding 20 MB should be rejected."""
        over_limit = MAX_FILE_SIZE[AssetType.IMAGE] + 1
        with pytest.raises(AppException) as exc_info:
            validate_file(
                file_name="huge.png",
                content_type="image/png",
                size=over_limit,
                asset_type=AssetType.IMAGE,
            )
        assert exc_info.value.code == "FILE_TOO_LARGE"

    def test_file_at_exact_limit_passes(self):
        """A file exactly at the size limit should pass."""
        exact_limit = MAX_FILE_SIZE[AssetType.MANUSCRIPT]
        validate_file(
            file_name="at_limit.pdf",
            content_type="application/pdf",
            size=exact_limit,
            asset_type=AssetType.MANUSCRIPT,
        )

    def test_cover_svg_not_allowed(self):
        """SVG is allowed for IMAGE but not COVER."""
        with pytest.raises(AppException) as exc_info:
            validate_file(
                file_name="cover.svg",
                content_type="image/svg+xml",
                size=1024,
                asset_type=AssetType.COVER,
            )
        assert exc_info.value.code == "INVALID_CONTENT_TYPE"

    def test_export_mobi_allowed(self):
        """MOBI should be allowed for EXPORT."""
        validate_file(
            file_name="output.mobi",
            content_type="application/x-mobipocket-ebook",
            size=1024,
            asset_type=AssetType.EXPORT,
        )

    def test_all_asset_types_have_size_limits(self):
        """Every AssetType enum value must have a size limit defined."""
        for at in AssetType:
            assert at in MAX_FILE_SIZE, f"Missing size limit for {at.value}"

    def test_all_asset_types_have_mime_whitelist(self):
        """Every AssetType enum value must have an allowed-MIME set."""
        for at in AssetType:
            assert at in ALLOWED_MIME_TYPES, f"Missing MIME whitelist for {at.value}"
            assert len(ALLOWED_MIME_TYPES[at]) > 0


# ===========================================================================
# Service — presigned upload
# ===========================================================================

class TestPresignedUpload:
    """Tests for StorageService.create_presigned_upload."""

    @pytest.mark.asyncio
    async def test_creates_presigned_url(self):
        db = _fake_db()
        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        resp = await svc.create_presigned_upload(
            org_id=ORG_ID,
            file_name="chapter1.pdf",
            content_type="application/pdf",
            size=2048,
            asset_type=AssetType.MANUSCRIPT,
        )

        assert resp.upload_url == "https://s3.example.com/presigned-put"
        assert resp.asset_id is not None
        assert resp.expires_in == 3600
        s3.generate_presigned_url.assert_called_once()
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_invalid_mime(self):
        db = _fake_db()
        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.create_presigned_upload(
                org_id=ORG_ID,
                file_name="virus.exe",
                content_type="application/x-msdownload",
                size=1024,
                asset_type=AssetType.MANUSCRIPT,
            )
        assert exc_info.value.code == "INVALID_CONTENT_TYPE"
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        db = _fake_db()
        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.create_presigned_upload(
                org_id=ORG_ID,
                file_name="huge.pdf",
                content_type="application/pdf",
                size=MAX_FILE_SIZE[AssetType.MANUSCRIPT] + 1,
                asset_type=AssetType.MANUSCRIPT,
            )
        assert exc_info.value.code == "FILE_TOO_LARGE"
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_key_structure(self):
        db = _fake_db()
        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        resp = await svc.create_presigned_upload(
            org_id=ORG_ID,
            file_name="my book.pdf",
            content_type="application/pdf",
            size=2048,
            asset_type=AssetType.MANUSCRIPT,
        )

        # Inspect the S3 key used in the presigned URL call
        call_kwargs = s3.generate_presigned_url.call_args
        s3_key = call_kwargs.kwargs.get("Params", call_kwargs[1]["Params"])["Key"]
        assert str(ORG_ID) in s3_key
        assert "manuscript" in s3_key
        assert "my_book.pdf" in s3_key  # spaces replaced with underscores


# ===========================================================================
# Service — S3 key builder
# ===========================================================================

class TestS3KeyBuilder:
    def test_key_format(self):
        asset_id = uuid.uuid4()
        key = StorageService._build_s3_key(ORG_ID, AssetType.IMAGE, asset_id, "photo.png")
        assert key == f"orgs/{ORG_ID}/image/{asset_id}/photo.png"

    def test_spaces_replaced(self):
        asset_id = uuid.uuid4()
        key = StorageService._build_s3_key(ORG_ID, AssetType.COVER, asset_id, "my cover art.jpg")
        assert " " not in key
        assert "my_cover_art.jpg" in key
