"""Integration tests for the Cover Design API endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db

_TEST_ORG_ID = uuid.uuid4()
_TEST_USER = {"user_id": str(uuid.uuid4()), "org_id": _TEST_ORG_ID, "role": "admin"}

# Mock return value for DALL-E image generation
_MOCK_IMAGE_RESULT = {
    "image_url": "https://example.com/generated-cover.png",
    "thumbnail_url": "https://example.com/generated-cover-thumb.png",
    "prompt_used": "test prompt",
    "width_px": 1600,
    "height_px": 2560,
    "dpi": 300,
    "status": "success",
    "error": None,
}


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Yield an HTTP test client with auth and DB overridden."""
    from app.main import create_app

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _TEST_USER
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_image_generation():
    """Mock DALL-E image generation to avoid external API calls."""

    async def _mock_generate(prompt, dimensions=None, platform=None):
        return {**_MOCK_IMAGE_RESULT, "prompt_used": prompt}

    async def _mock_variations(original_prompt, variation_type, count=3, instructions=None):
        return [
            {
                **_MOCK_IMAGE_RESULT,
                "prompt_used": f"{original_prompt} variation {i}",
                "variation_index": i,
                "variation_type": variation_type,
            }
            for i in range(count)
        ]

    with (
        patch(
            "app.modules.cover_design.service.generate_cover_image",
            side_effect=_mock_generate,
        ),
        patch(
            "app.modules.cover_design.service.generate_variations",
            side_effect=_mock_variations,
        ),
    ):
        yield


# ---------------------------------------------------------------------------
# POST /api/v1/covers/generate
# ---------------------------------------------------------------------------


class TestGenerateCover:
    """Tests for the cover generation endpoint."""

    @pytest.mark.asyncio
    async def test_generate_cover_success(self, client: AsyncClient):
        payload = {
            "title": "My Test Book",
            "author_name": "John Doe",
            "genre": "romance",
            "mood": "warm and inviting",
            "style_keywords": ["elegant", "soft"],
            "color_palette": ["#FF69B4", "#FFD700"],
            "platform": "amazon-kdp",
        }
        response = await client.post("/api/v1/covers/generate", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "My Test Book"
        assert data["author_name"] == "John Doe"
        assert data["genre"] == "romance"
        assert data["status"] == "completed"
        assert data["image_url"] is not None
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_generate_cover_with_book_id(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        payload = {
            "book_id": book_id,
            "title": "Another Book",
            "author_name": "Jane Smith",
            "genre": "thriller",
            "platform": "amazon-kdp",
        }
        response = await client.post("/api/v1/covers/generate", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["book_id"] == book_id

    @pytest.mark.asyncio
    async def test_generate_cover_missing_title(self, client: AsyncClient):
        payload = {
            "author_name": "John Doe",
            "genre": "romance",
        }
        response = await client.post("/api/v1/covers/generate", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_cover_missing_author(self, client: AsyncClient):
        payload = {
            "title": "A Book",
            "genre": "romance",
        }
        response = await client.post("/api/v1/covers/generate", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_cover_invalid_genre(self, client: AsyncClient):
        payload = {
            "title": "A Book",
            "author_name": "Author",
            "genre": "nonexistent-genre",
        }
        response = await client.post("/api/v1/covers/generate", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_cover_all_platforms(self, client: AsyncClient):
        """Ensure all platforms are accepted."""
        platforms = [
            "amazon-kdp",
            "ingram-spark",
            "barnes-noble",
            "apple-books",
            "google-play",
            "custom",
        ]
        for platform in platforms:
            payload = {
                "title": f"Platform Test {platform}",
                "author_name": "Author",
                "genre": "nonfiction",
                "platform": platform,
            }
            response = await client.post("/api/v1/covers/generate", json=payload)
            assert response.status_code == 201, f"Failed for platform {platform}"


# ---------------------------------------------------------------------------
# GET /api/v1/covers/templates
# ---------------------------------------------------------------------------


class TestListTemplates:
    """Tests for the template listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_templates(self, client: AsyncClient):
        response = await client.get("/api/v1/covers/templates")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_list_templates_by_genre(self, client: AsyncClient):
        response = await client.get("/api/v1/covers/templates?genre=romance")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 1
        for t in data:
            assert t["genre"] == "romance"

    @pytest.mark.asyncio
    async def test_list_templates_invalid_genre(self, client: AsyncClient):
        response = await client.get("/api/v1/covers/templates?genre=bogus")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_template_has_required_fields(self, client: AsyncClient):
        response = await client.get("/api/v1/covers/templates")
        data = response.json()["data"]
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "genre" in template
        assert "description" in template
        assert "dimensions" in template
        assert "font_recommendations" in template


# ---------------------------------------------------------------------------
# POST /api/v1/covers/analyze-competitors
# ---------------------------------------------------------------------------


class TestAnalyzeCompetitors:
    """Tests for the competitor analysis endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_competitors_with_urls(self, client: AsyncClient):
        payload = {
            "genre": "thriller",
            "niche_keywords": ["psychological", "domestic"],
            "competitor_image_urls": [
                "https://example.com/cover1.jpg",
                "https://example.com/cover2.jpg",
            ],
            "max_results": 5,
        }
        response = await client.post("/api/v1/covers/analyze-competitors", json=payload)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["genre"] == "thriller"
        assert len(data["niche_keywords"]) == 2
        assert len(data["analyses"]) > 0
        assert len(data["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_competitors_without_urls(self, client: AsyncClient):
        payload = {
            "genre": "romance",
            "niche_keywords": ["billionaire", "contemporary"],
        }
        response = await client.post("/api/v1/covers/analyze-competitors", json=payload)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["genre"] == "romance"
        assert "analyses" in data
        assert "trends" in data

    @pytest.mark.asyncio
    async def test_analyze_competitors_missing_keywords(self, client: AsyncClient):
        payload = {
            "genre": "romance",
            "niche_keywords": [],
        }
        response = await client.post("/api/v1/covers/analyze-competitors", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analysis_response_structure(self, client: AsyncClient):
        payload = {
            "genre": "sci-fi",
            "niche_keywords": ["space opera"],
            "competitor_image_urls": ["https://example.com/cover.jpg"],
        }
        response = await client.post("/api/v1/covers/analyze-competitors", json=payload)
        data = response.json()["data"]
        analysis = data["analyses"][0]
        assert "dominant_colors" in analysis
        assert "text_placement" in analysis
        assert "imagery_style" in analysis
        assert "overall_mood" in analysis
        assert "effectiveness_score" in analysis


# ---------------------------------------------------------------------------
# POST /api/v1/covers/{id}/variations
# ---------------------------------------------------------------------------


class TestCoverVariations:
    """Tests for the variation generation endpoint."""

    @pytest.mark.asyncio
    async def test_create_variations(self, client: AsyncClient):
        # First, create a cover
        create_payload = {
            "title": "Original Cover",
            "author_name": "Author",
            "genre": "fantasy",
        }
        create_resp = await client.post("/api/v1/covers/generate", json=create_payload)
        cover_id = create_resp.json()["data"]["id"]

        # Generate variations
        var_payload = {
            "variation_count": 2,
            "variation_type": "color",
        }
        response = await client.post(f"/api/v1/covers/{cover_id}/variations", json=var_payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data) == 2
        for v in data:
            assert v["title"] == "Original Cover"
            assert v["status"] == "completed"

    @pytest.mark.asyncio
    async def test_variations_for_nonexistent_cover(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        payload = {"variation_count": 1, "variation_type": "style"}
        response = await client.post(f"/api/v1/covers/{fake_id}/variations", json=payload)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/covers/book/{book_id}
# ---------------------------------------------------------------------------


class TestListCoversForBook:
    """Tests for listing covers by book ID."""

    @pytest.mark.asyncio
    async def test_list_covers_for_book(self, client: AsyncClient):
        book_id = str(uuid.uuid4())

        # Create two covers for the same book
        for i in range(2):
            payload = {
                "book_id": book_id,
                "title": f"Book Cover {i}",
                "author_name": "Author",
                "genre": "nonfiction",
            }
            await client.post("/api/v1/covers/generate", json=payload)

        response = await client.get(f"/api/v1/covers/book/{book_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_covers_for_book_empty(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/covers/book/{book_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data == []


# ---------------------------------------------------------------------------
# DELETE /api/v1/covers/{id}
# ---------------------------------------------------------------------------


class TestDeleteCover:
    """Tests for the cover deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_cover(self, client: AsyncClient):
        # Create a cover
        payload = {
            "title": "To Be Deleted",
            "author_name": "Author",
            "genre": "horror",
        }
        create_resp = await client.post("/api/v1/covers/generate", json=payload)
        cover_id = create_resp.json()["data"]["id"]

        # Delete it
        response = await client.delete(f"/api/v1/covers/{cover_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_cover(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/covers/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_cover_not_in_book_listing(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        payload = {
            "book_id": book_id,
            "title": "Will Be Deleted",
            "author_name": "Author",
            "genre": "mystery",
        }
        create_resp = await client.post("/api/v1/covers/generate", json=payload)
        cover_id = create_resp.json()["data"]["id"]

        # Delete
        await client.delete(f"/api/v1/covers/{cover_id}")

        # Should not appear in listing
        list_resp = await client.get(f"/api/v1/covers/book/{book_id}")
        data = list_resp.json()["data"]
        cover_ids = [c["id"] for c in data]
        assert cover_id not in cover_ids
