"""Unit tests for the storage service — presigned URL generation, file validation, size limits."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

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


# ===========================================================================
# Service — trigger_processing
# ===========================================================================

def _make_fake_asset(
    *,
    asset_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    status: str = "uploaded",
    content_type: str = "application/pdf",
    file_name: str = "book.pdf",
    size: int = 2048,
    s3_key: str | None = None,
    asset_type: str = "manuscript",
) -> MagicMock:
    """Return a MagicMock that behaves like a ContentAsset row."""
    asset = MagicMock()
    asset.id = asset_id or uuid.uuid4()
    asset.org_id = org_id or ORG_ID
    asset.status = status
    asset.content_type = content_type
    asset.file_name = file_name
    asset.size = size
    asset.s3_key = s3_key or f"orgs/{ORG_ID}/manuscript/{asset.id}/{file_name}"
    asset.asset_type = asset_type
    asset.metadata_ = None
    asset.mime_type = None
    asset.file_size = None
    asset.file_url = None
    asset.created_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    asset.updated_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    asset.deleted_at = None
    return asset


class TestTriggerProcessing:
    """Tests for StorageService.trigger_processing."""

    @pytest.mark.asyncio
    async def test_updates_status_to_processing_then_ready(self):
        """trigger_processing should transition status from 'uploaded' to 'processing' then 'ready'."""
        asset = _make_fake_asset(status=AssetStatus.UPLOADED.value)
        db = _fake_db()

        # _get_asset_or_404 returns our fake asset
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        # Track status transitions
        status_transitions = []
        original_flush = db.flush

        async def tracking_flush():
            status_transitions.append(asset.status)
            await original_flush()

        db.flush = tracking_flush

        result = await svc.trigger_processing(
            asset_id=asset.id, org_id=ORG_ID
        )

        # Should have first transitioned to PROCESSING, then to READY
        assert AssetStatus.PROCESSING.value in status_transitions
        assert asset.status == AssetStatus.READY.value
        assert result is not None

    @pytest.mark.asyncio
    async def test_asset_not_found_raises_404(self):
        """trigger_processing for a non-existent asset should raise 404."""
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.trigger_processing(
                asset_id=uuid.uuid4(), org_id=ORG_ID
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ASSET_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_invalid_state_raises_409(self):
        """trigger_processing on an asset in 'pending' state should raise 409."""
        asset = _make_fake_asset(status=AssetStatus.PENDING.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.trigger_processing(
                asset_id=asset.id, org_id=ORG_ID
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "INVALID_ASSET_STATE"

    @pytest.mark.asyncio
    async def test_processing_failure_sets_status_to_failed(self):
        """If _extract_metadata raises, status should be set to 'failed'."""
        asset = _make_fake_asset(status=AssetStatus.UPLOADED.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        # Force _extract_metadata to raise
        with patch.object(
            StorageService,
            "_extract_metadata",
            side_effect=RuntimeError("metadata extraction boom"),
        ):
            with pytest.raises(AppException) as exc_info:
                await svc.trigger_processing(
                    asset_id=asset.id, org_id=ORG_ID
                )
            assert exc_info.value.status_code == 500
            assert exc_info.value.code == "PROCESSING_FAILED"
            assert asset.status == AssetStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_extract_metadata_populates_asset_fields(self):
        """trigger_processing should populate metadata and legacy columns."""
        asset = _make_fake_asset(
            status=AssetStatus.UPLOADED.value,
            content_type="image/png",
            file_name="cover.png",
        )
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        await svc.trigger_processing(asset_id=asset.id, org_id=ORG_ID)

        # Metadata should be populated with image-type classification
        assert asset.metadata_ is not None
        assert asset.metadata_["type"] == "image"
        assert asset.metadata_["category"] == "visual"
        # Legacy columns should be back-filled
        assert asset.mime_type == "image/png"
        assert asset.file_size == asset.size


# ===========================================================================
# Service — complete_upload
# ===========================================================================


class TestCompleteUpload:
    """Tests for StorageService.complete_upload."""

    @pytest.mark.asyncio
    async def test_complete_upload_success(self):
        """complete_upload should transition PENDING -> UPLOADED -> (processing)."""
        asset = _make_fake_asset(status=AssetStatus.PENDING.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        # head_object returns successfully (file exists in S3)
        s3.head_object.return_value = {"ContentLength": 4096}

        svc = StorageService(db=db, s3_client=s3)

        result = await svc.complete_upload(
            asset_id=asset.id, org_id=ORG_ID
        )

        # After complete_upload, asset goes through UPLOADED -> trigger_processing -> READY
        assert asset.status == AssetStatus.READY.value
        s3.head_object.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_complete_upload_backfills_size_from_s3(self):
        """complete_upload should update size from S3 ContentLength."""
        asset = _make_fake_asset(status=AssetStatus.PENDING.value, size=0)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        s3.head_object.return_value = {"ContentLength": 9999}

        svc = StorageService(db=db, s3_client=s3)
        await svc.complete_upload(asset_id=asset.id, org_id=ORG_ID)

        assert asset.size == 9999

    @pytest.mark.asyncio
    async def test_complete_upload_wrong_state_raises_409(self):
        """complete_upload on an already-uploaded asset should raise 409."""
        asset = _make_fake_asset(status=AssetStatus.UPLOADED.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.complete_upload(asset_id=asset.id, org_id=ORG_ID)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "INVALID_ASSET_STATE"

    @pytest.mark.asyncio
    async def test_complete_upload_s3_missing_raises_400(self):
        """complete_upload when S3 object is missing should raise 400."""
        asset = _make_fake_asset(status=AssetStatus.PENDING.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )

        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.complete_upload(asset_id=asset.id, org_id=ORG_ID)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "UPLOAD_NOT_FOUND"


# ===========================================================================
# Service — soft-delete
# ===========================================================================


class TestDeleteAsset:
    """Tests for StorageService.delete_asset."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_status_and_deleted_at(self):
        """delete_asset should set status to 'deleted' and populate deleted_at."""
        asset = _make_fake_asset(status=AssetStatus.READY.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        await svc.delete_asset(asset_id=asset.id, org_id=ORG_ID)

        assert asset.status == AssetStatus.DELETED.value
        assert asset.deleted_at is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_404(self):
        """delete_asset for a non-existent asset should raise 404."""
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.delete_asset(asset_id=uuid.uuid4(), org_id=ORG_ID)
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ASSET_NOT_FOUND"


# ===========================================================================
# Service — access control (org_id isolation)
# ===========================================================================


class TestAccessControl:
    """Tests to verify that asset lookups enforce org_id checks."""

    @pytest.mark.asyncio
    async def test_get_asset_wrong_org_id_raises_404(self):
        """get_asset should raise 404 when org_id does not match."""
        db = _fake_db()
        mock_result = MagicMock()
        # The query filters by org_id, so it returns None for wrong org
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        wrong_org_id = uuid.uuid4()
        with pytest.raises(AppException) as exc_info:
            await svc.get_asset(
                asset_id=uuid.uuid4(), org_id=wrong_org_id
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ASSET_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_trigger_processing_wrong_org_raises_404(self):
        """trigger_processing should raise 404 when org_id does not match."""
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        svc = StorageService(db=db, s3_client=s3)

        with pytest.raises(AppException) as exc_info:
            await svc.trigger_processing(
                asset_id=uuid.uuid4(), org_id=uuid.uuid4()
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ASSET_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_asset_returns_download_url(self):
        """get_asset should return a response that includes a download_url."""
        asset = _make_fake_asset(status=AssetStatus.READY.value)
        db = _fake_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute.return_value = mock_result

        s3 = _fake_s3_client()
        s3.generate_presigned_url.return_value = "https://s3.example.com/presigned-get"
        svc = StorageService(db=db, s3_client=s3)

        result = await svc.get_asset(asset_id=asset.id, org_id=ORG_ID)

        assert result.download_url == "https://s3.example.com/presigned-get"
        s3.generate_presigned_url.assert_called_once()


# ===========================================================================
# Metadata extraction
# ===========================================================================


class TestExtractMetadata:
    """Tests for StorageService._extract_metadata."""

    def test_image_metadata(self):
        asset = _make_fake_asset(content_type="image/jpeg", file_name="photo.jpg")
        metadata = StorageService._extract_metadata(asset)
        assert metadata["type"] == "image"
        assert metadata["category"] == "visual"
        assert metadata["file_name"] == "photo.jpg"

    def test_pdf_metadata(self):
        asset = _make_fake_asset(content_type="application/pdf", file_name="book.pdf")
        metadata = StorageService._extract_metadata(asset)
        assert metadata["type"] == "document"
        assert metadata["category"] == "manuscript"

    def test_epub_metadata(self):
        asset = _make_fake_asset(content_type="application/epub+zip", file_name="book.epub")
        metadata = StorageService._extract_metadata(asset)
        assert metadata["type"] == "ebook"
        assert metadata["category"] == "manuscript"

    def test_mobi_metadata(self):
        asset = _make_fake_asset(content_type="application/x-mobipocket-ebook", file_name="book.mobi")
        metadata = StorageService._extract_metadata(asset)
        assert metadata["type"] == "ebook"
        assert metadata["category"] == "export"

    def test_unknown_content_type(self):
        asset = _make_fake_asset(content_type="application/octet-stream", file_name="data.bin")
        metadata = StorageService._extract_metadata(asset)
        assert metadata["type"] == "unknown"

    def test_options_passed_through(self):
        asset = _make_fake_asset(content_type="image/png", file_name="img.png")
        metadata = StorageService._extract_metadata(
            asset, action="resize", options={"width": 800}
        )
        assert metadata["action"] == "resize"
        assert metadata["options"] == {"width": 800}
