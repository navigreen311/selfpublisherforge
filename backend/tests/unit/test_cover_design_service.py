"""Unit tests for the Cover Design service layer.

Tests cover generation, variations, template listing, competitor analysis,
and cover queries.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.modules.cover_design import service
from app.modules.cover_design.models import Cover
from app.modules.cover_design.schemas import (
    CompetitorCoverAnalysisRequest,
    CoverGenerateRequest,
    CoverGenre,
    CoverPlatform,
    CoverStatus,
    CoverVariationRequest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_cover(
    db,
    org_id: uuid.UUID,
    book_id: uuid.UUID | None = None,
    title: str = "Test Cover",
    status: str = "completed",
) -> Cover:
    """Create a cover record."""
    cover = Cover(
        id=uuid.uuid4(),
        org_id=org_id,
        book_id=book_id or uuid.uuid4(),
        title=title,
        subtitle="A subtitle",
        author_name="Test Author",
        genre="fantasy",
        status=status,
        platform="amazon-kdp",
        image_url="https://example.com/cover.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        prompt_used="A fantasy cover with dragons",
        width_px=1600,
        height_px=2560,
        dpi=300,
        metadata_json={},
    )
    db.add(cover)
    await db.flush()
    await db.refresh(cover)
    return cover


# ---------------------------------------------------------------------------
# Cover generation tests
# ---------------------------------------------------------------------------


class TestGenerateCover:

    @pytest.mark.asyncio
    async def test_generate_cover_success(self, db_session):
        """Should generate a new cover and persist it."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        request = CoverGenerateRequest(
            book_id=book_id,
            title="My Book",
            subtitle="A Subtitle",
            author_name="John Doe",
            genre=CoverGenre.FANTASY,
            platform=CoverPlatform.AMAZON_KDP,
            mood="epic",
            style_keywords=["dragons", "magic"],
            color_palette=["red", "gold"],
            additional_instructions="Make it dramatic",
        )

        mock_result = {
            "image_url": "https://example.com/generated.jpg",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "prompt_used": "Epic fantasy cover with dragons",
            "width_px": 1600,
            "height_px": 2560,
            "dpi": 300,
        }

        with patch(
            "app.modules.cover_design.service.generate_cover_image",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = mock_result

            result = await service.generate_cover(db_session, org_id, request)

        assert result.org_id == org_id
        assert result.book_id == book_id
        assert result.title == "My Book"
        assert result.status == CoverStatus.COMPLETED
        assert result.image_url == "https://example.com/generated.jpg"

    @pytest.mark.asyncio
    async def test_generate_cover_failure(self, db_session):
        """Should mark cover as failed if generation fails."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        request = CoverGenerateRequest(
            book_id=book_id,
            title="My Book",
            author_name="John Doe",
            genre=CoverGenre.ROMANCE,
            platform=CoverPlatform.AMAZON_KDP,
        )

        with patch(
            "app.modules.cover_design.service.generate_cover_image",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.side_effect = RuntimeError("Generation failed")

            result = await service.generate_cover(db_session, org_id, request)

        assert result.status == CoverStatus.FAILED


# ---------------------------------------------------------------------------
# Variation tests
# ---------------------------------------------------------------------------


class TestCreateVariations:

    @pytest.mark.asyncio
    async def test_create_variations_success(self, db_session):
        """Should create variations of an existing cover."""
        org_id = uuid.uuid4()
        original = await _seed_cover(db_session, org_id, title="Original Cover")

        request = CoverVariationRequest(
            variation_type="color",
            variation_count=2,
            instructions="Change the color scheme",
        )

        mock_variations = [
            {
                "image_url": "https://example.com/var1.jpg",
                "thumbnail_url": "https://example.com/var1_thumb.jpg",
                "prompt_used": "Variation 1 prompt",
                "variation_type": "color",
                "variation_index": 0,
                "width_px": 1600,
                "height_px": 2560,
                "dpi": 300,
            },
            {
                "image_url": "https://example.com/var2.jpg",
                "thumbnail_url": "https://example.com/var2_thumb.jpg",
                "prompt_used": "Variation 2 prompt",
                "variation_type": "color",
                "variation_index": 1,
                "width_px": 1600,
                "height_px": 2560,
                "dpi": 300,
            },
        ]

        with patch(
            "app.modules.cover_design.service.generate_variations",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = mock_variations

            result = await service.create_variations(
                db_session, org_id, original.id, request
            )

        assert len(result) == 2
        assert result[0].image_url == "https://example.com/var1.jpg"
        assert result[1].image_url == "https://example.com/var2.jpg"

    @pytest.mark.asyncio
    async def test_create_variations_cover_not_found(self, db_session):
        """Should raise exception if original cover not found."""
        org_id = uuid.uuid4()
        cover_id = uuid.uuid4()

        request = CoverVariationRequest(
            variation_type="style",
            variation_count=1,
        )

        with pytest.raises(AppException) as exc_info:
            await service.create_variations(db_session, org_id, cover_id, request)
        assert exc_info.value.code == "COVER_NOT_FOUND"


# ---------------------------------------------------------------------------
# Template listing tests
# ---------------------------------------------------------------------------


class TestListTemplates:

    @pytest.mark.asyncio
    async def test_list_all_templates(self):
        """Should return all templates when no genre filter."""
        with patch("app.modules.cover_design.service.get_all_templates") as mock_get:
            mock_get.return_value = [
                MagicMock(
                    id="tmpl1",
                    name="Template 1",
                    genre=CoverGenre.FANTASY,
                    description="A fantasy template",
                    thumbnail_url="https://example.com/t1.jpg",
                    dimensions={"width": 1600, "height": 2560},
                    font_recommendations=["Arial"],
                    layout_guidance="Center aligned",
                    tags=["epic"],
                )
            ]

            result = await service.list_templates()

        assert len(result) == 1
        assert result[0].name == "Template 1"

    @pytest.mark.asyncio
    async def test_list_templates_by_genre(self):
        """Should filter templates by genre."""
        with patch("app.modules.cover_design.service.get_templates_by_genre") as mock_get:
            mock_get.return_value = [
                MagicMock(
                    id="tmpl2",
                    name="Romance Template",
                    genre=CoverGenre.ROMANCE,
                    description="A romance template",
                    thumbnail_url="https://example.com/t2.jpg",
                    dimensions={"width": 1600, "height": 2560},
                    font_recommendations=["Georgia"],
                    layout_guidance="Centered title",
                    tags=["romance"],
                )
            ]

            result = await service.list_templates(genre=CoverGenre.ROMANCE)

        assert len(result) == 1
        assert result[0].genre == CoverGenre.ROMANCE


# ---------------------------------------------------------------------------
# Competitor analysis tests
# ---------------------------------------------------------------------------


class TestAnalyzeCompetitors:

    @pytest.mark.asyncio
    async def test_analyze_competitors_success(self):
        """Should analyze competitor covers."""
        request = CompetitorCoverAnalysisRequest(
            genre=CoverGenre.THRILLER,
            niche_keywords=["spy", "conspiracy"],
            competitor_image_urls=[
                "https://example.com/comp1.jpg",
                "https://example.com/comp2.jpg",
            ],
            max_results=5,
        )

        mock_response = MagicMock(
            genre=CoverGenre.THRILLER,
            trends=["Dark colors", "Bold typography"],
            common_elements=["City skylines", "Shadowy figures"],
            recommendations=["Use dark blue palette", "Add suspense elements"],
        )

        with patch(
            "app.modules.cover_design.service.analyze_competitor_covers",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = mock_response

            result = await service.analyze_competitors(request)

        assert result.genre == CoverGenre.THRILLER
        assert "Dark colors" in result.trends


# ---------------------------------------------------------------------------
# Cover query tests
# ---------------------------------------------------------------------------


class TestListCoversForBook:

    @pytest.mark.asyncio
    async def test_list_covers_empty(self, db_session):
        """Should return empty list if no covers exist."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        result = await service.list_covers_for_book(db_session, org_id, book_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_covers_for_book(self, db_session):
        """Should return all covers for a specific book."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        cover1 = await _seed_cover(db_session, org_id, book_id, "Cover 1")
        cover2 = await _seed_cover(db_session, org_id, book_id, "Cover 2")
        # Different book - should not appear
        await _seed_cover(db_session, org_id, uuid.uuid4(), "Other Cover")

        result = await service.list_covers_for_book(db_session, org_id, book_id)
        assert len(result) == 2
        titles = {c.title for c in result}
        assert "Cover 1" in titles
        assert "Cover 2" in titles


class TestGetCoverById:

    @pytest.mark.asyncio
    async def test_get_cover_success(self, db_session):
        """Should retrieve a single cover by ID."""
        org_id = uuid.uuid4()
        cover = await _seed_cover(db_session, org_id, title="My Cover")

        result = await service.get_cover_by_id(db_session, org_id, cover.id)
        assert result.id == cover.id
        assert result.title == "My Cover"

    @pytest.mark.asyncio
    async def test_get_cover_not_found(self, db_session):
        """Should raise exception if cover not found."""
        org_id = uuid.uuid4()
        cover_id = uuid.uuid4()

        with pytest.raises(AppException) as exc_info:
            await service.get_cover_by_id(db_session, org_id, cover_id)
        assert exc_info.value.code == "COVER_NOT_FOUND"


class TestDeleteCover:

    @pytest.mark.asyncio
    async def test_delete_cover_success(self, db_session):
        """Should soft-delete a cover."""
        org_id = uuid.uuid4()
        cover = await _seed_cover(db_session, org_id)

        result = await service.delete_cover(db_session, org_id, cover.id)
        assert result is True

        # Verify it's soft-deleted
        with pytest.raises(AppException) as exc_info:
            await service.get_cover_by_id(db_session, org_id, cover.id)
        assert exc_info.value.code == "COVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_cover_not_found(self, db_session):
        """Should raise exception if cover doesn't exist."""
        org_id = uuid.uuid4()
        cover_id = uuid.uuid4()

        with pytest.raises(AppException) as exc_info:
            await service.delete_cover(db_session, org_id, cover_id)
        assert exc_info.value.code == "COVER_NOT_FOUND"
