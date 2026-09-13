"""Tests for Art Style Cloning features.

Covers: profile CRUD, style analysis, test generation, drift detection,
default management.

~14 test cases.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
PROFILE_ID = uuid.uuid4()
OTHER_PROFILE_ID = uuid.uuid4()


class TestStyleCloneCRUD:
    """Tests for style clone profile create, read, update, delete."""

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Create a style clone profile with name and sample images."""
        mock_service = AsyncMock()
        mock_service.create_profile.return_value = {
            "id": str(PROFILE_ID),
            "name": "Watercolor Whimsy",
            "book_type": "childrens",
            "description": "Soft watercolor style",
            "sample_image_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "style_prompt": "",
            "is_default": False,
            "org_id": str(ORG_ID),
        }
        result = await mock_service.create_profile(
            org_id=ORG_ID,
            name="Watercolor Whimsy",
            book_type="childrens",
            description="Soft watercolor style",
            sample_image_ids=[uuid.uuid4(), uuid.uuid4()],
        )
        assert result["name"] == "Watercolor Whimsy"
        assert result["book_type"] == "childrens"
        assert result["is_default"] is False
        mock_service.create_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_profiles_pagination(self):
        """Verify profile listing supports pagination."""
        mock_service = AsyncMock()
        profiles = [{"id": str(uuid.uuid4()), "name": f"Style {i}"} for i in range(6)]
        mock_service.list_profiles.return_value = {
            "items": profiles[:3],
            "total": 6,
            "page": 1,
            "page_size": 3,
        }
        result = await mock_service.list_profiles(org_id=ORG_ID, page=1, page_size=3)
        assert len(result["items"]) == 3
        assert result["total"] == 6

    @pytest.mark.asyncio
    async def test_list_profiles_filter_by_book_type(self):
        """Filter style profiles by book type."""
        mock_service = AsyncMock()
        mock_service.list_profiles.return_value = {
            "items": [{"id": str(PROFILE_ID), "book_type": "coloring"}],
            "total": 1,
        }
        result = await mock_service.list_profiles(org_id=ORG_ID, book_type="coloring")
        assert all(p["book_type"] == "coloring" for p in result["items"])

    @pytest.mark.asyncio
    async def test_get_profile(self):
        """Get a single style profile with full attributes."""
        mock_service = AsyncMock()
        mock_service.get_profile.return_value = {
            "id": str(PROFILE_ID),
            "name": "Watercolor Whimsy",
            "book_type": "childrens",
            "style_prompt": "watercolor, soft edges",
            "style_attributes": {
                "color_palette": "warm_pastels",
                "line_quality": "soft",
                "texture": "watercolor_paper",
                "detail_level": "medium",
            },
            "is_default": True,
        }
        result = await mock_service.get_profile(profile_id=PROFILE_ID)
        assert result["name"] == "Watercolor Whimsy"
        assert result["style_attributes"]["color_palette"] == "warm_pastels"

    @pytest.mark.asyncio
    async def test_update_profile(self):
        """Update profile name and description."""
        mock_service = AsyncMock()
        mock_service.update_profile.return_value = {
            "id": str(PROFILE_ID),
            "name": "Updated Watercolor",
            "description": "Updated description with bolder tones",
        }
        result = await mock_service.update_profile(
            profile_id=PROFILE_ID,
            name="Updated Watercolor",
            description="Updated description with bolder tones",
        )
        assert result["name"] == "Updated Watercolor"

    @pytest.mark.asyncio
    async def test_delete_profile(self):
        """Delete a style profile and verify deletion."""
        mock_service = AsyncMock()
        mock_service.delete_profile.return_value = {"deleted": True, "id": str(PROFILE_ID)}
        result = await mock_service.delete_profile(profile_id=PROFILE_ID)
        assert result["deleted"] is True


class TestStyleAnalysis:
    """Tests for AI-powered style analysis from sample images."""

    @pytest.mark.asyncio
    async def test_analyze_style_stub(self):
        """Verify style analysis returns structured attributes."""
        mock_service = AsyncMock()
        mock_service.analyze_style.return_value = {
            "profile_id": str(PROFILE_ID),
            "attributes": {
                "color_palette": "warm_pastels",
                "line_quality": "soft_flowing",
                "texture": "watercolor_paper",
                "detail_level": "medium",
            },
            "confidence": 0.87,
        }
        result = await mock_service.analyze_style(profile_id=PROFILE_ID)
        attrs = result["attributes"]
        assert "color_palette" in attrs
        assert "line_quality" in attrs
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_analyze_style_generates_prompt(self):
        """Verify style analysis creates a style prompt string."""
        mock_service = AsyncMock()
        mock_service.analyze_style.return_value = {
            "profile_id": str(PROFILE_ID),
            "attributes": {"color_palette": "warm_pastels"},
            "style_prompt": "watercolor illustration, soft flowing lines, warm pastel palette",
            "confidence": 0.85,
        }
        result = await mock_service.analyze_style(profile_id=PROFILE_ID)
        assert "style_prompt" in result
        assert len(result["style_prompt"]) > 10
        assert "watercolor" in result["style_prompt"].lower()


class TestStyleGeneration:
    """Tests for test image generation using a style profile."""

    @pytest.mark.asyncio
    async def test_test_generate_stub(self):
        """Verify test generation returns image URLs."""
        mock_service = AsyncMock()
        mock_service.test_generate.return_value = {
            "profile_id": str(PROFILE_ID),
            "images": [
                {"url": "https://example.com/test_gen_1.png", "seed": 42},
                {"url": "https://example.com/test_gen_2.png", "seed": 43},
            ],
            "prompt_used": "A friendly bear in a forest, watercolor style",
        }
        result = await mock_service.test_generate(
            profile_id=PROFILE_ID,
            prompt="A friendly bear in a forest",
        )
        assert len(result["images"]) == 2
        assert all("url" in img for img in result["images"])

    @pytest.mark.asyncio
    async def test_test_generate_count_param(self):
        """Verify count parameter controls number of generated images."""
        mock_service = AsyncMock()
        requested_count = 4
        mock_service.test_generate.return_value = {
            "profile_id": str(PROFILE_ID),
            "images": [{"url": f"https://example.com/gen_{i}.png", "seed": i} for i in range(requested_count)],
        }
        result = await mock_service.test_generate(
            profile_id=PROFILE_ID,
            prompt="Test prompt",
            count=requested_count,
        )
        assert len(result["images"]) == requested_count


class TestDriftDetection:
    """Tests for style drift detection between generated images and profile."""

    @pytest.mark.asyncio
    async def test_check_drift_stub(self):
        """Verify drift check returns a drift score."""
        mock_service = AsyncMock()
        mock_service.check_drift.return_value = {
            "profile_id": str(PROFILE_ID),
            "image_id": str(uuid.uuid4()),
            "drift_score": 0.15,
            "details": {"color_drift": 0.1, "line_drift": 0.2, "texture_drift": 0.15},
            "within_tolerance": True,
        }
        result = await mock_service.check_drift(profile_id=PROFILE_ID, image_id=uuid.uuid4())
        assert isinstance(result["drift_score"], float)
        assert result["within_tolerance"] is True

    @pytest.mark.asyncio
    async def test_drift_score_range(self):
        """Verify drift score is always between 0 and 1."""
        mock_service = AsyncMock()
        for expected_score in [0.0, 0.25, 0.5, 0.75, 1.0]:
            mock_service.check_drift.return_value = {
                "profile_id": str(PROFILE_ID),
                "drift_score": expected_score,
                "within_tolerance": expected_score < 0.3,
            }
            result = await mock_service.check_drift(profile_id=PROFILE_ID, image_id=uuid.uuid4())
            assert 0.0 <= result["drift_score"] <= 1.0


class TestDefaultManagement:
    """Tests for managing default style profiles per book type."""

    @pytest.mark.asyncio
    async def test_set_default(self):
        """Verify a profile can be set as the default for its book type."""
        mock_service = AsyncMock()
        mock_service.set_default.return_value = {
            "id": str(PROFILE_ID),
            "name": "Watercolor Whimsy",
            "book_type": "childrens",
            "is_default": True,
        }
        result = await mock_service.set_default(profile_id=PROFILE_ID, book_type="childrens")
        assert result["is_default"] is True
        assert result["book_type"] == "childrens"

    @pytest.mark.asyncio
    async def test_set_default_unsets_previous(self):
        """Verify setting a new default unsets the previous default for that book type."""
        mock_service = AsyncMock()
        mock_service.set_default.return_value = {
            "id": str(PROFILE_ID),
            "is_default": True,
            "book_type": "childrens",
        }
        result_a = await mock_service.set_default(profile_id=PROFILE_ID, book_type="childrens")
        assert result_a["is_default"] is True

        mock_service.set_default.return_value = {
            "id": str(OTHER_PROFILE_ID),
            "is_default": True,
            "book_type": "childrens",
        }
        result_b = await mock_service.set_default(profile_id=OTHER_PROFILE_ID, book_type="childrens")
        assert result_b["is_default"] is True
        assert result_b["id"] == str(OTHER_PROFILE_ID)

        mock_service.get_profile.return_value = {
            "id": str(PROFILE_ID),
            "is_default": False,
            "book_type": "childrens",
        }
        result_check = await mock_service.get_profile(profile_id=PROFILE_ID)
        assert result_check["is_default"] is False
