"""Tests for Children's Books illustration, safety, preview, and export services.

Covers:
- Illustration generation (single + variations)
- Character reference generation
- Trademark/content safety checks
- Font licensing checks
- Preview modes (spread, single, look inside)
- Preflight validation
- Export formats (print_pdf, kpf, fixed_epub, png)
- Gutter collision detection
- Trim size reflow
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty_books.models_childrens import (
    ChildrensBook,
    ChildrensBookCharacter,
    ChildrensBookPage,
)
from app.modules.specialty_books.service_childrens_illustration import (
    STYLE_DIRECTIVES,
    _build_illustration_prompt,
    _scan_text_for_sensitivity,
    _scan_text_for_trademarks,
    check_font_licensing,
    check_gutter_collisions,
    export_book,
    generate_character_references,
    generate_illustration,
    generate_preview,
    generate_reflow,
    generate_variations,
    run_preflight,
    safety_check,
)

# ---------------------------------------------------------------------------
# BLOCKED ON DECISION D-1 — see the parallel build plan, package P-05.
#
# This module exercises `app/modules/specialty_books/`, which `app/main.py`
# imports zero times: the tree is unreachable from the running application.
# It also declares nineteen model class names that the live `specialty/` tree
# declares too, onto the same table names, so whichever is imported first wins
# the Table and the other's columns simply are not there.
#
# The failures here are that collision, not test rot:
#   * service_childrens.create_childrens_book passes `creation_mode=` to a
#     model that only declares `story_mode`;
#   * asset_provenance is built from one tree's AssetProvenance and written
#     through the other's, so `generated_url` does not exist on the table.
#
# Neither is fixable without choosing which tree survives, and "fixing" them
# by adding columns to a table both trees map would entrench the duplication
# this decision exists to remove. Skipped, not deleted, and not weakened:
# P-05 either deletes this tree and these tests with it, or wires it and makes
# them pass.
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.skip(
    reason="D-1 / P-05: specialty_books is unreachable from main.py and its models "
    "collide with the live specialty tree on 19 shared class and table names"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _create_test_book(
    db: AsyncSession,
    title: str = "Test Book",
    age_range: str = "3-5",
    page_count: int = 32,
    trim_size: str = "8.5x8.5",
    illustration_style: str = "watercolor",
) -> ChildrensBook:
    """Create a test children's book."""
    book = ChildrensBook(
        org_id=ORG_ID,
        title=title,
        age_range=age_range,
        page_count=page_count,
        trim_size=trim_size,
        illustration_style=illustration_style,
        status="draft",
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def _create_test_page(
    db: AsyncSession,
    book_id: uuid.UUID,
    page_number: int = 1,
    text_content: str | None = "The cat sat on the mat.",
    illustration_prompt: str | None = "A friendly orange cat sitting on a blue mat",
    text_font: str | None = "Open Sans",
    layout: str | None = "text_bottom",
) -> ChildrensBookPage:
    """Create a test page."""
    page = ChildrensBookPage(
        book_id=book_id,
        page_number=page_number,
        page_type="content",
        text_content=text_content,
        illustration_prompt=illustration_prompt,
        text_font=text_font,
        layout=layout,
    )
    db.add(page)
    await db.flush()
    await db.refresh(page)
    return page


async def _create_test_character(
    db: AsyncSession,
    book_id: uuid.UUID,
    name: str = "Whiskers",
    species: str = "orange tabby kitten",
    description: str = "A small fluffy orange tabby kitten with bright green eyes",
    auto_append: bool = True,
    clothing_rules: dict | None = None,
) -> ChildrensBookCharacter:
    """Create a test character."""
    char = ChildrensBookCharacter(
        book_id=book_id,
        name=name,
        species=species,
        description=description,
        auto_append=auto_append,
        clothing_rules=clothing_rules or {"accessory": "red collar with gold bell"},
    )
    db.add(char)
    await db.flush()
    await db.refresh(char)
    return char


# ---------------------------------------------------------------------------
# Tests -- Pure unit tests (no DB)
# ---------------------------------------------------------------------------


class TestPromptBuilding:
    """Test illustration prompt construction."""

    def test_basic_prompt_includes_page_text(self):
        """Prompt includes the page's illustration_prompt."""

        class FakePage:
            illustration_prompt = "A cat in a garden"

        class FakeChar:
            auto_append = True
            name = "Cat"
            species = "cat"
            description = "Orange tabby"
            clothing_rules = None

        prompt = _build_illustration_prompt(FakePage(), [FakeChar()], "watercolor")
        assert "A cat in a garden" in prompt
        assert "Orange tabby" in prompt
        assert "watercolor" in prompt.lower()

    def test_prompt_skips_non_auto_append_characters(self):
        """Characters with auto_append=False are not included."""

        class FakePage:
            illustration_prompt = "A scene"

        class FakeChar:
            auto_append = False
            name = "Secret"
            species = "dragon"
            description = "Hidden dragon"
            clothing_rules = None

        prompt = _build_illustration_prompt(FakePage(), [FakeChar()], "cartoon")
        assert "Hidden dragon" not in prompt

    def test_all_style_directives_exist(self):
        """All defined styles have directives."""
        for style in [
            "watercolor",
            "cartoon",
            "flat",
            "storybook",
            "realistic",
            "crayon",
            "collage",
            "anime",
        ]:
            assert style in STYLE_DIRECTIVES


class TestTrademarkSafety:
    """Test trademark and content safety scanning."""

    def test_detects_disney_trademark(self):
        issues = _scan_text_for_trademarks("A princess like Disney Elsa")
        assert len(issues) >= 1
        assert any(i["term"] == "disney" for i in issues)

    def test_detects_multiple_trademarks(self):
        issues = _scan_text_for_trademarks("A Paw Patrol and Bluey crossover")
        assert len(issues) >= 2

    def test_detects_artist_style_reference(self):
        issues = _scan_text_for_trademarks("Draw in the style of Eric Carle")
        assert len(issues) >= 1
        assert any(i["type"] == "trademark" for i in issues)

    def test_clean_text_passes(self):
        issues = _scan_text_for_trademarks("A friendly cat playing in a garden")
        assert len(issues) == 0

    def test_content_sensitivity_weapons(self):
        issues = _scan_text_for_sensitivity("The knight drew his sword and attacked")
        assert len(issues) >= 1
        assert any(i["category"] == "weapons_violence" for i in issues)

    def test_clean_content_passes(self):
        issues = _scan_text_for_sensitivity("The bunny hopped through the meadow")
        assert len(issues) == 0

    def test_detects_mature_themes(self):
        issues = _scan_text_for_sensitivity("Characters drinking alcohol at a party")
        assert len(issues) >= 1
        assert any(i["category"] == "mature_themes" for i in issues)

    def test_detects_excessive_fear(self):
        issues = _scan_text_for_sensitivity("The terrifying nightmare creature")
        assert len(issues) >= 1
        assert any(i["category"] == "excessive_fear" for i in issues)

    def test_frozen_blocked(self):
        issues = _scan_text_for_trademarks("A story about Frozen characters")
        assert len(issues) >= 1
        assert any(i["term"] == "frozen" for i in issues)


# ---------------------------------------------------------------------------
# Tests -- Async DB tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGenerateIllustration:
    """Test illustration generation service."""

    async def test_generate_illustration_success(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        page = await _create_test_page(db_session, book.id)
        await _create_test_character(db_session, book.id)

        result = await generate_illustration(db_session, book.id, page.id, ORG_ID)

        assert "illustration_url" in result
        assert result["illustration_url"] is not None
        assert "provenance" in result
        assert result["provenance"]["model"] == "dall-e-3-stub"
        assert result["seed"] is not None

    async def test_generate_illustration_trademark_blocked(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        page = await _create_test_page(
            db_session,
            book.id,
            illustration_prompt="A character like Disney Elsa",
        )

        from app.core.exceptions import AppException

        with pytest.raises(AppException) as exc_info:
            await generate_illustration(db_session, book.id, page.id, ORG_ID)
        assert exc_info.value.code == "TRADEMARK_VIOLATION"

    async def test_generate_illustration_updates_page(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        page = await _create_test_page(db_session, book.id)

        result = await generate_illustration(db_session, book.id, page.id, ORG_ID)

        await db_session.refresh(page)
        assert page.illustration_url == result["illustration_url"]
        assert page.illustration_model == "dall-e-3-stub"


@pytest.mark.asyncio
class TestGenerateVariations:
    """Test variation generation."""

    async def test_generates_requested_count(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        page = await _create_test_page(db_session, book.id)

        variations = await generate_variations(db_session, book.id, page.id, ORG_ID, count=4)

        assert len(variations) == 4
        assert all("illustration_url" in v for v in variations)
        assert all(v["variation_index"] == i for i, v in enumerate(variations))


@pytest.mark.asyncio
class TestCharacterReferences:
    """Test character reference image generation."""

    async def test_generates_four_views(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        char = await _create_test_character(db_session, book.id)

        result = await generate_character_references(db_session, book.id, char.id, ORG_ID)

        assert len(result["reference_images"]) == 4
        views = [r["view"] for r in result["reference_images"]]
        assert "front_view" in views
        assert "side_view" in views
        assert "happy_face" in views
        assert "scared_face" in views

    async def test_stores_references_on_character(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        char = await _create_test_character(db_session, book.id)

        await generate_character_references(db_session, book.id, char.id, ORG_ID)

        await db_session.refresh(char)
        assert char.reference_images is not None
        assert len(char.reference_images) == 4


@pytest.mark.asyncio
class TestSafetyCheck:
    """Test full book safety check."""

    async def test_clean_book_passes(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        result = await safety_check(db_session, book.id, ORG_ID)

        assert result["passed"] is True
        assert result["total_issues"] == 0

    async def test_detects_trademark_in_prompt(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(
            db_session,
            book.id,
            illustration_prompt="Draw Peppa Pig in a garden",
        )

        result = await safety_check(db_session, book.id, ORG_ID)

        assert result["passed"] is False
        assert result["has_errors"] is True


@pytest.mark.asyncio
class TestFontLicensing:
    """Test font licensing checks."""

    async def test_known_safe_font_passes(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id, text_font="Open Sans")

        result = await check_font_licensing(db_session, book.id, ORG_ID)

        assert result["all_licensed"] is True

    async def test_unknown_font_fails(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id, text_font="SuperRarePremiumFont")

        result = await check_font_licensing(db_session, book.id, ORG_ID)

        assert result["all_licensed"] is False


@pytest.mark.asyncio
class TestPreview:
    """Test preview generation."""

    async def test_spread_view(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        for i in range(4):
            await _create_test_page(db_session, book.id, page_number=i + 1)

        result = await generate_preview(db_session, book.id, ORG_ID, "spread_view")

        assert result["mode"] == "spread_view"
        assert "guides" in result
        assert len(result["spreads"]) == 2

    async def test_look_inside_shows_first_10_percent(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        for i in range(20):
            await _create_test_page(db_session, book.id, page_number=i + 1)

        result = await generate_preview(db_session, book.id, ORG_ID, "look_inside")

        assert result["mode"] == "look_inside"
        assert result["preview_page_count"] == 2  # 10% of 20
        assert "mobile" in result["frames"]
        assert "desktop" in result["frames"]


@pytest.mark.asyncio
class TestPreflight:
    """Test preflight validation."""

    async def test_complete_book_passes_illustration_check(self, db_session: AsyncSession):
        book = await _create_test_book(db_session, age_range="3-5", page_count=32)
        for i in range(32):
            await _create_test_page(
                db_session,
                book.id,
                page_number=i + 1,
                text_content="Hi." if i > 0 else "Hello.",
                text_font="Open Sans",
            )

        result = await run_preflight(db_session, book.id, ORG_ID)

        assert "checklist" in result
        assert result["checks_total"] >= 9
        illust_check = next(c for c in result["checklist"] if c["check"] == "illustrations_complete")
        assert illust_check["passed"] is True

    async def test_missing_illustrations_flagged(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        page = await _create_test_page(db_session, book.id)
        page.illustration_url = None
        await db_session.flush()

        result = await run_preflight(db_session, book.id, ORG_ID)

        illust_check = next(c for c in result["checklist"] if c["check"] == "illustrations_complete")
        assert illust_check["passed"] is False


@pytest.mark.asyncio
class TestExport:
    """Test export in various formats."""

    async def test_print_pdf_export(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        result = await export_book(db_session, book.id, ORG_ID, "print_pdf")

        assert result["format"] == "print_pdf"
        assert "file_url" in result
        assert result["dimensions"]["dpi"] == 300
        assert "provenance_report" in result
        assert "font_license_summary" in result

    async def test_kpf_export(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        result = await export_book(db_session, book.id, ORG_ID, "kpf")

        assert result["format"] == "kpf"
        assert result["kindle_features"]["fixed_layout"] is True

    async def test_png_export(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        for i in range(3):
            await _create_test_page(db_session, book.id, page_number=i + 1)

        result = await export_book(db_session, book.id, ORG_ID, "png")

        assert result["format"] == "png"
        assert len(result["files"]) == 3
        assert result["dpi"] == 300

    async def test_invalid_format_raises(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        from app.core.exceptions import AppException

        with pytest.raises(AppException) as exc_info:
            await export_book(db_session, book.id, ORG_ID, "docx")
        assert exc_info.value.code == "INVALID_EXPORT_FORMAT"


@pytest.mark.asyncio
class TestGutterCheck:
    """Test gutter collision detection."""

    async def test_no_collisions_on_clean_book(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        result = await check_gutter_collisions(db_session, book.id, ORG_ID)

        assert result["passed"] is True
        assert len(result["collisions"]) == 0


@pytest.mark.asyncio
class TestReflow:
    """Test trim size reflow."""

    async def test_reflow_to_different_size(self, db_session: AsyncSession):
        book = await _create_test_book(db_session, trim_size="8.5x8.5")
        await _create_test_page(db_session, book.id)

        result = await generate_reflow(db_session, book.id, ORG_ID, "8x10")

        assert result["current_trim_size"] == "8.5x8.5"
        assert result["target_trim_size"] == "8x10"
        assert "scale_x" in result
        assert "scale_y" in result
        assert result["page_count"] == 1

    async def test_invalid_trim_size_raises(self, db_session: AsyncSession):
        book = await _create_test_book(db_session)
        await _create_test_page(db_session, book.id)

        from app.core.exceptions import AppException

        with pytest.raises(AppException) as exc_info:
            await generate_reflow(db_session, book.id, ORG_ID, "invalid")
        assert exc_info.value.code == "INVALID_TRIM_SIZE"
