"""Unit tests for the Cover Design module.

Covers schemas, models, service helpers, analyzer, generator, and templates.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.modules.cover_design.schemas import (
    ColorAnalysis,
    CompetitorAnalysisResponse,
    CompetitorCoverAnalysis,
    CompetitorCoverAnalysisRequest,
    CoverDimensions,
    CoverGenerateRequest,
    CoverGenre,
    CoverPlatform,
    CoverResponse,
    CoverStatus,
    CoverTemplateResponse,
    CoverVariationRequest,
)
from app.modules.cover_design.analyzer import (
    analyze_competitor_covers,
    analyze_single_cover,
)
from app.modules.cover_design.generator import build_cover_prompt
from app.modules.cover_design.templates import (
    get_all_templates,
    get_dimensions_for_platform,
    get_template_by_id,
    get_templates_by_genre,
)
from app.modules.cover_design.service import _cover_to_response


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestCoverSchemas:
    """Validate Pydantic v2 schemas for cover design."""

    def test_cover_response_from_attributes(self):
        assert CoverResponse.model_config.get("from_attributes") is True

    def test_cover_template_response_from_attributes(self):
        assert CoverTemplateResponse.model_config.get("from_attributes") is True

    def test_competitor_cover_analysis_from_attributes(self):
        assert CompetitorCoverAnalysis.model_config.get("from_attributes") is True

    def test_competitor_analysis_response_from_attributes(self):
        assert CompetitorAnalysisResponse.model_config.get("from_attributes") is True

    def test_color_analysis_from_attributes(self):
        assert ColorAnalysis.model_config.get("from_attributes") is True

    def test_generate_request_requires_title(self):
        with pytest.raises(ValidationError):
            CoverGenerateRequest(
                author_name="Author",
                genre=CoverGenre.ROMANCE,
            )

    def test_generate_request_requires_author(self):
        with pytest.raises(ValidationError):
            CoverGenerateRequest(
                title="Book",
                genre=CoverGenre.ROMANCE,
            )

    def test_generate_request_rejects_invalid_genre(self):
        with pytest.raises(ValidationError):
            CoverGenerateRequest(
                title="Book",
                author_name="Author",
                genre="nonexistent",
            )

    def test_generate_request_defaults(self):
        req = CoverGenerateRequest(
            title="Test",
            author_name="Author",
            genre=CoverGenre.THRILLER,
        )
        assert req.platform == CoverPlatform.AMAZON_KDP
        assert req.style_keywords == []
        assert req.color_palette == []
        assert req.book_id is None

    def test_variation_request_defaults(self):
        req = CoverVariationRequest()
        assert req.variation_count == 3
        assert req.variation_type == "style"

    def test_variation_request_count_bounds(self):
        with pytest.raises(ValidationError):
            CoverVariationRequest(variation_count=0)
        with pytest.raises(ValidationError):
            CoverVariationRequest(variation_count=11)

    def test_competitor_analysis_request_requires_keywords(self):
        with pytest.raises(ValidationError):
            CompetitorCoverAnalysisRequest(
                genre=CoverGenre.ROMANCE,
                niche_keywords=[],
            )

    def test_cover_response_construction(self):
        resp = CoverResponse(
            id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            title="Cover",
            author_name="Author",
            genre=CoverGenre.FANTASY,
            status=CoverStatus.COMPLETED,
            platform=CoverPlatform.AMAZON_KDP,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert resp.genre == CoverGenre.FANTASY
        assert resp.status == CoverStatus.COMPLETED


# ---------------------------------------------------------------------------
# Analyzer tests
# ---------------------------------------------------------------------------


class TestAnalyzer:
    """Test the competitor cover analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_single_cover_returns_analysis(self):
        result = await analyze_single_cover("https://example.com/cover.jpg")
        assert isinstance(result, CompetitorCoverAnalysis)
        assert result.image_url == "https://example.com/cover.jpg"
        assert len(result.dominant_colors) > 0
        assert result.effectiveness_score is not None

    @pytest.mark.asyncio
    async def test_analyze_competitor_covers_with_urls(self):
        result = await analyze_competitor_covers(
            genre=CoverGenre.THRILLER,
            niche_keywords=["psychological"],
            image_urls=["https://example.com/c1.jpg", "https://example.com/c2.jpg"],
        )
        assert isinstance(result, CompetitorAnalysisResponse)
        assert result.genre == CoverGenre.THRILLER
        assert len(result.analyses) == 2
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analyze_competitor_covers_without_urls(self):
        result = await analyze_competitor_covers(
            genre=CoverGenre.ROMANCE,
            niche_keywords=["contemporary"],
        )
        assert isinstance(result, CompetitorAnalysisResponse)
        assert len(result.analyses) >= 1
        assert "trends" in result.model_dump()

    @pytest.mark.asyncio
    async def test_analyze_respects_max_results(self):
        urls = [f"https://example.com/cover{i}.jpg" for i in range(10)]
        result = await analyze_competitor_covers(
            genre=CoverGenre.SCI_FI,
            niche_keywords=["space"],
            image_urls=urls,
            max_results=3,
        )
        assert len(result.analyses) == 3

    @pytest.mark.asyncio
    async def test_analysis_trends_structure(self):
        result = await analyze_competitor_covers(
            genre=CoverGenre.FANTASY,
            niche_keywords=["epic"],
            image_urls=["https://example.com/cover.jpg"],
        )
        trends = result.trends
        assert "dominant_colours" in trends
        assert "common_moods" in trends
        assert "average_effectiveness" in trends
        assert "sample_size" in trends


# ---------------------------------------------------------------------------
# Template tests
# ---------------------------------------------------------------------------


class TestTemplates:
    """Test the template library functions."""

    def test_get_all_templates_returns_list(self):
        templates = get_all_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_get_template_by_valid_id(self):
        template = get_template_by_id("romance-classic")
        assert template is not None
        assert template.genre == CoverGenre.ROMANCE

    def test_get_template_by_invalid_id_returns_none(self):
        assert get_template_by_id("nonexistent") is None

    def test_get_templates_by_genre_filters_correctly(self):
        templates = get_templates_by_genre(CoverGenre.THRILLER)
        assert len(templates) >= 1
        for t in templates:
            assert t.genre == CoverGenre.THRILLER

    def test_dimensions_for_all_platforms(self):
        for platform in CoverPlatform:
            dims = get_dimensions_for_platform(platform)
            assert dims.width_px > 0
            assert dims.height_px > 0
            assert dims.dpi > 0


# ---------------------------------------------------------------------------
# Generator prompt-building tests
# ---------------------------------------------------------------------------


class TestBuildCoverPrompt:
    """Test the prompt builder for cover generation."""

    def test_prompt_includes_title_and_author(self):
        prompt = build_cover_prompt(
            title="Amazing Book",
            author_name="Jane Doe",
            genre=CoverGenre.ROMANCE,
        )
        assert "Amazing Book" in prompt
        assert "Jane Doe" in prompt

    def test_prompt_includes_mood_when_provided(self):
        prompt = build_cover_prompt(
            title="Dark Night",
            author_name="Author",
            genre=CoverGenre.THRILLER,
            mood="tense and foreboding",
        )
        assert "tense and foreboding" in prompt

    def test_prompt_all_genres_succeed(self):
        for genre in CoverGenre:
            prompt = build_cover_prompt(
                title="Test",
                author_name="Author",
                genre=genre,
            )
            assert len(prompt) > 50


# ---------------------------------------------------------------------------
# Service helper tests
# ---------------------------------------------------------------------------


class TestCoverToResponse:
    """Test the _cover_to_response helper."""

    def test_maps_cover_orm_object(self):
        mock_cover = MagicMock()
        mock_cover.id = uuid.uuid4()
        mock_cover.org_id = uuid.uuid4()
        mock_cover.book_id = None
        mock_cover.title = "Test Cover"
        mock_cover.subtitle = None
        mock_cover.author_name = "Author"
        mock_cover.genre = "romance"
        mock_cover.status = "completed"
        mock_cover.image_url = "https://example.com/img.png"
        mock_cover.thumbnail_url = "https://example.com/thumb.png"
        mock_cover.prompt_used = "A prompt"
        mock_cover.width_px = 1600
        mock_cover.height_px = 2560
        mock_cover.dpi = 300
        mock_cover.bleed_px = 38
        mock_cover.platform = "amazon-kdp"
        mock_cover.metadata_json = {"mood": "warm"}
        mock_cover.created_at = datetime.now(timezone.utc)
        mock_cover.updated_at = datetime.now(timezone.utc)

        result = _cover_to_response(mock_cover)

        assert isinstance(result, CoverResponse)
        assert result.title == "Test Cover"
        assert result.genre == CoverGenre.ROMANCE
        assert result.status == CoverStatus.COMPLETED
        assert result.dimensions is not None
        assert result.dimensions.width_px == 1600

    def test_maps_cover_without_dimensions(self):
        mock_cover = MagicMock()
        mock_cover.id = uuid.uuid4()
        mock_cover.org_id = uuid.uuid4()
        mock_cover.book_id = None
        mock_cover.title = "No Dims"
        mock_cover.subtitle = None
        mock_cover.author_name = "Author"
        mock_cover.genre = "thriller"
        mock_cover.status = "pending"
        mock_cover.image_url = None
        mock_cover.thumbnail_url = None
        mock_cover.prompt_used = None
        mock_cover.width_px = None
        mock_cover.height_px = None
        mock_cover.dpi = 300
        mock_cover.bleed_px = 0
        mock_cover.platform = "amazon-kdp"
        mock_cover.metadata_json = None
        mock_cover.created_at = datetime.now(timezone.utc)
        mock_cover.updated_at = datetime.now(timezone.utc)

        result = _cover_to_response(mock_cover)

        assert result.dimensions is None
        assert result.metadata == {}


# ---------------------------------------------------------------------------
# Router configuration tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify the cover design router is properly configured."""

    def test_router_exists_and_is_api_router(self):
        from app.modules.cover_design.router import router
        from fastapi import APIRouter

        assert isinstance(router, APIRouter)

    def test_router_has_covers_prefix(self):
        from app.modules.cover_design.router import router

        assert router.prefix == "/covers"

    def test_router_has_correct_tags(self):
        from app.modules.cover_design.router import router

        assert "covers" in router.tags
