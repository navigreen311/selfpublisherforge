"""Integration tests for storage API endpoints — uses mocked S3 and in-memory SQLite."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.modules.storage.schemas import AssetStatus, AssetType
from app.modules.storage.service import ContentAsset


# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them afterwards."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Mock S3 + auth helpers
# ---------------------------------------------------------------------------

FAKE_USER = {
    "user_id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    "org_id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    "role": "admin",
}


def _mock_s3_client() -> MagicMock:
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://s3.example.com/presigned"
    client.head_object.return_value = {"ContentLength": 1024}
    return client


# ---------------------------------------------------------------------------
# App fixture with overridden deps
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Yield an async test client with DB and auth overridden."""
    from app.main import create_app
    from app.core.dependencies import get_current_user

    app = create_app()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper to patch S3 client inside the service
# ---------------------------------------------------------------------------

def _patch_s3():
    return patch(
        "app.modules.storage.service._get_s3_client",
        return_value=_mock_s3_client(),
    )


# ===========================================================================
# Tests
# ===========================================================================


class TestUploadFlow:
    """Test the presigned upload + complete flow."""

    @pytest.mark.asyncio
    async def test_request_upload_returns_presigned_url(self, client: AsyncClient):
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "manuscript.pdf",
                    "content_type": "application/pdf",
                    "size": 2048,
                    "asset_type": "manuscript",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert "upload_url" in data
        assert "asset_id" in data
        assert data["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_complete_upload_marks_uploaded(self, client: AsyncClient):
        with _patch_s3():
            # Step 1: request upload
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "manuscript.pdf",
                    "content_type": "application/pdf",
                    "size": 2048,
                    "asset_type": "manuscript",
                },
            )
            asset_id = resp.json()["asset_id"]

            # Step 2: complete upload
            resp2 = await client.post(
                "/api/v1/storage/upload/complete",
                json={"asset_id": asset_id},
            )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["status"] == "uploaded"
        assert data["id"] == asset_id

    @pytest.mark.asyncio
    async def test_upload_rejects_invalid_mime(self, client: AsyncClient):
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "hack.exe",
                    "content_type": "application/x-msdownload",
                    "size": 1024,
                    "asset_type": "manuscript",
                },
            )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_CONTENT_TYPE"

    @pytest.mark.asyncio
    async def test_upload_rejects_oversized(self, client: AsyncClient):
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "huge.pdf",
                    "content_type": "application/pdf",
                    "size": 60 * 1024 * 1024,  # 60 MB > 50 MB limit
                    "asset_type": "manuscript",
                },
            )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FILE_TOO_LARGE"


class TestAssetCRUD:
    """Test listing, fetching, and deleting assets."""

    async def _create_asset(self, client: AsyncClient) -> str:
        """Helper: create an asset via the upload flow and return its ID."""
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "test.pdf",
                    "content_type": "application/pdf",
                    "size": 1024,
                    "asset_type": "manuscript",
                },
            )
            asset_id = resp.json()["asset_id"]
            await client.post(
                "/api/v1/storage/upload/complete",
                json={"asset_id": asset_id},
            )
        return asset_id

    @pytest.mark.asyncio
    async def test_list_assets_empty(self, client: AsyncClient):
        with _patch_s3():
            resp = await client.get("/api/v1/storage/assets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_assets_returns_created(self, client: AsyncClient):
        with _patch_s3():
            await self._create_asset(client)
            resp = await client.get("/api/v1/storage/assets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["file_name"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_list_assets_filter_by_type(self, client: AsyncClient):
        with _patch_s3():
            await self._create_asset(client)
            # Filter for images — should return empty
            resp = await client.get("/api/v1/storage/assets?asset_type=image")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_asset_detail(self, client: AsyncClient):
        with _patch_s3():
            asset_id = await self._create_asset(client)
            resp = await client.get(f"/api/v1/storage/assets/{asset_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == asset_id
        assert data["download_url"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_asset_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        with _patch_s3():
            resp = await client.get(f"/api/v1/storage/assets/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_asset(self, client: AsyncClient):
        with _patch_s3():
            asset_id = await self._create_asset(client)
            resp = await client.delete(f"/api/v1/storage/assets/{asset_id}")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

        # Confirm the asset no longer appears in listing
        with _patch_s3():
            list_resp = await client.get("/api/v1/storage/assets")
        assert len(list_resp.json()["items"]) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_asset_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        with _patch_s3():
            resp = await client.delete(f"/api/v1/storage/assets/{fake_id}")
        assert resp.status_code == 404


class TestProcessing:
    """Test the processing trigger endpoint."""

    async def _create_uploaded_asset(self, client: AsyncClient) -> str:
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "cover.jpg",
                    "content_type": "image/jpeg",
                    "size": 5_000_000,
                    "asset_type": "image",
                },
            )
            asset_id = resp.json()["asset_id"]
            await client.post(
                "/api/v1/storage/upload/complete",
                json={"asset_id": asset_id},
            )
        return asset_id

    @pytest.mark.asyncio
    async def test_trigger_processing(self, client: AsyncClient):
        with _patch_s3():
            asset_id = await self._create_uploaded_asset(client)
            resp = await client.post(
                f"/api/v1/storage/assets/{asset_id}/process",
                json={"action": "resize"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processing"

    @pytest.mark.asyncio
    async def test_processing_on_pending_asset_fails(self, client: AsyncClient):
        """Cannot process an asset that has not been fully uploaded."""
        with _patch_s3():
            resp = await client.post(
                "/api/v1/storage/upload",
                json={
                    "file_name": "cover.jpg",
                    "content_type": "image/jpeg",
                    "size": 5_000_000,
                    "asset_type": "image",
                },
            )
            asset_id = resp.json()["asset_id"]

            # Try to process without completing upload
            resp2 = await client.post(
                f"/api/v1/storage/assets/{asset_id}/process",
                json={"action": "resize"},
            )
        assert resp2.status_code == 409
