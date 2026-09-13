"""End-to-end test: Manuscript creation to publishing flow.

This test exercises the complete user journey from creating a new project
and manuscript, adding chapters, running KDP validation, creating a production
pipeline, exporting formats, and creating platform listings.

Tests use the async HTTPX client and in-memory SQLite fixtures from conftest.py.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.project import Book, BookFormat, BookStatus, Project, ProjectType

settings = get_settings()
AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"
API_PREFIX = settings.API_V1_PREFIX
PUB_PREFIX = f"{settings.API_V1_PREFIX}/publishing"

VALID_PASSWORD = "StrongP@ss1"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def _register(
    client: AsyncClient,
    email: str = "e2e@test.com",
    password: str = VALID_PASSWORD,
    name: str = "E2E Tester",
    org_name: str = "E2E Test Org",
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
    """Build an Authorization: Bearer <token> header dict."""
    return {"Authorization": f"Bearer {access_token}"}


async def _register_and_get_token(
    client: AsyncClient,
    email: str,
) -> tuple[str, str]:
    """Register, login, and return (access_token, org_id)."""
    reg_data = await _register(client, email=email)
    org_id = reg_data["user"]["org_id"]
    login_data = await _login(client, email=email)
    access_token = login_data["tokens"]["access_token"]
    return access_token, org_id


async def _create_project_and_book(
    db: AsyncSession,
    org_id: str,
    book_title: str = "Test Book",
    book_format: BookFormat = BookFormat.EBOOK,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert a Project + Book directly into the DB and return their IDs."""
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        org_id=uuid.UUID(org_id),
        title=f"{book_title} Project",
        type=ProjectType.BOOK,
    )
    db.add(project)
    await db.flush()

    book_id = uuid.uuid4()
    book = Book(
        id=book_id,
        project_id=project_id,
        title=book_title,
        format=book_format,
        status=BookStatus.DRAFT,
    )
    db.add(book)
    await db.flush()
    return project_id, book_id


# ---------------------------------------------------------------------------
# E2E Test: Complete Manuscript to Publishing Flow
# ---------------------------------------------------------------------------


class TestManuscriptToPublishFlow:
    """Complete flow: create project, manuscript, chapters, validate,
    create pipeline, export, and create listing."""

    @pytest.mark.asyncio
    async def test_full_manuscript_to_publish_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test the complete flow from manuscript creation to publishing.

        Flow steps:
        1. Register user and authenticate
        2. Create a new project and book
        3. Create chapters via the AI Writing API
        4. Run KDP validation on the book
        5. Create a production pipeline
        6. Export manuscript as EPUB
        7. Update book metadata
        8. Create a publishing account
        9. Create a listing for the book
        10. Verify final state
        """
        # ===== Step 1: Register + login -> get token =====
        email = "manuscript-flow@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # ===== Step 2: Create a new project and book (via DB) =====
        project_id, book_id = await _create_project_and_book(
            db_session,
            org_id,
            book_title="My First Novel",
            book_format=BookFormat.EBOOK,
        )

        # ===== Step 3: Create chapters via AI Writing API =====
        chapters_created = []

        # Create Chapter 1
        ch1_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            json={
                "title": "Chapter 1: The Beginning",
                "content": "It was a dark and stormy night when everything changed. " * 50,
                "order": 0,
                "synopsis": "Our hero begins their journey",
            },
            headers=_auth_header(token),
        )
        assert ch1_resp.status_code == 201, ch1_resp.text
        ch1_data = ch1_resp.json()
        chapters_created.append(ch1_data["id"])
        assert ch1_data["title"] == "Chapter 1: The Beginning"
        assert ch1_data["order"] == 0
        assert ch1_data["word_count"] > 0

        # Create Chapter 2
        ch2_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            json={
                "title": "Chapter 2: The Journey",
                "content": "The path ahead was long and uncertain, filled with danger. " * 50,
                "order": 1,
                "synopsis": "The journey continues",
            },
            headers=_auth_header(token),
        )
        assert ch2_resp.status_code == 201, ch2_resp.text
        ch2_data = ch2_resp.json()
        chapters_created.append(ch2_data["id"])
        assert ch2_data["order"] == 1

        # Create Chapter 3
        ch3_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            json={
                "title": "Chapter 3: The Resolution",
                "content": "Finally, everything came together in an unexpected way. " * 50,
                "order": 2,
                "synopsis": "The story concludes",
            },
            headers=_auth_header(token),
        )
        assert ch3_resp.status_code == 201, ch3_resp.text
        ch3_data = ch3_resp.json()
        chapters_created.append(ch3_data["id"])
        assert ch3_data["order"] == 2

        # Verify we can list all chapters
        list_chapters_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            headers=_auth_header(token),
        )
        assert list_chapters_resp.status_code == 200
        chapters_list = list_chapters_resp.json()
        assert len(chapters_list) == 3
        assert all(ch["book_id"] == str(book_id) for ch in chapters_list)

        # Verify chapters are ordered correctly
        assert chapters_list[0]["order"] == 0
        assert chapters_list[1]["order"] == 1
        assert chapters_list[2]["order"] == 2

        # ===== Step 4: Get full manuscript =====
        manuscript_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/manuscript",
            headers=_auth_header(token),
        )
        assert manuscript_resp.status_code == 200
        manuscript_data = manuscript_resp.json()
        assert manuscript_data["book_id"] == str(book_id)
        assert len(manuscript_data["chapters"]) == 3
        assert manuscript_data["total_word_count"] > 0

        # ===== Step 5: Run KDP validation =====
        # Run full validation on the book
        validation_resp = await client.post(
            f"{PUB_PREFIX}/validate",
            json={
                "ebook_validation": {
                    "has_toc": True,
                    "image_count": 2,
                    "images": [
                        {
                            "filename": "cover.jpg",
                            "format": "jpeg",
                            "size_bytes": 500000,
                            "dpi": 300,
                        },
                        {
                            "filename": "interior.jpg",
                            "format": "jpeg",
                            "size_bytes": 300000,
                            "dpi": 300,
                        },
                    ],
                    "has_broken_links": False,
                    "has_prohibited_elements": False,
                    "min_font_size_pt": 12,
                    "total_file_size_mb": 8.5,
                },
                "cover_validation": {
                    "cover_type": "ebook",
                    "width_inches": 8.0,
                    "height_inches": 10.0,
                    "dpi": 300,
                    "file_format": "JPEG",
                    "color_space": "RGB",
                },
                "compliance_scan": {
                    "title": "My First Novel",
                    "description": "An exciting new novel about adventure and discovery.",
                    "keywords": ["fiction", "adventure", "mystery"],
                    "content_sample": "It was a dark and stormy night...",
                },
            },
            headers=_auth_header(token),
        )
        assert validation_resp.status_code == 200, validation_resp.text
        validation_data = validation_resp.json()
        assert validation_data["overall_status"] in ["passed", "warnings", "failed"]
        assert "results" in validation_data
        assert isinstance(validation_data["results"], list)
        # Verify validation ran (may have 0 issues which is good)
        assert validation_data["total_errors"] >= 0
        assert validation_data["total_warnings"] >= 0

        # ===== Step 6: Create production pipeline =====
        pipeline_resp = await client.post(
            f"{API_PREFIX}/pipelines",
            json={
                "book_id": str(book_id),
                "name": "Production Pipeline for My First Novel",
                "description": "E-book production pipeline",
            },
            headers=_auth_header(token),
        )
        assert pipeline_resp.status_code == 201, pipeline_resp.text
        pipeline_data = pipeline_resp.json()
        pipeline_id = pipeline_data["id"]
        assert pipeline_data["book_id"] == str(book_id)
        assert pipeline_data["status"] in ["draft", "active"]

        # ===== Step 7: Export as EPUB =====
        export_resp = await client.post(
            f"{PUB_PREFIX}/export/epub",
            json={
                "book_id": str(book_id),
                "format": "epub",
                "template_id": None,
                "include_toc": True,
                "include_cover": True,
            },
            headers=_auth_header(token),
        )
        assert export_resp.status_code == 201, export_resp.text
        export_data = export_resp.json()
        assert export_data["format"] == "epub"
        assert export_data["book_id"] == str(book_id)
        assert export_data["status"] in ["processing", "completed", "queued"]
        # file_url might be None if processing
        assert "file_url" in export_data

        # ===== Step 8: Update book metadata =====
        metadata_resp = await client.patch(
            f"{API_PREFIX}/books/{book_id}/metadata",
            json={
                "title": "My First Novel",
                "description": "An exciting new novel about adventure and discovery in a magical world.",
                "authors": ["Jane Doe"],
                "keywords": ["fiction", "adventure", "mystery", "magic"],
                "categories": ["Fiction", "Adventure"],
                "language": "en",
                "isbn": "978-1234567890",
            },
            headers=_auth_header(token),
        )
        assert metadata_resp.status_code == 200, metadata_resp.text
        metadata_data = metadata_resp.json()
        assert metadata_data["title"] == "My First Novel"
        assert metadata_data["isbn"] == "978-1234567890"
        assert "adventure" in metadata_data["keywords"]

        # ===== Step 9: Create publishing account =====
        account_resp = await client.post(
            f"{PUB_PREFIX}/accounts",
            json={
                "platform": "kdp",
                "account_name": "My KDP Account",
                "account_email": "author@example.com",
                "credentials": {},
            },
            headers=_auth_header(token),
        )
        assert account_resp.status_code == 201, account_resp.text
        account_data = account_resp.json()
        account_id = account_data["id"]
        assert account_data["platform"] == "kdp"

        # ===== Step 10: Create a listing (via DB - no API endpoint exists) =====
        # Insert listing directly since the publishing router doesn't expose
        # a listing creation endpoint
        from app.models.publishing import Listing
        from app.models.publishing import ListingStatus as ListingStatusEnum

        listing_id = uuid.uuid4()
        listing = Listing(
            id=listing_id,
            book_id=book_id,
            publishing_account_id=uuid.UUID(account_id),
            platform_id=None,
            status=ListingStatusEnum.DRAFT,
            listing_data={
                "platform": "kdp",
                "title": "My First Novel",
                "description": "An exciting new novel about adventure and discovery in a magical world.",
                "price": 9.99,
                "keywords": ["fiction", "adventure", "mystery", "magic"],
            },
        )
        db_session.add(listing)
        await db_session.flush()

        # ===== Step 11: Verify listing appears in listings API =====
        listings_resp = await client.get(
            f"{PUB_PREFIX}/listings",
            headers=_auth_header(token),
        )
        assert listings_resp.status_code == 200
        listings = listings_resp.json()
        assert len(listings) >= 1

        found_listing = [l for l in listings if l["id"] == str(listing_id)]
        assert len(found_listing) == 1
        assert found_listing[0]["book_id"] == str(book_id)
        assert found_listing[0]["status"] == "draft"

        # ===== Step 12: Verify final book state =====
        # Get the book metadata to verify everything is connected
        final_metadata_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/metadata",
            headers=_auth_header(token),
        )
        assert final_metadata_resp.status_code == 200
        final_metadata = final_metadata_resp.json()
        assert final_metadata["book_id"] == str(book_id)
        assert final_metadata["title"] == "My First Novel"
        assert final_metadata["isbn"] == "978-1234567890"

        # Verify manuscript still accessible with all chapters
        final_manuscript_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/manuscript",
            headers=_auth_header(token),
        )
        assert final_manuscript_resp.status_code == 200
        final_manuscript = final_manuscript_resp.json()
        assert len(final_manuscript["chapters"]) == 3
        assert final_manuscript["total_word_count"] > 0

    @pytest.mark.asyncio
    async def test_manuscript_readability_analysis(self, client: AsyncClient, db_session: AsyncSession):
        """Test manuscript readability analysis as part of the flow."""
        # Register and authenticate
        email = "readability@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create project and book
        _project_id, book_id = await _create_project_and_book(db_session, org_id, book_title="Readability Test Book")

        # Create a chapter with readable content
        chapter_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            json={
                "title": "Chapter 1",
                "content": "The quick brown fox jumps over the lazy dog. " * 100,
                "order": 0,
            },
            headers=_auth_header(token),
        )
        assert chapter_resp.status_code == 201

        # Get readability score
        readability_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/manuscript/readability-score",
            headers=_auth_header(token),
        )
        assert readability_resp.status_code == 200
        readability = readability_resp.json()
        assert "flesch_reading_ease" in readability
        assert "flesch_kincaid_grade" in readability
        assert "reading_level" in readability

        # Analyze full manuscript
        analysis_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/analyze",
            headers=_auth_header(token),
        )
        assert analysis_resp.status_code == 200
        analysis = analysis_resp.json()
        assert "total_word_count" in analysis
        assert "chapter_count" in analysis
        assert "readability" in analysis

    @pytest.mark.asyncio
    async def test_chapter_reordering(self, client: AsyncClient, db_session: AsyncSession):
        """Test reordering chapters within a manuscript."""
        # Register and authenticate
        email = "reorder@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create project and book
        _project_id, book_id = await _create_project_and_book(db_session, org_id, book_title="Reorder Test Book")

        # Create 3 chapters
        chapter_ids = []
        for i in range(3):
            ch_resp = await client.post(
                f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
                json={
                    "title": f"Chapter {i+1}",
                    "content": f"Content for chapter {i+1}",
                    "order": i,
                },
                headers=_auth_header(token),
            )
            assert ch_resp.status_code == 201
            chapter_ids.append(ch_resp.json()["id"])

        # Reorder: swap chapter 1 and chapter 3
        reorder_resp = await client.patch(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters/reorder",
            json={
                "chapters": [
                    {"chapter_id": chapter_ids[2], "order": 0},  # Ch3 -> first
                    {"chapter_id": chapter_ids[1], "order": 1},  # Ch2 -> middle
                    {"chapter_id": chapter_ids[0], "order": 2},  # Ch1 -> last
                ],
            },
            headers=_auth_header(token),
        )
        assert reorder_resp.status_code == 200
        reordered = reorder_resp.json()
        assert len(reordered) == 3

        # Verify new order
        assert reordered[0]["id"] == chapter_ids[2]
        assert reordered[0]["order"] == 0
        assert reordered[1]["id"] == chapter_ids[1]
        assert reordered[1]["order"] == 1
        assert reordered[2]["id"] == chapter_ids[0]
        assert reordered[2]["order"] == 2

    @pytest.mark.asyncio
    async def test_chapter_update(self, client: AsyncClient, db_session: AsyncSession):
        """Test updating chapter content and title."""
        # Register and authenticate
        email = "update@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create project and book
        _project_id, book_id = await _create_project_and_book(db_session, org_id, book_title="Update Test Book")

        # Create a chapter
        create_resp = await client.post(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
            json={
                "title": "Original Title",
                "content": "Original content",
                "order": 0,
            },
            headers=_auth_header(token),
        )
        assert create_resp.status_code == 201
        chapter_id = create_resp.json()["id"]

        # Update the chapter
        update_resp = await client.put(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters/{chapter_id}",
            json={
                "title": "Updated Title",
                "content": "Updated content with more words and detail",
            },
            headers=_auth_header(token),
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["title"] == "Updated Title"
        assert updated["content"] == "Updated content with more words and detail"
        assert updated["word_count"] > 0

        # Verify update persisted by getting the chapter again
        get_resp = await client.get(
            f"{API_PREFIX}/books/{book_id}/manuscript/chapters/{chapter_id}",
            headers=_auth_header(token),
        )
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved["title"] == "Updated Title"
        assert retrieved["content"] == "Updated content with more words and detail"

    @pytest.mark.asyncio
    async def test_print_book_validation_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test validation flow for a print book."""
        # Register and authenticate
        email = "print-book@test.com"
        token, org_id = await _register_and_get_token(client, email)

        # Create project and book (PRINT format this time)
        _project_id, book_id = await _create_project_and_book(
            db_session,
            org_id,
            book_title="Print Book",
            book_format=BookFormat.PRINT,
        )

        # Create chapters
        for i in range(5):
            await client.post(
                f"{API_PREFIX}/books/{book_id}/manuscript/chapters",
                json={
                    "title": f"Chapter {i+1}",
                    "content": "This is print book content. " * 100,
                    "order": i,
                },
                headers=_auth_header(token),
            )

        # Run print validation
        print_validation_resp = await client.post(
            f"{PUB_PREFIX}/validate/print",
            json={
                "trim_size": "6x9",
                "page_count": 200,
                "paper_type": "white",
                "has_bleed": False,
                "inside_margin": 0.75,
                "outside_margin": 0.5,
                "top_margin": 0.75,
                "bottom_margin": 0.75,
                "image_dpi": 300,
                "fonts_embedded": True,
                "color_space": "CMYK",
            },
            headers=_auth_header(token),
        )
        assert print_validation_resp.status_code == 200
        print_validation = print_validation_resp.json()
        assert print_validation["status"] in ["passed", "warnings", "failed"]

        # Export as PDF
        pdf_export_resp = await client.post(
            f"{PUB_PREFIX}/export/pdf",
            json={
                "book_id": str(book_id),
                "format": "pdf",
                "template_id": None,
                "trim_size": "6x9",
                "include_toc": True,
                "include_cover": True,
            },
            headers=_auth_header(token),
        )
        assert pdf_export_resp.status_code == 201, pdf_export_resp.text
        pdf_export = pdf_export_resp.json()
        assert pdf_export["format"] == "pdf"
        assert pdf_export["book_id"] == str(book_id)
