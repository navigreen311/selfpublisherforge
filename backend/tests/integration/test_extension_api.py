"""Integration tests for the Chrome Extension API endpoints."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# POST /api/v1/extension/extract
# ---------------------------------------------------------------------------


class TestSaveExtractedData:
    """Tests for the data extraction saving endpoint."""

    @pytest.mark.asyncio
    async def test_save_extracted_data_success(self, client: AsyncClient):
        payload = {
            "data": {
                "asin": "B0CTEST001",
                "title": "Test Book Title",
                "author": "John Author",
                "price": 9.99,
                "currency": "USD",
                "bsr": 1234,
                "bsr_categories": {"Kindle eBooks > Romance": 342},
                "categories": ["Romance", "Contemporary"],
                "keywords": ["romance", "love", "drama"],
                "reviews": {
                    "total_reviews": 150,
                    "average_rating": 4.3,
                    "rating_distribution": {"5": 80, "4": 40, "3": 20, "2": 5, "1": 5},
                },
                "page_url": "https://www.amazon.com/dp/B0CTEST001",
                "image_url": "https://images-na.ssl-images-amazon.com/test.jpg",
                "marketplace": "amazon.com",
                "publication_date": "January 15, 2024",
                "page_count": 320,
                "language": "English",
            },
            "notes": "Interesting competitor",
            "tags": ["competitor", "romance"],
        }
        response = await client.post("/api/v1/extension/extract", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["asin"] == "B0CTEST001"
        assert data["title"] == "Test Book Title"
        assert data["bsr"] == 1234
        assert data["id"] is not None
        assert data["org_id"] is not None

    @pytest.mark.asyncio
    async def test_save_extracted_data_minimal(self, client: AsyncClient):
        """Only ASIN and title are truly required."""
        payload = {
            "data": {
                "asin": "B0CTEST002",
                "title": "Minimal Book",
            },
        }
        response = await client.post("/api/v1/extension/extract", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["asin"] == "B0CTEST002"
        assert data["bsr"] is None

    @pytest.mark.asyncio
    async def test_save_extracted_data_missing_asin(self, client: AsyncClient):
        payload = {
            "data": {
                "title": "No ASIN Book",
            },
        }
        response = await client.post("/api/v1/extension/extract", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_save_extracted_data_invalid_asin_length(self, client: AsyncClient):
        payload = {
            "data": {
                "asin": "SHORT",
                "title": "Bad ASIN",
            },
        }
        response = await client.post("/api/v1/extension/extract", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_save_extracted_data_different_marketplace(self, client: AsyncClient):
        payload = {
            "data": {
                "asin": "B0CTEST003",
                "title": "UK Book",
                "marketplace": "amazon.co.uk",
                "currency": "GBP",
                "price": 7.99,
            },
        }
        response = await client.post("/api/v1/extension/extract", json=payload)
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/v1/extension/quick-research
# ---------------------------------------------------------------------------


class TestQuickResearch:
    """Tests for the quick research endpoint."""

    @pytest.mark.asyncio
    async def test_quick_research_with_asin(self, client: AsyncClient):
        # First save some data so there's something to research
        extract_payload = {
            "data": {
                "asin": "B0CRESRCH1",
                "title": "Research Target",
                "bsr": 5000,
                "price": 12.99,
            },
        }
        await client.post("/api/v1/extension/extract", json=extract_payload)

        # Now query
        response = await client.get(
            "/api/v1/extension/quick-research?asin=B0CRESRCH1"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["asin"] == "B0CRESRCH1"
        assert data["title"] == "Research Target"
        assert data["current_bsr"] == 5000

    @pytest.mark.asyncio
    async def test_quick_research_with_keywords(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/extension/quick-research?keywords=romance&keywords=billionaire"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "related_keywords" in data

    @pytest.mark.asyncio
    async def test_quick_research_no_params(self, client: AsyncClient):
        response = await client.get("/api/v1/extension/quick-research")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["asin"] is None

    @pytest.mark.asyncio
    async def test_quick_research_unknown_asin(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/extension/quick-research?asin=B0CUNKNOWN"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["current_bsr"] is None

    @pytest.mark.asyncio
    async def test_quick_research_estimated_sales(self, client: AsyncClient):
        # Save a product with a known BSR
        await client.post(
            "/api/v1/extension/extract",
            json={"data": {"asin": "B0CSALES01", "title": "Sales Test", "bsr": 500}},
        )
        response = await client.get(
            "/api/v1/extension/quick-research?asin=B0CSALES01"
        )
        data = response.json()["data"]
        assert data["estimated_daily_sales"] is not None
        assert data["estimated_daily_sales"] > 0


# ---------------------------------------------------------------------------
# POST /api/v1/extension/clip
# ---------------------------------------------------------------------------


class TestSaveClip:
    """Tests for the Knowledge Vault clip saving endpoint."""

    @pytest.mark.asyncio
    async def test_save_text_clip(self, client: AsyncClient):
        payload = {
            "clip_type": "text",
            "content": "This is an interesting paragraph from a blog post about self-publishing.",
            "source_url": "https://example.com/blog/self-publishing-tips",
            "title": "Self-Publishing Tips",
            "tags": ["tips", "self-publishing"],
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["clip_type"] == "text"
        assert data["title"] == "Self-Publishing Tips"
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_save_link_clip(self, client: AsyncClient):
        payload = {
            "clip_type": "link",
            "content": "https://example.com/great-resource",
            "source_url": "https://example.com",
            "title": "Great Resource",
            "tags": ["resource"],
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["clip_type"] == "link"

    @pytest.mark.asyncio
    async def test_save_product_clip(self, client: AsyncClient):
        payload = {
            "clip_type": "product",
            "content": '{"asin": "B0CTEST001", "title": "Product Clip"}',
            "source_url": "https://www.amazon.com/dp/B0CTEST001",
            "tags": ["amazon", "product"],
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_save_clip_minimal(self, client: AsyncClient):
        payload = {
            "content": "Just some text",
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_save_clip_empty_content(self, client: AsyncClient):
        payload = {
            "clip_type": "text",
            "content": "",
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_save_clip_with_notes(self, client: AsyncClient):
        payload = {
            "content": "Clipped content",
            "notes": "This is relevant to my thriller project",
            "tags": ["thriller", "research"],
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_save_clip_invalid_type(self, client: AsyncClient):
        payload = {
            "clip_type": "invalid_type",
            "content": "Some content",
        }
        response = await client.post("/api/v1/extension/clip", json=payload)
        assert response.status_code == 422
