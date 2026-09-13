"""End-to-end tests for the publishing operations flow.

Each test exercises a complete user journey through the HTTP API,
combining authentication, publishing accounts, listings, templates,
book metadata, and export endpoints.  Tests use the async HTTPX client
and in-memory SQLite fixtures from ``conftest.py``.

Where the API does not yet expose CRUD endpoints (e.g. listing
creation, project/book creation), the test inserts rows directly
via the DB session so that subsequent API calls have data to act on.
"""

from __future__ import annotations

import uuid
from datetime import UTC

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.project import Book, BookFormat, BookStatus, Project, ProjectType
from app.models.publishing import (
    Listing,
)
from app.models.publishing import (
    ListingStatus as ListingStatusEnum,
)

settings = get_settings()
AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"
PUB_PREFIX = f"{settings.API_V1_PREFIX}/publishing"
API_PREFIX = settings.API_V1_PREFIX

VALID_PASSWORD = "StrongP@ss1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(
    client: AsyncClient,
    email: str = "pub-e2e@test.com",
    password: str = VALID_PASSWORD,
    name: str = "Pub E2E Tester",
    org_name: str = "Pub E2E Org",
) -> dict:
    """Register a user and return the full response JSON."""
    resp = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "org_name": org_name,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(
    client: AsyncClient,
    email: str,
    password: str = VALID_PASSWORD,
) -> dict:
    """Login and return the response JSON (containing tokens)."""
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth_header(access_token: str) -> dict[str, str]:
    """Build an ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {access_token}"}


async def _register_and_get_token(
    client: AsyncClient,
    email: str,
) -> tuple[str, str]:
    """Register, login, and return ``(access_token, org_id)``."""
    reg_data = await _register(client, email=email)
    org_id = reg_data["user"]["org_id"]
    login_data = await _login(client, email=email)
    access_token = login_data["tokens"]["access_token"]
    return access_token, org_id


async def _create_project_and_book(
    db: AsyncSession,
    org_id: str,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert a Project + Book directly into the DB and return their IDs."""
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        org_id=uuid.UUID(org_id),
        title="Test Book Project",
        type=ProjectType.BOOK,
    )
    db.add(project)
    await db.flush()

    book_id = uuid.uuid4()
    book = Book(
        id=book_id,
        project_id=project_id,
        title="My Test Book",
        format=BookFormat.EBOOK,
        status=BookStatus.DRAFT,
    )
    db.add(book)
    await db.flush()
    return project_id, book_id


async def _create_publishing_account_via_api(
    client: AsyncClient,
    token: str,
    platform: str = "kdp",
    account_name: str = "My KDP Account",
) -> dict:
    """Create a publishing account through the API and return response JSON."""
    resp = await client.post(
        f"{PUB_PREFIX}/accounts",
        json={
            "platform": platform,
            "account_name": account_name,
            "account_email": "author@example.com",
            "credentials": {},
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_listing_in_db(
    db: AsyncSession,
    book_id: uuid.UUID,
    account_id: uuid.UUID,
    platform: str = "kdp",
    status: ListingStatusEnum = ListingStatusEnum.DRAFT,
    title: str | None = None,
    listing_data: dict | None = None,
) -> uuid.UUID:
    """Insert a Listing directly into the DB and return its ID.

    The publishing router does not expose a listing-creation endpoint,
    so E2E tests seed data via the DB for subsequent API assertions.
    """
    listing_id = uuid.uuid4()
    data = listing_data or {
        "platform": platform,
        "title": title or "Test Listing",
    }
    listing = Listing(
        id=listing_id,
        book_id=book_id,
        publishing_account_id=account_id,
        platform_id=None,
        status=status,
        listing_data=data,
    )
    db.add(listing)
    await db.flush()
    return listing_id


# ---------------------------------------------------------------------------
# E2E: Create project -> add listing -> publish flow
# ---------------------------------------------------------------------------


class TestCreateProjectAddListingPublish:
    """Full flow: register, create a project+book, create a publishing
    account, add a listing, and exercise listing retrieval and sync."""

    @pytest.mark.asyncio
    async def test_full_publishing_flow(self, client: AsyncClient, db_session: AsyncSession):
        # 1. Register + login -> get token
        email = "pub-flow-1@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # 2. Create a book project (via DB -- no project API exists)
        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        # 3. Create a publishing account via API
        account_data = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account_data["id"])
        assert account_data["platform"] == "kdp"
        assert account_data["account_name"] == "My KDP Account"

        # 4. Create a listing for the book (via DB)
        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
            platform="kdp",
            title="My Test Book on KDP",
        )

        # 5. GET /publishing/listings -> verify listing appears
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        listings = list_resp.json()
        assert len(listings) >= 1

        found = [l for l in listings if l["id"] == str(listing_id)]
        assert len(found) == 1
        listing = found[0]
        assert listing["book_id"] == str(book_id)
        assert listing["status"] == "draft"

        # 6. Sync the listing
        sync_resp = await client.post(
            f"{PUB_PREFIX}/listings/{listing_id}/sync",
            headers=_auth_header(token),
        )
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["listing_id"] == str(listing_id)
        assert sync_data["status"] in ("sync_queued",)

    @pytest.mark.asyncio
    async def test_publishing_account_lifecycle(self, client: AsyncClient, db_session: AsyncSession):
        """Create an account, list it, then delete it."""
        email = "pub-acct-lifecycle@test.com"
        token, _org_id = await _register_and_get_token(client, email)

        # Create account
        account_data = await _create_publishing_account_via_api(
            client, token, platform="kdp", account_name="Lifecycle KDP"
        )
        account_id = account_data["id"]

        # List accounts -> should contain the new account
        list_resp = await client.get(
            f"{PUB_PREFIX}/accounts",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        accounts = list_resp.json()
        assert any(a["id"] == account_id for a in accounts)

        # Delete account
        del_resp = await client.delete(
            f"{PUB_PREFIX}/accounts/{account_id}",
            headers=_auth_header(token),
        )
        assert del_resp.status_code == 204

        # List accounts -> should be empty (soft-deleted)
        list_resp2 = await client.get(
            f"{PUB_PREFIX}/accounts",
            headers=_auth_header(token),
        )
        assert list_resp2.status_code == 200
        assert not any(a["id"] == account_id for a in list_resp2.json())


# ---------------------------------------------------------------------------
# E2E: Multiple listings for one project
# ---------------------------------------------------------------------------


class TestMultipleListingsForOneProject:
    """Create a project with multiple listings across different platforms."""

    @pytest.mark.asyncio
    async def test_multiple_listings_same_book(self, client: AsyncClient, db_session: AsyncSession):
        email = "multi-listing@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create a book
        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        # Create a KDP publishing account via API
        kdp_account = await _create_publishing_account_via_api(
            client, token, platform="kdp", account_name="KDP Account"
        )
        kdp_account_id = uuid.UUID(kdp_account["id"])

        # Create a second publishing account via API (for a different listing)
        is_account = await _create_publishing_account_via_api(client, token, platform="kdp", account_name="IS Account")
        is_account_id = uuid.UUID(is_account["id"])

        # Create KDP listing (via DB)
        kdp_listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=kdp_account_id,
            platform="kdp",
            title="My Book - KDP Edition",
        )

        # Create IngramSpark listing (via DB)
        # Note: listing_data.platform must use schema PlatformType values
        # (e.g. "ingram_spark"), not DB enum values (e.g. "ingramspark")
        is_listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=is_account_id,
            platform="ingram_spark",
            title="My Book - IngramSpark Edition",
        )

        # GET /publishing/listings -> verify both appear
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        listings = list_resp.json()

        # Filter to only our book's listings
        book_listings = [l for l in listings if l["book_id"] == str(book_id)]
        assert len(book_listings) == 2

        listing_ids = {l["id"] for l in book_listings}
        assert str(kdp_listing_id) in listing_ids
        assert str(is_listing_id) in listing_ids


# ---------------------------------------------------------------------------
# E2E: Listing status transitions
# ---------------------------------------------------------------------------


class TestListingStatusTransitions:
    """Verify that listing status can transition from draft to other states."""

    @pytest.mark.asyncio
    async def test_listing_created_as_draft(self, client: AsyncClient, db_session: AsyncSession):
        """A newly created listing should have 'draft' status."""
        email = "status-draft@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
        )

        # Verify status via the listings API
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        listings = list_resp.json()
        found = [l for l in listings if l["id"] == str(listing_id)]
        assert len(found) == 1
        assert found[0]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_listing_status_changes_to_pending(self, client: AsyncClient, db_session: AsyncSession):
        """Update a listing's status to 'pending' via DB and verify it's
        reflected when queried through the API."""
        email = "status-pending@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
        )

        # Transition status to pending via DB (no update API for listings yet)
        from sqlalchemy import update

        stmt = update(Listing).where(Listing.id == listing_id).values(status=ListingStatusEnum.PENDING)
        await db_session.execute(stmt)
        await db_session.flush()

        # Verify the updated status via the listings API
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        listings = list_resp.json()
        found = [l for l in listings if l["id"] == str(listing_id)]
        assert len(found) == 1
        assert found[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_listing_status_live_via_db(self, client: AsyncClient, db_session: AsyncSession):
        """Verify a listing with 'live' status is correctly reported by the API."""
        email = "status-live@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        # Create a listing already in LIVE status
        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
            status=ListingStatusEnum.LIVE,
        )

        # Verify the live status is returned by the API
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        listings = list_resp.json()
        found = [l for l in listings if l["id"] == str(listing_id)]
        assert len(found) == 1
        assert found[0]["status"] == "live"

    @pytest.mark.asyncio
    async def test_listing_sync_returns_queued(self, client: AsyncClient, db_session: AsyncSession):
        """Syncing a listing returns 'sync_queued' regardless of Celery
        broker availability (either dispatched or inline fallback)."""
        email = "status-sync@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
        )

        sync_resp = await client.post(
            f"{PUB_PREFIX}/listings/{listing_id}/sync",
            headers=_auth_header(token),
        )
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["listing_id"] == str(listing_id)
        assert sync_data["status"] == "sync_queued"
        assert "message" in sync_data


# ---------------------------------------------------------------------------
# E2E: Delete listing (soft-delete)
# ---------------------------------------------------------------------------


class TestDeleteListing:
    """Verify that soft-deleting a listing hides it from the API."""

    @pytest.mark.asyncio
    async def test_soft_deleted_listing_not_returned(self, client: AsyncClient, db_session: AsyncSession):
        """After soft-deleting a listing via DB, the API should no longer
        return it in the listings list."""
        email = "del-listing@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
        )

        # Verify listing exists in the API
        list_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        found_before = [l for l in list_resp.json() if l["id"] == str(listing_id)]
        assert len(found_before) == 1

        # Soft-delete the listing via DB
        from datetime import datetime

        from sqlalchemy import update

        stmt = update(Listing).where(Listing.id == listing_id).values(deleted_at=datetime.now(UTC))
        await db_session.execute(stmt)
        await db_session.flush()

        # Verify listing no longer appears in the API
        list_resp2 = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert list_resp2.status_code == 200
        found_after = [l for l in list_resp2.json() if l["id"] == str(listing_id)]
        assert len(found_after) == 0

    @pytest.mark.asyncio
    async def test_sync_deleted_listing_returns_not_found(self, client: AsyncClient, db_session: AsyncSession):
        """Syncing a soft-deleted listing should return a 'not_found' status."""
        email = "del-sync@test.com"
        token, org_id = await _register_and_get_token(client, email)

        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        account = await _create_publishing_account_via_api(client, token)
        account_id = uuid.UUID(account["id"])

        listing_id = await _create_listing_in_db(
            db_session,
            book_id=book_id,
            account_id=account_id,
        )

        # Soft-delete the listing
        from datetime import datetime

        from sqlalchemy import update

        stmt = update(Listing).where(Listing.id == listing_id).values(deleted_at=datetime.now(UTC))
        await db_session.execute(stmt)
        await db_session.flush()

        # Attempt to sync the deleted listing
        sync_resp = await client.post(
            f"{PUB_PREFIX}/listings/{listing_id}/sync",
            headers=_auth_header(token),
        )
        assert sync_resp.status_code == 200
        data = sync_resp.json()
        assert data["status"] == "not_found"


# ---------------------------------------------------------------------------
# E2E: Book metadata flow
# ---------------------------------------------------------------------------


class TestBookMetadataFlow:
    """Create a book, then update and retrieve its metadata via the API."""

    @pytest.mark.asyncio
    async def test_update_and_get_metadata(self, client: AsyncClient, db_session: AsyncSession):
        email = "metadata@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create a book with initial metadata
        _project_id, book_id = await _create_project_and_book(db_session, org_id)

        # Update metadata via API
        patch_resp = await client.patch(
            f"{API_PREFIX}/books/{book_id}/metadata",
            json={
                "title": "Updated Title",
                "description": "A great book about testing",
                "authors": ["Jane Author"],
                "keywords": ["testing", "automation", "publishing"],
                "categories": ["Technology"],
                "language": "en",
                "isbn": "978-1234567890",
            },
            headers=_auth_header(token),
        )
        assert patch_resp.status_code == 200
        meta = patch_resp.json()
        assert meta["title"] == "Updated Title"
        assert meta["description"] == "A great book about testing"
        assert meta["authors"] == ["Jane Author"]
        assert "testing" in meta["keywords"]
        assert meta["isbn"] == "978-1234567890"

        # Retrieve metadata via GET and verify it matches
        get_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/metadata",
            headers=_auth_header(token),
        )
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved["title"] == "Updated Title"
        assert retrieved["isbn"] == "978-1234567890"
        assert retrieved["book_id"] == str(book_id)


# ---------------------------------------------------------------------------
# E2E: Formatting templates flow
# ---------------------------------------------------------------------------


class TestFormattingTemplatesFlow:
    """Create custom templates and list them alongside built-in ones."""

    @pytest.mark.asyncio
    async def test_create_and_list_templates(self, client: AsyncClient, db_session: AsyncSession):
        email = "templates@test.com"
        token, _org_id = await _register_and_get_token(client, email)

        # List built-in templates
        list_resp = await client.get(
            f"{PUB_PREFIX}/templates",
            headers=_auth_header(token),
        )
        assert list_resp.status_code == 200
        builtin_count = len(list_resp.json())

        # Create a custom template
        create_resp = await client.post(
            f"{PUB_PREFIX}/templates",
            json={
                "name": "My Custom Romance Template",
                "genre": "romance",
                "description": "A custom template for romance novels",
                "trim_size": "5.5x8.5",
            },
            headers=_auth_header(token),
        )
        assert create_resp.status_code == 201
        custom_template = create_resp.json()
        assert custom_template["name"] == "My Custom Romance Template"
        assert custom_template["genre"] == "romance"
        assert custom_template["is_builtin"] is False

        # List again -> should include the new custom template
        list_resp2 = await client.get(
            f"{PUB_PREFIX}/templates",
            headers=_auth_header(token),
        )
        assert list_resp2.status_code == 200
        all_templates = list_resp2.json()
        assert len(all_templates) == builtin_count + 1

        custom_found = [t for t in all_templates if t["name"] == "My Custom Romance Template"]
        assert len(custom_found) == 1


# ---------------------------------------------------------------------------
# E2E: Delete nonexistent account returns 404
# ---------------------------------------------------------------------------


class TestPublishingAccountErrors:
    """Verify error handling for publishing account operations."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_account_returns_404(self, client: AsyncClient, db_session: AsyncSession):
        email = "acct-err@test.com"
        token, _org_id = await _register_and_get_token(client, email)

        fake_id = uuid.uuid4()
        resp = await client.delete(
            f"{PUB_PREFIX}/accounts/{fake_id}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_listing_access_rejected(
        self,
        client: AsyncClient,
    ):
        """Accessing listings without a token should be rejected."""
        resp = await client.get(f"{PUB_PREFIX}/listings")
        # 401, not 403: a missing Authorization header is unauthenticated.
        # FastAPI's HTTPBearer used to answer 403 here, which this test was
        # written against; it returns 401 since 0.12x, per RFC 7235.
        assert resp.status_code == 401
