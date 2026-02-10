"""Integration tests for the Publishing Operations Center API.

These tests exercise the full request/response cycle through
the FastAPI router, service layer, and generators.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.publishing_ops.router import router, metadata_router
from app.modules.publishing_ops.service import _reset_stores
from app.modules.publishing_ops.schemas import (
    ExportFormat,
    PlatformType,
    TemplateGenre,
    TrimSize,
)

# Build a minimal FastAPI app for testing
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1/publishing")
app.include_router(metadata_router, prefix="/api/v1")

BASE = "/api/v1"


@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset in-memory stores before each test."""
    _reset_stores()
    yield
    _reset_stores()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Publishing Accounts
# ---------------------------------------------------------------------------

class TestPublishingAccounts:
    @pytest.mark.anyio
    async def test_list_accounts_empty(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/publishing/accounts")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.anyio
    async def test_create_account(self, client: AsyncClient):
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
    async def test_create_and_list_accounts(self, client: AsyncClient):
        payload = {
            "platform": "ingram_spark",
            "account_name": "IngramSpark Acct",
        }
        await client.post(f"{BASE}/publishing/accounts", json=payload)
        resp = await client.get(f"{BASE}/publishing/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.anyio
    async def test_delete_account(self, client: AsyncClient):
        payload = {"platform": "kdp", "account_name": "To Delete"}
        create_resp = await client.post(f"{BASE}/publishing/accounts", json=payload)
        account_id = create_resp.json()["id"]

        del_resp = await client.delete(f"{BASE}/publishing/accounts/{account_id}")
        assert del_resp.status_code == 204

        list_resp = await client.get(f"{BASE}/publishing/accounts")
        assert len(list_resp.json()) == 0

    @pytest.mark.anyio
    async def test_delete_nonexistent_account(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.delete(f"{BASE}/publishing/accounts/{fake_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class TestExport:
    @pytest.mark.anyio
    async def test_export_epub(self, client: AsyncClient):
        payload = {
            "book_id": str(uuid.uuid4()),
            "format": "epub",
            "chapters": [
                {"title": "Ch1", "content": "Hello world", "order": 1},
                {"title": "Ch2", "content": "Goodbye world", "order": 2},
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
        payload = {
            "book_id": str(uuid.uuid4()),
            "format": "pdf",
            "chapters": [
                {"title": "Introduction", "content": "Welcome to the book.", "order": 1},
            ],
            "trim_size": "6x9",
            "include_isbn_barcode": True,
            "isbn": "978-3-16-148410-0",
        }
        resp = await client.post(f"{BASE}/publishing/export/pdf", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["format"] == "pdf"
        assert data["file_size_bytes"] > 0

    @pytest.mark.anyio
    async def test_export_epub_empty_chapters(self, client: AsyncClient):
        payload = {
            "book_id": str(uuid.uuid4()),
            "format": "epub",
            "chapters": [],
        }
        resp = await client.post(f"{BASE}/publishing/export/epub", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# Formatting Templates
# ---------------------------------------------------------------------------

class TestTemplates:
    @pytest.mark.anyio
    async def test_list_builtin_templates(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/publishing/templates")
        assert resp.status_code == 200
        templates = resp.json()
        # At least 8 built-in templates
        assert len(templates) >= 8
        genres = [t["genre"] for t in templates]
        assert "romance" in genres
        assert "thriller" in genres
        assert "nonfiction" in genres

    @pytest.mark.anyio
    async def test_create_custom_template(self, client: AsyncClient):
        payload = {
            "name": "My Custom Template",
            "genre": "custom",
            "description": "A test template",
            "trim_size": "5.5x8.5",
            "style_settings": {
                "font_family": "Courier",
                "font_size_pt": 10.0,
                "line_height": 1.3,
            },
        }
        resp = await client.post(f"{BASE}/publishing/templates", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Custom Template"
        assert data["is_builtin"] is False

    @pytest.mark.anyio
    async def test_custom_template_in_list(self, client: AsyncClient):
        payload = {
            "name": "Another Template",
            "genre": "custom",
        }
        await client.post(f"{BASE}/publishing/templates", json=payload)
        resp = await client.get(f"{BASE}/publishing/templates")
        names = [t["name"] for t in resp.json()]
        assert "Another Template" in names


# ---------------------------------------------------------------------------
# Book Metadata
# ---------------------------------------------------------------------------

class TestBookMetadata:
    @pytest.mark.anyio
    async def test_get_metadata_not_found(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        resp = await client.get(f"{BASE}/books/{book_id}/metadata")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_update_creates_metadata(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        payload = {
            "title": "My Great Novel",
            "subtitle": "A Thrilling Tale",
            "description": "A description of the book.",
            "authors": ["Jane Author"],
            "keywords": ["thriller", "suspense"],
            "categories": ["Fiction > Thriller"],
            "isbn": "978-0-123456-47-2",
        }
        resp = await client.patch(f"{BASE}/books/{book_id}/metadata", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My Great Novel"
        assert data["isbn"] == "978-0-123456-47-2"

    @pytest.mark.anyio
    async def test_get_metadata_after_update(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        await client.patch(
            f"{BASE}/books/{book_id}/metadata",
            json={"title": "Retrievable Book"},
        )
        resp = await client.get(f"{BASE}/books/{book_id}/metadata")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Retrievable Book"

    @pytest.mark.anyio
    async def test_partial_update(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        await client.patch(
            f"{BASE}/books/{book_id}/metadata",
            json={"title": "Original Title", "description": "Original desc"},
        )
        # Update only the description
        resp = await client.patch(
            f"{BASE}/books/{book_id}/metadata",
            json={"description": "Updated desc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Original Title"
        assert data["description"] == "Updated desc"

    @pytest.mark.anyio
    async def test_update_pricing(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        payload = {
            "title": "Priced Book",
            "pricing": {"currency": "USD", "list_price": 9.99, "sale_price": 4.99},
        }
        resp = await client.patch(f"{BASE}/books/{book_id}/metadata", json=payload)
        assert resp.status_code == 200
        pricing = resp.json()["pricing"]
        assert pricing["list_price"] == 9.99
        assert pricing["sale_price"] == 4.99


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

class TestListings:
    @pytest.mark.anyio
    async def test_list_listings_empty(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/publishing/listings")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.anyio
    async def test_sync_listing(self, client: AsyncClient):
        listing_id = str(uuid.uuid4())
        resp = await client.post(f"{BASE}/publishing/listings/{listing_id}/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sync_queued"
        assert data["listing_id"] == listing_id
