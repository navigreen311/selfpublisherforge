"""Integration tests for the Product Page Conversion Lab API endpoints.

Tests the full request/response cycle through FastAPI, validating
request validation, response shapes, and HTTP status codes.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.product_page_lab.schemas import (
    BlurbAnalysis,
    CategoryAnalysis,
    KeywordAnalysis,
    ListingAnalysis,
    PriceAnalysis,
    Recommendation,
    TitleAnalysis,
)

API_PREFIX = "/api/v1/product-page"

_TEST_ORG_ID = uuid.uuid4()
_TEST_USER = {"user_id": str(uuid.uuid4()), "org_id": _TEST_ORG_ID, "role": "admin"}


def _make_listing_analysis(asin: str | None = None) -> ListingAnalysis:
    """Build a realistic ``ListingAnalysis`` instance for mocking."""
    return ListingAnalysis(
        asin=asin,
        title="Mock Title",
        title_score=75.0,
        blurb_score=68.0,
        keyword_score=70.0,
        category_score=60.0,
        price_score=80.0,
        overall_score=70.6,
        title_analysis=TitleAnalysis(
            score=75.0,
            length=10,
            has_keywords=True,
            keyword_matches=["romance"],
            power_words=["captivating"],
            issues=[],
        ),
        blurb_analysis=BlurbAnalysis(
            score=68.0,
            word_count=50,
            has_hook=True,
            has_bullet_points=False,
            has_cta=False,
            has_html_formatting=False,
            readability_grade=8.0,
            emotional_words=["love"],
            issues=[],
        ),
        keyword_analysis=KeywordAnalysis(
            score=70.0,
            keywords_found=["romance"],
            keyword_density=1.5,
            missing_high_value_keywords=[],
            over_stuffed=False,
        ),
        category_analysis=CategoryAnalysis(
            score=60.0,
            current_categories=["Romance"],
            suggested_categories=[],
        ),
        price_analysis=PriceAnalysis(
            score=80.0,
            current_price=3.99,
            genre_avg_price=4.99,
            suggested_range="$2.99 - $4.99",
            issues=[],
        ),
        recommendations=[
            Recommendation(
                area="blurb",
                severity="warning",
                message="Blurb could be improved.",
                suggestion="Add a call to action.",
            ),
        ],
    )


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


# ===========================================================================
# POST /analyze
# ===========================================================================

class TestAnalyzeListing:
    """Tests for POST /api/v1/product-page/analyze."""

    @pytest.mark.asyncio
    async def test_analyze_with_asin(self, client: AsyncClient):
        mock_result = _make_listing_analysis(asin="B09V2KKG1D")
        with patch(
            "app.modules.product_page_lab.router.service.analyze_amazon_listing",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await client.post(
                f"{API_PREFIX}/analyze",
                json={"asin": "B09V2KKG1D"},
            )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "overall_score" in data
        assert "title_score" in data
        assert "blurb_score" in data
        assert "keyword_score" in data
        assert "category_score" in data
        assert "price_score" in data
        assert "recommendations" in data
        assert data["asin"] == "B09V2KKG1D"

    @pytest.mark.asyncio
    async def test_analyze_with_url(self, client: AsyncClient):
        mock_result = _make_listing_analysis(asin="B09V2KKG1D")
        with patch(
            "app.modules.product_page_lab.router.service.analyze_amazon_listing",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await client.post(
                f"{API_PREFIX}/analyze",
                json={"url": "https://www.amazon.com/dp/B09V2KKG1D"},
            )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["asin"] == "B09V2KKG1D"

    @pytest.mark.asyncio
    async def test_analyze_missing_asin_and_url(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/analyze",
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_invalid_asin_format(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/analyze",
            json={"asin": "invalid"},
        )
        assert response.status_code == 422


# ===========================================================================
# POST /blurb/generate
# ===========================================================================

class TestBlurbGenerate:
    """Tests for POST /api/v1/product-page/blurb/generate."""

    @pytest.mark.asyncio
    async def test_generate_blurb_variants(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/blurb/generate",
            json={
                "current_blurb": "A thrilling tale of love and betrayal in Victorian England. Two hearts collide in a world of secrets and lies.",
                "genre": "romance",
                "num_variants": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "original_score" in data
        assert "variants" in data
        assert len(data["variants"]) == 2
        for variant in data["variants"]:
            assert "variant_id" in variant
            assert "content" in variant
            assert "style" in variant
            assert "estimated_conversion_score" in variant

    @pytest.mark.asyncio
    async def test_generate_with_keywords(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/blurb/generate",
            json={
                "current_blurb": "A comprehensive guide to personal productivity and time management for busy professionals.",
                "genre": "self_help",
                "keywords": ["productivity", "time management"],
                "num_variants": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["variants"]) == 1

    @pytest.mark.asyncio
    async def test_generate_blurb_too_short(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/blurb/generate",
            json={
                "current_blurb": "Too short",
                "genre": "romance",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_too_many_variants(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/blurb/generate",
            json={
                "current_blurb": "A perfectly normal length blurb about a story.",
                "genre": "romance",
                "num_variants": 10,
            },
        )
        assert response.status_code == 422


# ===========================================================================
# POST /blurb/ab-test  &  GET /blurb/ab-test/{id}
# ===========================================================================

class TestABTest:
    """Tests for A/B test creation and retrieval."""

    @pytest.mark.asyncio
    async def test_create_and_get_ab_test(self, client: AsyncClient):
        book_id = str(uuid.uuid4())

        # Create
        create_response = await client.post(
            f"{API_PREFIX}/blurb/ab-test",
            json={
                "book_id": book_id,
                "name": "Blurb Test Q1 2025",
                "variant_a": "First version of the blurb with emotional hooks and compelling narrative.",
                "variant_b": "Second version of the blurb with benefit-driven approach and bullet points.",
                "duration_days": 14,
            },
        )
        assert create_response.status_code == 201
        create_data = create_response.json()["data"]
        assert create_data["name"] == "Blurb Test Q1 2025"
        assert create_data["status"] == "draft"
        assert create_data["book_id"] == book_id
        test_id = create_data["id"]

        # Get
        get_response = await client.get(f"{API_PREFIX}/blurb/ab-test/{test_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()["data"]
        assert get_data["id"] == test_id
        assert get_data["variant_a"]["variant_label"] == "A"
        assert get_data["variant_b"]["variant_label"] == "B"

    @pytest.mark.asyncio
    async def test_get_ab_test_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{API_PREFIX}/blurb/ab-test/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_ab_test_invalid_variant(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/blurb/ab-test",
            json={
                "book_id": str(uuid.uuid4()),
                "name": "Test",
                "variant_a": "Too short",
                "variant_b": "Also too short",
                "duration_days": 7,
            },
        )
        assert response.status_code == 422


# ===========================================================================
# POST /look-inside/analyze
# ===========================================================================

class TestLookInsideAnalysis:
    """Tests for POST /api/v1/product-page/look-inside/analyze."""

    @pytest.mark.asyncio
    async def test_analyze_look_inside(self, client: AsyncClient):
        preview_text = (
            "The night was dark and full of terrors.\n\n"
            "Sarah crept through the abandoned mansion, her flashlight "
            "cutting through the darkness. Every creak of the floorboards "
            "sent her heart racing.\n\n"
            '"Who\'s there?" she whispered, her voice trembling.\n\n'
            "No answer came. Only the wind howling through broken windows.\n\n"
            "She pressed forward, driven by a desperate need to find the "
            "truth about her sister's disappearance. The clues had led her "
            "here, to this forgotten place on the edge of town."
        )

        response = await client.post(
            f"{API_PREFIX}/look-inside/analyze",
            json={
                "preview_text": preview_text,
                "genre": "thriller",
                "chapter_titles": [
                    "The Disappearance",
                    "Shadows and Secrets",
                    "Chapter 3",
                    "The Truth Emerges",
                    "No Way Out",
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "overall_score" in data
        assert "hook_strength" in data
        assert "first_page_impact" in data
        assert "pacing_score" in data
        assert "toc_effectiveness" in data
        assert "sections" in data
        assert len(data["sections"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_look_inside_short_preview(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/look-inside/analyze",
            json={
                "preview_text": "Too short.",
                "genre": "romance",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_look_inside_no_chapters(self, client: AsyncClient):
        preview_text = (
            "A long enough preview text that meets the minimum length requirement. "
            "It contains several sentences about interesting topics and themes."
        )
        response = await client.post(
            f"{API_PREFIX}/look-inside/analyze",
            json={
                "preview_text": preview_text,
                "genre": "fantasy",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["toc_effectiveness"] <= 50  # No TOC should score low


# ===========================================================================
# POST /mobile-check
# ===========================================================================

class TestMobileCheck:
    """Tests for POST /api/v1/product-page/mobile-check."""

    @pytest.mark.asyncio
    async def test_mobile_check(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/mobile-check",
            json={
                "title": "The Secret Heir: A Captivating Romance Novel About Love and Betrayal",
                "blurb": (
                    "What if everything you believed was a lie? "
                    "A gripping story of passion and deceit that will keep you reading all night. "
                    "When Lady Victoria discovers a dark secret about her family, she must choose "
                    "between duty and desire. Buy now!"
                ),
                "author_name": "Elizabeth Thornton",
                "subtitle": "A Victorian Romance Series Book 1",
                "price": 3.99,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "overall_score" in data
        assert "title_display" in data
        assert "blurb_fold_point" in data
        assert "blurb_above_fold" in data
        assert "device_previews" in data
        assert len(data["device_previews"]) > 0

    @pytest.mark.asyncio
    async def test_mobile_check_short_title(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/mobile-check",
            json={
                "title": "Short Title",
                "blurb": "A short blurb for mobile testing purposes.",
                "author_name": "Author",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title_display"]["is_truncated"] is False

    @pytest.mark.asyncio
    async def test_mobile_check_missing_required_fields(self, client: AsyncClient):
        response = await client.post(
            f"{API_PREFIX}/mobile-check",
            json={"title": "Hello"},
        )
        assert response.status_code == 422


# ===========================================================================
# GET /scores/{book_id}
# ===========================================================================

class TestConversionScores:
    """Tests for GET /api/v1/product-page/scores/{book_id}."""

    @pytest.mark.asyncio
    async def test_get_scores(self, client: AsyncClient):
        book_id = str(uuid.uuid4())
        response = await client.get(f"{API_PREFIX}/scores/{book_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["book_id"] == book_id
        assert "overall_score" in data
        assert "listing_score" in data
        assert "blurb_score" in data
        assert "mobile_score" in data

    @pytest.mark.asyncio
    async def test_get_scores_invalid_uuid(self, client: AsyncClient):
        response = await client.get(f"{API_PREFIX}/scores/not-a-uuid")
        assert response.status_code == 422
