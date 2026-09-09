"""Unit tests for the cover generator module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.cover_design.generator import (
    _pick_dalle_size,
    build_cover_prompt,
    generate_cover_image,
    generate_variations,
)
from app.modules.cover_design.schemas import (
    CoverDimensions,
    CoverGenre,
    CoverPlatform,
)
from app.modules.cover_design.templates import (
    PLATFORM_DIMENSIONS,
    get_all_templates,
    get_dimensions_for_platform,
    get_template_by_id,
    get_templates_by_genre,
)


def _fake_dalle_response():
    """Build a mock OpenAI DALL-E 3 response object."""
    image_datum = MagicMock()
    image_datum.url = "https://fake-dalle.openai.test/generated-image.png"
    image_datum.revised_prompt = "A revised test prompt"
    response = MagicMock()
    response.data = [image_datum]
    return response


@pytest.fixture(autouse=True)
def _mock_openai_dalle(monkeypatch):
    """Patch the OpenAI DALL-E call so no real API request is made.

    This fixture:
    1. Makes ``_get_openai_api_key`` return a fake key so the early-return
       "not configured" branch is skipped.
    2. Replaces ``openai.AsyncOpenAI`` with a mock whose
       ``images.generate`` coroutine returns a fake response.
    """
    monkeypatch.setattr(
        "app.modules.cover_design.generator._get_openai_api_key",
        lambda: "sk-fake-test-key",
    )

    mock_client_instance = MagicMock()
    mock_client_instance.images.generate = AsyncMock(return_value=_fake_dalle_response())
    mock_client_cls = MagicMock(return_value=mock_client_instance)
    monkeypatch.setattr(
        "app.modules.cover_design.generator.openai.AsyncOpenAI",
        mock_client_cls,
    )


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


class TestBuildCoverPrompt:
    """Tests for build_cover_prompt()."""

    def test_basic_prompt_contains_title_and_author(self):
        prompt = build_cover_prompt(
            title="My Great Book",
            author_name="Jane Doe",
            genre=CoverGenre.ROMANCE,
        )
        assert "My Great Book" in prompt
        assert "Jane Doe" in prompt

    def test_prompt_includes_genre_guidance(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.THRILLER,
        )
        # Thriller guidance mentions high-contrast or bold
        assert "contrast" in prompt.lower() or "bold" in prompt.lower() or "dramatic" in prompt.lower()

    def test_prompt_includes_subtitle(self):
        prompt = build_cover_prompt(
            title="Main Title",
            subtitle="A Subtitle",
            author_name="Author",
            genre=CoverGenre.NONFICTION,
        )
        assert "A Subtitle" in prompt

    def test_prompt_includes_mood(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.HORROR,
            mood="creepy and unsettling",
        )
        assert "creepy and unsettling" in prompt

    def test_prompt_includes_style_keywords(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.SCI_FI,
            style_keywords=["minimalist", "neon"],
        )
        assert "minimalist" in prompt
        assert "neon" in prompt

    def test_prompt_includes_color_palette(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.FANTASY,
            color_palette=["#FF0000", "gold"],
        )
        assert "#FF0000" in prompt
        assert "gold" in prompt

    def test_prompt_includes_additional_instructions(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.OTHER,
            additional_instructions="Include a lighthouse",
        )
        assert "Include a lighthouse" in prompt

    def test_prompt_includes_template_layout_guidance(self):
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.ROMANCE,
            template_id="romance-classic",
        )
        # The classic romance template has layout guidance
        assert "layout" in prompt.lower() or "script" in prompt.lower() or "title" in prompt.lower()

    def test_prompt_with_nonexistent_template(self):
        """Should not crash when template_id doesn't match."""
        prompt = build_cover_prompt(
            title="Test",
            author_name="Author",
            genre=CoverGenre.OTHER,
            template_id="nonexistent-template",
        )
        assert "Test" in prompt

    def test_all_genres_have_prompt_fragments(self):
        """Ensure every genre produces a valid prompt without errors."""
        for genre in CoverGenre:
            prompt = build_cover_prompt(
                title="Test Book",
                author_name="Author",
                genre=genre,
            )
            assert len(prompt) > 50
            assert "Test Book" in prompt


# ---------------------------------------------------------------------------
# DALL-E size picker
# ---------------------------------------------------------------------------


class TestPickDalleSize:
    """Tests for _pick_dalle_size()."""

    def test_portrait_ratio(self):
        assert _pick_dalle_size(1600, 2560) == "1024x1792"

    def test_landscape_ratio(self):
        assert _pick_dalle_size(2560, 1600) == "1792x1024"

    def test_square_ratio(self):
        assert _pick_dalle_size(1024, 1024) == "1024x1024"

    def test_nearly_square(self):
        # ratio = 0.9 — should be "square"
        assert _pick_dalle_size(900, 1000) == "1024x1024"


# ---------------------------------------------------------------------------
# Image generation (placeholder)
# ---------------------------------------------------------------------------


class TestGenerateCoverImage:
    """Tests for the async generate_cover_image() function."""

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        result = await generate_cover_image("A test prompt")
        assert "image_url" in result
        assert "thumbnail_url" in result
        assert "prompt_used" in result
        assert "width_px" in result
        assert "height_px" in result
        assert "dpi" in result

    @pytest.mark.asyncio
    async def test_uses_provided_dimensions(self):
        dims = CoverDimensions(width_px=1800, height_px=2700, dpi=300, bleed_px=38)
        result = await generate_cover_image("A test prompt", dimensions=dims)
        assert result["width_px"] == 1800
        assert result["height_px"] == 2700

    @pytest.mark.asyncio
    async def test_defaults_to_amazon_kdp_dimensions(self):
        result = await generate_cover_image("A test prompt")
        kdp_dims = PLATFORM_DIMENSIONS[CoverPlatform.AMAZON_KDP]
        assert result["width_px"] == kdp_dims.width_px
        assert result["height_px"] == kdp_dims.height_px

    @pytest.mark.asyncio
    async def test_image_url_is_not_empty(self):
        result = await generate_cover_image("Test")
        assert result["image_url"]
        assert result["thumbnail_url"]


# ---------------------------------------------------------------------------
# Variation generation
# ---------------------------------------------------------------------------


class TestGenerateVariations:
    """Tests for generate_variations()."""

    @pytest.mark.asyncio
    async def test_returns_correct_count(self):
        results = await generate_variations("Test prompt", "style", count=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_variation_type_is_set(self):
        results = await generate_variations("Test", "color", count=2)
        for r in results:
            assert r["variation_type"] == "color"

    @pytest.mark.asyncio
    async def test_variation_index_is_sequential(self):
        results = await generate_variations("Test", "layout", count=4)
        indices = [r["variation_index"] for r in results]
        assert indices == [0, 1, 2, 3]

    @pytest.mark.asyncio
    async def test_accepts_instructions(self):
        results = await generate_variations(
            "Test prompt",
            "typography",
            count=1,
            instructions="Use a hand-drawn font",
        )
        assert len(results) == 1
        assert "prompt_used" in results[0]


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


class TestTemplates:
    """Tests for the template library."""

    def test_get_all_templates_not_empty(self):
        templates = get_all_templates()
        assert len(templates) > 0

    def test_get_template_by_id(self):
        template = get_template_by_id("romance-classic")
        assert template is not None
        assert template.genre == CoverGenre.ROMANCE

    def test_get_template_by_invalid_id(self):
        template = get_template_by_id("nonexistent-id")
        assert template is None

    def test_get_templates_by_genre(self):
        romance_templates = get_templates_by_genre(CoverGenre.ROMANCE)
        assert len(romance_templates) >= 1
        for t in romance_templates:
            assert t.genre == CoverGenre.ROMANCE

    def test_get_templates_by_genre_empty(self):
        # OTHER might not have templates
        templates = get_templates_by_genre(CoverGenre.OTHER)
        assert isinstance(templates, list)

    def test_all_templates_have_required_fields(self):
        for t in get_all_templates():
            assert t.id
            assert t.name
            assert t.genre in CoverGenre
            assert t.description
            assert t.dimensions
            assert t.dimensions.width_px > 0
            assert t.dimensions.height_px > 0

    def test_get_dimensions_for_platform(self):
        for platform in CoverPlatform:
            dims = get_dimensions_for_platform(platform)
            assert dims.width_px > 0
            assert dims.height_px > 0
            assert dims.dpi >= 72

    def test_templates_cover_major_genres(self):
        """Ensure at least these popular genres have templates."""
        for genre in [
            CoverGenre.ROMANCE,
            CoverGenre.THRILLER,
            CoverGenre.SCI_FI,
            CoverGenre.FANTASY,
            CoverGenre.NONFICTION,
            CoverGenre.CHILDRENS,
        ]:
            templates = get_templates_by_genre(genre)
            assert len(templates) >= 1, f"No templates for {genre}"
