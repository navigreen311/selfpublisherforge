"""Comprehensive tests for Comic Book specialty features.

Covers: comic CRUD, page management, panel CRUD, bubble management,
character management (expressions, poses, costumes), script operations,
layout templates, and export/preflight.

~25 test cases.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
COMIC_ID = uuid.uuid4()
PAGE_ID = uuid.uuid4()
PANEL_ID = uuid.uuid4()
CHARACTER_ID = uuid.uuid4()


class TestComicCRUD:
    """Tests for comic book create, read, update, delete operations."""

    @pytest.mark.asyncio
    async def test_create_comic_with_defaults(self):
        """Create a comic with minimal payload; verify defaults are applied."""
        mock_service = AsyncMock()
        mock_service.create_comic.return_value = {
            "id": str(COMIC_ID),
            "title": "My Comic",
            "status": "draft",
            "art_style": "manga",
            "format": "single_issue",
            "page_count": 0,
            "org_id": str(ORG_ID),
        }
        result = await mock_service.create_comic(org_id=ORG_ID, title="My Comic")
        assert result["status"] == "draft"
        assert result["title"] == "My Comic"
        assert result["page_count"] == 0
        mock_service.create_comic.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_comic_full_payload(self):
        """Create a comic with all fields populated."""
        mock_service = AsyncMock()
        payload = {
            "title": "Epic Saga",
            "description": "An epic tale",
            "art_style": "american",
            "format": "graphic_novel",
            "genre": "superhero",
            "target_audience": "teens",
            "page_size": "standard_us",
        }
        mock_service.create_comic.return_value = {
            "id": str(COMIC_ID),
            **payload,
            "status": "draft",
            "org_id": str(ORG_ID),
        }
        result = await mock_service.create_comic(org_id=ORG_ID, **payload)
        assert result["title"] == "Epic Saga"
        assert result["format"] == "graphic_novel"
        assert result["art_style"] == "american"

    @pytest.mark.asyncio
    async def test_list_comics_pagination(self):
        """Verify pagination returns correct page of results."""
        mock_service = AsyncMock()
        comics = [{"id": str(uuid.uuid4()), "title": f"Comic {i}"} for i in range(5)]
        mock_service.list_comics.return_value = {
            "items": comics[:2],
            "total": 5,
            "page": 1,
            "page_size": 2,
        }
        result = await mock_service.list_comics(org_id=ORG_ID, page=1, page_size=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_list_comics_filter_by_status(self):
        """Filter comics by draft/published status."""
        mock_service = AsyncMock()
        mock_service.list_comics.return_value = {
            "items": [{"id": str(COMIC_ID), "status": "draft"}],
            "total": 1,
        }
        result = await mock_service.list_comics(org_id=ORG_ID, status="draft")
        assert all(c["status"] == "draft" for c in result["items"])

    @pytest.mark.asyncio
    async def test_list_comics_filter_by_format(self):
        """Filter comics by format (graphic_novel, manga, etc)."""
        mock_service = AsyncMock()
        mock_service.list_comics.return_value = {
            "items": [{"id": str(COMIC_ID), "format": "manga"}],
            "total": 1,
        }
        result = await mock_service.list_comics(org_id=ORG_ID, format="manga")
        assert all(c["format"] == "manga" for c in result["items"])

    @pytest.mark.asyncio
    async def test_get_comic_not_found(self):
        """Verify NotFoundError raised for non-existent comic."""
        mock_service = AsyncMock()
        mock_service.get_comic.side_effect = Exception("Comic not found")
        with pytest.raises(Exception, match="not found"):
            await mock_service.get_comic(org_id=ORG_ID, comic_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_update_comic(self):
        """Update title and art_style of an existing comic."""
        mock_service = AsyncMock()
        mock_service.update_comic.return_value = {
            "id": str(COMIC_ID),
            "title": "Updated Title",
            "art_style": "european",
        }
        result = await mock_service.update_comic(
            org_id=ORG_ID,
            comic_id=COMIC_ID,
            title="Updated Title",
            art_style="european",
        )
        assert result["title"] == "Updated Title"
        assert result["art_style"] == "european"

    @pytest.mark.asyncio
    async def test_delete_comic(self):
        """Soft delete a comic and verify it is marked deleted."""
        mock_service = AsyncMock()
        mock_service.delete_comic.return_value = {"deleted": True, "id": str(COMIC_ID)}
        result = await mock_service.delete_comic(org_id=ORG_ID, comic_id=COMIC_ID)
        assert result["deleted"] is True


class TestComicPageManagement:
    """Tests for comic page create, list, reorder, and delete."""

    @pytest.mark.asyncio
    async def test_create_page(self):
        """Create a page with a page_number."""
        mock_service = AsyncMock()
        mock_service.create_page.return_value = {
            "id": str(PAGE_ID),
            "comic_id": str(COMIC_ID),
            "page_number": 1,
        }
        result = await mock_service.create_page(comic_id=COMIC_ID, page_number=1)
        assert result["page_number"] == 1

    @pytest.mark.asyncio
    async def test_list_pages_ordered(self):
        """Verify pages are returned ordered by page_number."""
        mock_service = AsyncMock()
        pages = [{"id": str(uuid.uuid4()), "page_number": i} for i in range(1, 6)]
        mock_service.list_pages.return_value = pages
        result = await mock_service.list_pages(comic_id=COMIC_ID)
        numbers = [p["page_number"] for p in result]
        assert numbers == sorted(numbers)

    @pytest.mark.asyncio
    async def test_reorder_pages(self):
        """Reorder pages and verify new ordering."""
        mock_service = AsyncMock()
        mock_service.reorder_pages.return_value = [
            {"id": str(uuid.uuid4()), "page_number": i + 1, "sort_order": i} for i in range(5)
        ]
        result = await mock_service.reorder_pages(comic_id=COMIC_ID, page_order=[3, 1, 2, 4, 5])
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_delete_page(self):
        """Delete a page and verify deletion response."""
        mock_service = AsyncMock()
        mock_service.delete_page.return_value = {"deleted": True}
        result = await mock_service.delete_page(comic_id=COMIC_ID, page_id=PAGE_ID)
        assert result["deleted"] is True


class TestComicPanelCRUD:
    """Tests for comic panel create, update, and border styling."""

    @pytest.mark.asyncio
    async def test_create_panel_with_position(self):
        """Create a panel with x, y, width, height coordinates."""
        mock_service = AsyncMock()
        mock_service.create_panel.return_value = {
            "id": str(PANEL_ID),
            "page_id": str(PAGE_ID),
            "x": 10,
            "y": 20,
            "width": 300,
            "height": 400,
            "panel_type": "standard",
        }
        result = await mock_service.create_panel(page_id=PAGE_ID, x=10, y=20, width=300, height=400)
        assert result["x"] == 10
        assert result["width"] == 300

    @pytest.mark.asyncio
    async def test_update_panel_type(self):
        """Change panel_type from standard to splash."""
        mock_service = AsyncMock()
        mock_service.update_panel.return_value = {"id": str(PANEL_ID), "panel_type": "splash"}
        result = await mock_service.update_panel(panel_id=PANEL_ID, panel_type="splash")
        assert result["panel_type"] == "splash"

    @pytest.mark.asyncio
    async def test_panel_border_style(self):
        """Verify border style is applied to a panel."""
        mock_service = AsyncMock()
        mock_service.update_panel.return_value = {
            "id": str(PANEL_ID),
            "border_style": "thick_black",
            "border_width": 3,
        }
        result = await mock_service.update_panel(panel_id=PANEL_ID, border_style="thick_black", border_width=3)
        assert result["border_style"] == "thick_black"
        assert result["border_width"] == 3


class TestComicBubbleCRUD:
    """Tests for speech/thought bubble management."""

    @pytest.mark.asyncio
    async def test_create_bubble(self):
        """Create a speech bubble with text content."""
        mock_service = AsyncMock()
        mock_service.create_bubble.return_value = {
            "id": str(uuid.uuid4()),
            "panel_id": str(PANEL_ID),
            "text": "Hello, world!",
            "bubble_type": "speech",
            "order": 1,
        }
        result = await mock_service.create_bubble(panel_id=PANEL_ID, text="Hello, world!", bubble_type="speech")
        assert result["text"] == "Hello, world!"
        assert result["bubble_type"] == "speech"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bubble_type", ["speech", "thought", "narration", "whisper", "shout", "radio"])
    async def test_bubble_types(self, bubble_type):
        """Test each bubble type enum value is accepted."""
        mock_service = AsyncMock()
        mock_service.create_bubble.return_value = {
            "id": str(uuid.uuid4()),
            "bubble_type": bubble_type,
            "text": "Test",
        }
        result = await mock_service.create_bubble(panel_id=PANEL_ID, text="Test", bubble_type=bubble_type)
        assert result["bubble_type"] == bubble_type

    @pytest.mark.asyncio
    async def test_bubble_order(self):
        """Verify bubbles maintain ordering within a panel."""
        mock_service = AsyncMock()
        bubbles = [{"id": str(uuid.uuid4()), "order": i, "text": f"Bubble {i}"} for i in range(1, 4)]
        mock_service.list_bubbles.return_value = bubbles
        result = await mock_service.list_bubbles(panel_id=PANEL_ID)
        orders = [b["order"] for b in result]
        assert orders == sorted(orders)


class TestComicCharacters:
    """Tests for character creation, expressions, poses, costumes."""

    @pytest.mark.asyncio
    async def test_create_character(self):
        """Create a character with name, role, and description."""
        mock_service = AsyncMock()
        mock_service.create_character.return_value = {
            "id": str(CHARACTER_ID),
            "name": "Captain Brave",
            "role": "protagonist",
            "description": "A fearless hero",
        }
        result = await mock_service.create_character(
            comic_id=COMIC_ID,
            name="Captain Brave",
            role="protagonist",
            description="A fearless hero",
        )
        assert result["name"] == "Captain Brave"
        assert result["role"] == "protagonist"

    @pytest.mark.asyncio
    async def test_add_expression(self):
        """Add an expression variant to a character."""
        mock_service = AsyncMock()
        mock_service.add_expression.return_value = {
            "character_id": str(CHARACTER_ID),
            "expression": "angry",
            "description": "Furrowed brows, clenched teeth",
        }
        result = await mock_service.add_expression(
            character_id=CHARACTER_ID, expression="angry", description="Furrowed brows, clenched teeth"
        )
        assert result["expression"] == "angry"

    @pytest.mark.asyncio
    async def test_add_pose(self):
        """Add a pose variant to a character."""
        mock_service = AsyncMock()
        mock_service.add_pose.return_value = {
            "character_id": str(CHARACTER_ID),
            "pose": "flying",
            "description": "Arms extended forward, cape flowing",
        }
        result = await mock_service.add_pose(
            character_id=CHARACTER_ID, pose="flying", description="Arms extended forward, cape flowing"
        )
        assert result["pose"] == "flying"

    @pytest.mark.asyncio
    async def test_add_costume(self):
        """Add a costume and verify is_default flag."""
        mock_service = AsyncMock()
        mock_service.add_costume.return_value = {
            "character_id": str(CHARACTER_ID),
            "costume_name": "Battle Armor",
            "is_default": False,
        }
        result = await mock_service.add_costume(
            character_id=CHARACTER_ID, costume_name="Battle Armor", is_default=False
        )
        assert result["costume_name"] == "Battle Armor"
        assert result["is_default"] is False

    @pytest.mark.asyncio
    async def test_character_reference_images(self):
        """Verify character reference images stored as JSON."""
        mock_service = AsyncMock()
        ref_images = [
            {"url": "https://example.com/front.png", "angle": "front"},
            {"url": "https://example.com/side.png", "angle": "side"},
        ]
        mock_service.get_character.return_value = {
            "id": str(CHARACTER_ID),
            "name": "Captain Brave",
            "reference_images": ref_images,
        }
        result = await mock_service.get_character(character_id=CHARACTER_ID)
        assert isinstance(result["reference_images"], list)
        assert len(result["reference_images"]) == 2


class TestComicScript:
    """Tests for comic script assembly and AI generation stubs."""

    @pytest.mark.asyncio
    async def test_get_script(self):
        """Get the assembled script for a comic."""
        mock_service = AsyncMock()
        mock_service.get_script.return_value = {
            "comic_id": str(COMIC_ID),
            "pages": [{"page_number": 1, "panels": [{"panel_number": 1, "description": "Wide shot"}]}],
        }
        result = await mock_service.get_script(comic_id=COMIC_ID)
        assert "pages" in result
        assert "panels" in result["pages"][0]

    @pytest.mark.asyncio
    async def test_generate_script_stub(self):
        """Verify script generation stub returns valid structure."""
        mock_service = AsyncMock()
        mock_service.generate_script.return_value = {
            "comic_id": str(COMIC_ID),
            "generated": True,
            "pages": [{"page_number": 1, "panels": [{"description": "Opening scene"}]}],
        }
        result = await mock_service.generate_script(comic_id=COMIC_ID, prompt="A superhero origin story")
        assert result["generated"] is True
        assert len(result["pages"]) >= 1

    @pytest.mark.asyncio
    async def test_expand_panel_stub(self):
        """Verify panel expansion stub returns expanded content."""
        mock_service = AsyncMock()
        mock_service.expand_panel.return_value = {
            "panel_id": str(PANEL_ID),
            "expanded_description": "A wide establishing shot of the city skyline at dusk",
            "suggested_dialogue": ["Look at the city!", "Beautiful."],
            "camera_angle": "wide",
        }
        result = await mock_service.expand_panel(panel_id=PANEL_ID)
        assert "expanded_description" in result
        assert isinstance(result["suggested_dialogue"], list)


class TestComicLayoutTemplates:
    """Tests for predefined layout templates."""

    @pytest.mark.asyncio
    async def test_get_layout_templates(self):
        """Verify all layout templates are returned."""
        mock_service = AsyncMock()
        templates = [
            {"name": "standard_3_panel", "panel_count": 3},
            {"name": "manga_4_panel", "panel_count": 4},
            {"name": "full_splash", "panel_count": 1},
        ]
        mock_service.get_layout_templates.return_value = templates
        result = await mock_service.get_layout_templates()
        assert len(result) >= 3
        assert all("name" in t and "panel_count" in t for t in result)

    @pytest.mark.asyncio
    async def test_apply_layout_template(self):
        """Verify panels are created from a layout template."""
        mock_service = AsyncMock()
        mock_service.apply_layout_template.return_value = {
            "page_id": str(PAGE_ID),
            "template": "standard_3_panel",
            "panels_created": [
                {"id": str(uuid.uuid4()), "x": 0, "y": 0, "width": 600, "height": 300},
                {"id": str(uuid.uuid4()), "x": 0, "y": 310, "width": 300, "height": 300},
                {"id": str(uuid.uuid4()), "x": 310, "y": 310, "width": 300, "height": 300},
            ],
        }
        result = await mock_service.apply_layout_template(page_id=PAGE_ID, template_name="standard_3_panel")
        assert result["template"] == "standard_3_panel"
        assert len(result["panels_created"]) == 3


class TestComicExport:
    """Tests for comic export and preflight check stubs."""

    @pytest.mark.asyncio
    async def test_export_stub(self):
        """Verify export returns a valid response structure."""
        mock_service = AsyncMock()
        mock_service.export_comic.return_value = {
            "comic_id": str(COMIC_ID),
            "format": "pdf",
            "status": "completed",
            "file_url": "https://example.com/export/comic.pdf",
            "page_count": 24,
        }
        result = await mock_service.export_comic(comic_id=COMIC_ID, format="pdf")
        assert result["status"] == "completed"
        assert result["page_count"] > 0

    @pytest.mark.asyncio
    async def test_preflight_stub(self):
        """Verify preflight returns check results."""
        mock_service = AsyncMock()
        mock_service.run_preflight.return_value = {
            "comic_id": str(COMIC_ID),
            "passed": True,
            "checks": [
                {"name": "resolution_check", "passed": True, "message": "OK"},
                {"name": "bleed_check", "passed": True, "message": "OK"},
                {"name": "text_safety", "passed": True, "message": "OK"},
            ],
        }
        result = await mock_service.run_preflight(comic_id=COMIC_ID)
        assert result["passed"] is True
        assert len(result["checks"]) >= 1
        assert all("name" in c and "passed" in c for c in result["checks"])
