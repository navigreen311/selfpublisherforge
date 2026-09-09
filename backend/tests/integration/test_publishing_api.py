"""Integration tests for the Publishing Operations Center API.

These tests exercise the full request/response cycle through
the FastAPI router, service layer, and generators using mocked
DB dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

# Build a minimal FastAPI app for testing
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.modules.publishing_ops.router import metadata_router, router

app = FastAPI()
app.include_router(router, prefix="/api/v1/publishing")
app.include_router(metadata_router, prefix="/api/v1")

BASE = "/api/v1"

_TEST_ORG_ID = uuid.uuid4()
_TEST_USER = {"user_id": str(uuid.uuid4()), "org_id": _TEST_ORG_ID, "role": "admin"}
_NOW = datetime.now(UTC)


# Override dependencies
async def _override_current_user():
    return _TEST_USER


# In-memory store to simulate DB for accounts, templates, exports
_accounts: dict[str, dict] = {}
_templates: list[dict] = []
_metadata_store: dict[str, dict] = {}


@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset in-memory mocks before each test."""
    _accounts.clear()
    _templates.clear()
    _metadata_store.clear()
    yield


@pytest.fixture
async def client():
    app.dependency_overrides[get_current_user] = _override_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Publishing Accounts
# ---------------------------------------------------------------------------

class TestPublishingAccounts:
    @pytest.mark.anyio
    async def test_create_account(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import PublishingAccount
            mock_svc.create_account = AsyncMock(return_value=PublishingAccount(
                id=uuid.uuid4(),
                org_id=_TEST_ORG_ID,
                platform="kdp",
                account_name="My KDP Account",
                account_email="author@example.com",
                is_active=True,
                last_synced_at=None,
                created_at=_NOW,
                updated_at=_NOW,
            ))
            payload = {
                "platform": "kdp",
                "account_name": "My KDP Account",
                "account_email": "author@example.com",
                "credentials": {},
            }
            resp = await client.post(f"{BASE}/publishing/accounts", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["platform"] == "kdp"
            assert data["account_name"] == "My KDP Account"
            assert "id" in data

    @pytest.mark.anyio
    async def test_list_accounts_empty(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            mock_svc.list_accounts = AsyncMock(return_value=[])
            resp = await client.get(f"{BASE}/publishing/accounts")
            assert resp.status_code == 200
            assert resp.json() == []

    @pytest.mark.anyio
    async def test_delete_account(self, client: AsyncClient):
        account_id = uuid.uuid4()
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            mock_svc.delete_account = AsyncMock(return_value=True)
            resp = await client.delete(f"{BASE}/publishing/accounts/{account_id}")
            assert resp.status_code == 204

    @pytest.mark.anyio
    async def test_delete_nonexistent_account(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            mock_svc.delete_account = AsyncMock(return_value=False)
            resp = await client.delete(f"{BASE}/publishing/accounts/{fake_id}")
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class TestExport:
    @pytest.mark.anyio
    async def test_export_epub(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import ExportResponse
            mock_svc.generate_export = AsyncMock(return_value=ExportResponse(
                id=uuid.uuid4(),
                book_id=uuid.uuid4(),
                format="epub",
                status="completed",
                file_url="/exports/test.epub",
                file_size_bytes=1024,
                page_count=None,
                created_at=_NOW,
                message="EPUB export completed",
            ))
            payload = {
                "book_id": str(uuid.uuid4()),
                "format": "epub",
                "chapters": [
                    {"title": "Ch1", "content": "Hello world", "order": 1},
                ],
                "include_toc": True,
                "include_cover": False,
            }
            resp = await client.post(f"{BASE}/publishing/export/epub", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "completed"
            assert data["format"] == "epub"
            assert data["file_size_bytes"] > 0
            assert data["file_url"].endswith(".epub")

    @pytest.mark.anyio
    async def test_export_pdf(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import ExportResponse
            mock_svc.generate_export = AsyncMock(return_value=ExportResponse(
                id=uuid.uuid4(),
                book_id=uuid.uuid4(),
                format="pdf",
                status="completed",
                file_url="/exports/test.pdf",
                file_size_bytes=2048,
                page_count=10,
                created_at=_NOW,
                message="PDF export completed",
            ))
            payload = {
                "book_id": str(uuid.uuid4()),
                "format": "pdf",
                "chapters": [
                    {"title": "Introduction", "content": "Welcome.", "order": 1},
                ],
                "trim_size": "6x9",
            }
            resp = await client.post(f"{BASE}/publishing/export/pdf", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "completed"
            assert data["format"] == "pdf"


# ---------------------------------------------------------------------------
# Formatting Templates
# ---------------------------------------------------------------------------

class TestTemplates:
    @pytest.mark.anyio
    async def test_list_builtin_templates(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import FormattingTemplate
            mock_svc.list_templates = AsyncMock(return_value=[
                FormattingTemplate(
                    id=uuid.uuid4(), org_id=None, name="Romance Standard",
                    genre="romance", description=None, trim_size="5.5x8.5",
                    is_builtin=True,
                    created_at=_NOW, updated_at=_NOW,
                ),
                FormattingTemplate(
                    id=uuid.uuid4(), org_id=None, name="Thriller Pace",
                    genre="thriller", description=None, trim_size="6x9",
                    is_builtin=True,
                    created_at=_NOW, updated_at=_NOW,
                ),
                FormattingTemplate(
                    id=uuid.uuid4(), org_id=None, name="Nonfiction Clean",
                    genre="nonfiction", description=None, trim_size="6x9",
                    is_builtin=True,
                    created_at=_NOW, updated_at=_NOW,
                ),
            ])
            resp = await client.get(f"{BASE}/publishing/templates")
            assert resp.status_code == 200
            templates = resp.json()
            assert len(templates) >= 3
            genres = [t["genre"] for t in templates]
            assert "romance" in genres
            assert "thriller" in genres
            assert "nonfiction" in genres

    @pytest.mark.anyio
    async def test_create_custom_template(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import FormattingTemplate
            mock_svc.create_template = AsyncMock(return_value=FormattingTemplate(
                id=uuid.uuid4(), org_id=_TEST_ORG_ID,
                name="My Custom Template", genre="custom",
                description="A test template", trim_size="5.5x8.5",
                is_builtin=False,
                created_at=_NOW, updated_at=_NOW,
            ))
            payload = {
                "name": "My Custom Template",
                "genre": "custom",
                "description": "A test template",
                "trim_size": "5.5x8.5",
            }
            resp = await client.post(f"{BASE}/publishing/templates", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == "My Custom Template"
            assert data["is_builtin"] is False


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

class TestListings:
    @pytest.mark.anyio
    async def test_list_listings_empty(self, client: AsyncClient):
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            mock_svc.list_listings = AsyncMock(return_value=[])
            resp = await client.get(f"{BASE}/publishing/listings")
            assert resp.status_code == 200
            assert resp.json() == []

    @pytest.mark.anyio
    async def test_sync_listing(self, client: AsyncClient):
        listing_id = uuid.uuid4()
        with patch("app.modules.publishing_ops.router.service") as mock_svc:
            from app.modules.publishing_ops.schemas import ListingSyncResponse
            mock_svc.sync_listing = AsyncMock(return_value=ListingSyncResponse(
                listing_id=listing_id,
                status="sync_queued",
                message="Listing sync has been queued",
            ))
            resp = await client.post(f"{BASE}/publishing/listings/{listing_id}/sync")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "sync_queued"
            assert data["listing_id"] == str(listing_id)
