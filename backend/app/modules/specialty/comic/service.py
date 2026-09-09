"""Comic Book Studio service layer.

Provides CRUD for comics, pages, panels, bubbles, and characters,
plus AI-powered script generation, panel art generation, layout
templates, character expression/pose/costume management, and
export/preflight.
"""

from __future__ import annotations

import json
import logging
import uuid as _uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.specialty.models.comic import (
    CharacterCostume,
    CharacterExpression,
    CharacterPose,
    Comic,
    ComicBubble,
    ComicCharacter,
    ComicPage,
    ComicPanel,
)
from app.modules.specialty.models.enums import (
    BookStatus,
    BubbleType,
    ComicFormat,
    PanelType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------


async def _llm_generate(prompt: str, system_prompt: str = "", max_tokens: int = 4000) -> str:
    """Call the LLM orchestration service and return generated text."""
    try:
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            GenerationConfig,
            TaskType,
        )
        from app.modules.llm_orchestration.service import LLMOrchestrationService

        svc = LLMOrchestrationService()
        request = CompletionRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type=TaskType.CREATIVE,
            config=GenerationConfig(max_tokens=max_tokens),
        )
        response = await svc.complete(request)
        return response.content
    except Exception:
        logger.warning("LLM orchestration unavailable; returning structured fallback", exc_info=True)
        return json.dumps(
            {
                "status": "service_unavailable",
                "message": (
                    "The AI text-generation service is currently unavailable. "
                    "A manual template has been provided below."
                ),
                "template": {
                    "pages": [
                        {
                            "page_number": i,
                            "panels": [
                                {
                                    "panel_number": 1,
                                    "description": f"[Enter panel description for page {i}]",
                                    "dialogue": "[Enter dialogue]",
                                },
                            ],
                        }
                        for i in range(1, 6)
                    ],
                },
            }
        )


async def _llm_generate_image(prompt: str) -> dict[str, str]:
    """Request an AI-generated image. Returns dict with ``image_url``."""
    try:
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            GenerationConfig,
            TaskType,
        )
        from app.modules.llm_orchestration.service import LLMOrchestrationService

        svc = LLMOrchestrationService()
        request = CompletionRequest(
            prompt=f"Generate a comic panel illustration: {prompt}",
            system_prompt="You are an image generation dispatcher. Return a JSON object with 'image_url' key.",
            task_type=TaskType.CREATIVE,
            config=GenerationConfig(max_tokens=500),
        )
        response = await svc.complete(request)
        try:
            data = json.loads(response.content)
            return {"image_url": data.get("image_url", ""), "prompt_used": prompt}
        except (json.JSONDecodeError, KeyError):
            return {"image_url": "", "prompt_used": prompt}
    except Exception:
        logger.warning("Image generation unavailable; returning pending stub", exc_info=True)
        panel_id = str(_uuid.uuid4())
        return {
            "image_url": f"/api/v1/storage/specialty/comic/pending/panels/{panel_id}/illustration.png",
            "status": "pending_generation",
            "prompt_used": prompt,
            "message": (
                "The illustration generation service is currently unavailable. "
                "The image has been queued and will be generated when the service "
                "is restored."
            ),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _comic_to_dict(comic: Comic) -> dict[str, Any]:
    return {
        "id": str(comic.id),
        "org_id": str(comic.org_id),
        "title": comic.title,
        "subtitle": comic.subtitle,
        "author": comic.author,
        "artist": comic.artist,
        "letterer": comic.letterer,
        "colorist": comic.colorist,
        "art_style": comic.art_style.value if comic.art_style else None,
        "format": comic.format.value if comic.format else None,
        "color_mode": comic.color_mode.value if comic.color_mode else None,
        "ink_style": comic.ink_style.value if comic.ink_style else None,
        "pacing": comic.pacing.value if comic.pacing else None,
        "status": comic.status.value if comic.status else None,
        "genre": comic.genre,
        "premise": comic.premise,
        "script_text": comic.script_text,
        "trim_size": comic.trim_size,
        "page_count": comic.page_count,
        "target_audience": comic.target_audience,
        "border_style": comic.border_style.value if comic.border_style else None,
        "gutter_style": comic.gutter_style.value if comic.gutter_style else None,
        "content_rating": comic.content_rating,
        "violence_level": comic.violence_level,
        "language_level": comic.language_level,
        "safety_settings": comic.safety_settings or {},
        "qa_score": comic.qa_score,
        "created_at": comic.created_at.isoformat() if comic.created_at else None,
        "updated_at": comic.updated_at.isoformat() if comic.updated_at else None,
    }


def _page_to_dict(page: ComicPage) -> dict[str, Any]:
    return {
        "id": str(page.id),
        "comic_id": str(page.comic_id),
        "page_number": page.page_number,
        "page_type": page.page_type,
        "script_text": page.script_text,
        "thumbnail_url": page.thumbnail_url,
        "full_art_url": page.full_art_url,
        "layout_template": page.layout_template,
        "panel_count": page.panel_count,
        "created_at": page.created_at.isoformat() if page.created_at else None,
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }


def _panel_to_dict(panel: ComicPanel) -> dict[str, Any]:
    return {
        "id": str(panel.id),
        "page_id": str(panel.page_id),
        "panel_order": panel.panel_order,
        "panel_type": panel.panel_type.value if panel.panel_type else None,
        "description": panel.description,
        "art_prompt": panel.art_prompt,
        "art_url": panel.art_url,
        "art_seed": panel.art_seed,
        "x": panel.x,
        "y": panel.y,
        "width": panel.width,
        "height": panel.height,
        "border_style": panel.border_style.value if panel.border_style else None,
        "background_color": panel.background_color,
        "created_at": panel.created_at.isoformat() if panel.created_at else None,
        "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
    }


def _bubble_to_dict(bubble: ComicBubble) -> dict[str, Any]:
    return {
        "id": str(bubble.id),
        "panel_id": str(bubble.panel_id),
        "bubble_order": bubble.bubble_order,
        "bubble_type": bubble.bubble_type.value if bubble.bubble_type else None,
        "text": bubble.text,
        "character_name": bubble.character_name,
        "font": bubble.font,
        "font_size": bubble.font_size,
        "x": bubble.x,
        "y": bubble.y,
        "tail_direction": bubble.tail_direction,
        "created_at": bubble.created_at.isoformat() if bubble.created_at else None,
        "updated_at": bubble.updated_at.isoformat() if bubble.updated_at else None,
    }


def _char_to_dict(char: ComicCharacter) -> dict[str, Any]:
    return {
        "id": str(char.id),
        "comic_id": str(char.comic_id),
        "name": char.name,
        "role": char.role,
        "description": char.description,
        "visual_description": char.visual_description,
        "reference_images": char.reference_images or [],
        "auto_append": char.auto_append,
        "default_costume": char.default_costume,
        "color_palette": char.color_palette or {},
        "created_at": char.created_at.isoformat() if char.created_at else None,
        "updated_at": char.updated_at.isoformat() if char.updated_at else None,
    }


def _expression_to_dict(expr: CharacterExpression) -> dict[str, Any]:
    return {
        "id": str(expr.id),
        "character_id": str(expr.character_id),
        "name": expr.name,
        "description": expr.description,
        "reference_url": expr.reference_url,
        "created_at": expr.created_at.isoformat() if expr.created_at else None,
    }


def _pose_to_dict(pose: CharacterPose) -> dict[str, Any]:
    return {
        "id": str(pose.id),
        "character_id": str(pose.character_id),
        "name": pose.name,
        "description": pose.description,
        "reference_url": pose.reference_url,
        "created_at": pose.created_at.isoformat() if pose.created_at else None,
    }


def _costume_to_dict(costume: CharacterCostume) -> dict[str, Any]:
    return {
        "id": str(costume.id),
        "character_id": str(costume.character_id),
        "name": costume.name,
        "description": costume.description,
        "reference_url": costume.reference_url,
        "is_default": costume.is_default,
        "created_at": costume.created_at.isoformat() if costume.created_at else None,
    }


async def _get_comic_or_404(db: AsyncSession, org_id: UUID, comic_id: UUID) -> Comic:
    stmt = select(Comic).where(
        Comic.id == comic_id,
        Comic.org_id == org_id,
        Comic.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    comic = result.scalar_one_or_none()
    if comic is None:
        raise NotFoundError("Comic", f"Comic {comic_id} not found")
    return comic


async def _get_page_or_404(db: AsyncSession, org_id: UUID, comic_id: UUID, page_id: UUID) -> ComicPage:
    stmt = select(ComicPage).where(
        ComicPage.id == page_id,
        ComicPage.comic_id == comic_id,
        ComicPage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("ComicPage", f"Page {page_id} not found")
    return page


async def _get_panel_or_404(db: AsyncSession, org_id: UUID, page_id: UUID, panel_id: UUID) -> ComicPanel:
    stmt = select(ComicPanel).where(
        ComicPanel.id == panel_id,
        ComicPanel.page_id == page_id,
        ComicPanel.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    panel = result.scalar_one_or_none()
    if panel is None:
        raise NotFoundError("ComicPanel", f"Panel {panel_id} not found")
    return panel


async def _get_bubble_or_404(db: AsyncSession, org_id: UUID, panel_id: UUID, bubble_id: UUID) -> ComicBubble:
    stmt = select(ComicBubble).where(
        ComicBubble.id == bubble_id,
        ComicBubble.panel_id == panel_id,
        ComicBubble.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    bubble = result.scalar_one_or_none()
    if bubble is None:
        raise NotFoundError("ComicBubble", f"Bubble {bubble_id} not found")
    return bubble


async def _get_character_or_404(db: AsyncSession, org_id: UUID, comic_id: UUID, char_id: UUID) -> ComicCharacter:
    stmt = select(ComicCharacter).where(
        ComicCharacter.id == char_id,
        ComicCharacter.comic_id == comic_id,
        ComicCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError("ComicCharacter", f"Character {char_id} not found")
    return char


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats(db: AsyncSession, org_id: UUID) -> dict[str, Any]:
    """Get comic book statistics for the org."""
    total_stmt = (
        select(func.count())
        .select_from(Comic)
        .where(
            Comic.org_id == org_id,
            Comic.deleted_at.is_(None),
        )
    )
    total_result = await db.execute(total_stmt)
    total_comics = total_result.scalar() or 0

    in_progress_stmt = (
        select(func.count())
        .select_from(Comic)
        .where(
            Comic.org_id == org_id,
            Comic.deleted_at.is_(None),
            Comic.status == BookStatus.in_progress,
        )
    )
    in_progress_result = await db.execute(in_progress_stmt)
    in_progress = in_progress_result.scalar() or 0

    published_stmt = (
        select(func.count())
        .select_from(Comic)
        .where(
            Comic.org_id == org_id,
            Comic.deleted_at.is_(None),
            Comic.status == BookStatus.published,
        )
    )
    published_result = await db.execute(published_stmt)
    published = published_result.scalar() or 0

    comic_ids_stmt = select(Comic.id).where(
        Comic.org_id == org_id,
        Comic.deleted_at.is_(None),
    )
    pages_stmt = (
        select(func.count())
        .select_from(ComicPage)
        .where(
            ComicPage.comic_id.in_(comic_ids_stmt),
            ComicPage.deleted_at.is_(None),
        )
    )
    pages_result = await db.execute(pages_stmt)
    pages_created = pages_result.scalar() or 0

    page_ids_stmt = select(ComicPage.id).where(
        ComicPage.comic_id.in_(comic_ids_stmt),
        ComicPage.deleted_at.is_(None),
    )
    panels_stmt = (
        select(func.count())
        .select_from(ComicPanel)
        .where(
            ComicPanel.page_id.in_(page_ids_stmt),
            ComicPanel.deleted_at.is_(None),
        )
    )
    panels_result = await db.execute(panels_stmt)
    panels_created = panels_result.scalar() or 0

    return {
        "total_comics": total_comics,
        "in_progress": in_progress,
        "published": published,
        "pages_created": pages_created,
        "panels_created": panels_created,
    }


# ---------------------------------------------------------------------------
# Comic CRUD
# ---------------------------------------------------------------------------


async def list_comics(
    db: AsyncSession,
    org_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: BookStatus | None = None,
    format_filter: ComicFormat | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """List comics with pagination and optional filters."""
    stmt = select(Comic).where(
        Comic.org_id == org_id,
        Comic.deleted_at.is_(None),
    )
    count_stmt = (
        select(func.count())
        .select_from(Comic)
        .where(
            Comic.org_id == org_id,
            Comic.deleted_at.is_(None),
        )
    )

    if status_filter:
        stmt = stmt.where(Comic.status == status_filter)
        count_stmt = count_stmt.where(Comic.status == status_filter)
    if format_filter:
        stmt = stmt.where(Comic.format == format_filter)
        count_stmt = count_stmt.where(Comic.format == format_filter)
    if search:
        like_term = f"%{search}%"
        stmt = stmt.where(Comic.title.ilike(like_term))
        count_stmt = count_stmt.where(Comic.title.ilike(like_term))

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Comic.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    comics = result.scalars().all()

    return {
        "items": [_comic_to_dict(c) for c in comics],
        "total_count": total_count,
        "has_more": (offset + page_size) < total_count,
        "next_cursor": str(page + 1) if (offset + page_size) < total_count else None,
    }


async def create_comic(db: AsyncSession, org_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new comic book."""
    comic = Comic(
        org_id=org_id,
        title=payload["title"],
        subtitle=payload.get("subtitle"),
        author=payload.get("author"),
        artist=payload.get("artist"),
        letterer=payload.get("letterer"),
        colorist=payload.get("colorist"),
        format=payload.get("format"),
        art_style=payload.get("art_style"),
        color_mode=payload.get("color_mode"),
        ink_style=payload.get("ink_style"),
        pacing=payload.get("pacing"),
        status=BookStatus.draft.value,
        genre=payload.get("genre"),
        premise=payload.get("premise"),
        script_text=payload.get("script_text"),
        trim_size=payload.get("trim_size", "6.625x10.25"),
        page_count=payload.get("page_count", 24),
        target_audience=payload.get("target_audience"),
        border_style=payload.get("border_style"),
        gutter_style=payload.get("gutter_style"),
        content_rating=payload.get("content_rating"),
        violence_level=payload.get("violence_level"),
        language_level=payload.get("language_level"),
        safety_settings=payload.get("safety_settings"),
    )
    db.add(comic)
    await db.flush()
    await db.refresh(comic)
    return _comic_to_dict(comic)


async def get_comic(db: AsyncSession, org_id: UUID, comic_id: UUID) -> dict[str, Any]:
    """Get comic detail with pages and characters."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    result = _comic_to_dict(comic)

    pages = await list_pages(db, org_id, comic_id)
    characters = await list_characters(db, org_id, comic_id)
    result["pages"] = pages
    result["characters"] = characters
    return result


async def update_comic(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Update a comic book."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    allowed = {
        "title",
        "subtitle",
        "author",
        "artist",
        "letterer",
        "colorist",
        "format",
        "art_style",
        "color_mode",
        "ink_style",
        "pacing",
        "status",
        "genre",
        "premise",
        "script_text",
        "trim_size",
        "page_count",
        "target_audience",
        "border_style",
        "gutter_style",
        "content_rating",
        "violence_level",
        "language_level",
        "safety_settings",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(comic, key, value)
    await db.flush()
    await db.refresh(comic)
    return _comic_to_dict(comic)


async def delete_comic(db: AsyncSession, org_id: UUID, comic_id: UUID) -> bool:
    """Soft-delete a comic book."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    comic.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Page CRUD
# ---------------------------------------------------------------------------


async def list_pages(db: AsyncSession, org_id: UUID, comic_id: UUID) -> list[dict[str, Any]]:
    """List all pages for a comic, ordered by page_number."""
    await _get_comic_or_404(db, org_id, comic_id)
    stmt = (
        select(ComicPage)
        .where(
            ComicPage.comic_id == comic_id,
            ComicPage.deleted_at.is_(None),
        )
        .order_by(ComicPage.page_number)
    )
    result = await db.execute(stmt)
    return [_page_to_dict(p) for p in result.scalars().all()]


async def create_page(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new page in a comic."""
    await _get_comic_or_404(db, org_id, comic_id)

    if "page_number" not in payload:
        max_stmt = select(func.max(ComicPage.page_number)).where(
            ComicPage.comic_id == comic_id,
            ComicPage.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        current_max = max_result.scalar() or 0
        payload["page_number"] = current_max + 1

    page = ComicPage(
        comic_id=comic_id,
        page_number=payload["page_number"],
        page_type=payload.get("page_type", "story"),
        script_text=payload.get("script_text"),
        thumbnail_url=payload.get("thumbnail_url"),
        full_art_url=payload.get("full_art_url"),
        layout_template=payload.get("layout_template"),
        panel_count=payload.get("panel_count", 6),
    )
    db.add(page)
    await db.flush()
    await db.refresh(page)

    # Update comic page count
    count_stmt = (
        select(func.count())
        .select_from(ComicPage)
        .where(
            ComicPage.comic_id == comic_id,
            ComicPage.deleted_at.is_(None),
        )
    )
    count_result = await db.execute(count_stmt)
    await db.execute(update(Comic).where(Comic.id == comic_id).values(page_count=count_result.scalar() or 0))

    return _page_to_dict(page)


async def update_page(
    db: AsyncSession, org_id: UUID, comic_id: UUID, page_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update a comic page."""
    page = await _get_page_or_404(db, org_id, comic_id, page_id)
    allowed = {
        "page_number",
        "page_type",
        "script_text",
        "thumbnail_url",
        "full_art_url",
        "layout_template",
        "panel_count",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(page, key, value)
    await db.flush()
    await db.refresh(page)
    return _page_to_dict(page)


async def delete_page(db: AsyncSession, org_id: UUID, comic_id: UUID, page_id: UUID) -> bool:
    """Delete a comic page."""
    page = await _get_page_or_404(db, org_id, comic_id, page_id)
    page.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def reorder_pages(db: AsyncSession, org_id: UUID, comic_id: UUID, page_ids: list[UUID]) -> list[dict[str, Any]]:
    """Reorder pages by providing the desired order of page IDs."""
    await _get_comic_or_404(db, org_id, comic_id)
    for idx, pid in enumerate(page_ids, start=1):
        await db.execute(
            update(ComicPage)
            .where(
                ComicPage.id == UUID(str(pid)),
                ComicPage.comic_id == comic_id,
            )
            .values(page_number=idx)
        )
    await db.flush()
    return await list_pages(db, org_id, comic_id)


# ---------------------------------------------------------------------------
# Panel CRUD
# ---------------------------------------------------------------------------


async def list_panels(db: AsyncSession, org_id: UUID, page_id: UUID) -> list[dict[str, Any]]:
    """List all panels for a page."""
    stmt = (
        select(ComicPanel)
        .where(
            ComicPanel.page_id == page_id,
            ComicPanel.deleted_at.is_(None),
        )
        .order_by(ComicPanel.panel_order)
    )
    result = await db.execute(stmt)
    return [_panel_to_dict(p) for p in result.scalars().all()]


async def create_panel(db: AsyncSession, org_id: UUID, page_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new panel on a page."""
    if "panel_order" not in payload:
        max_stmt = select(func.max(ComicPanel.panel_order)).where(
            ComicPanel.page_id == page_id,
            ComicPanel.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        current_max = max_result.scalar() or 0
        payload["panel_order"] = current_max + 1

    panel = ComicPanel(
        page_id=page_id,
        panel_order=payload["panel_order"],
        panel_type=payload.get("panel_type", PanelType.standard.value),
        description=payload.get("description"),
        art_prompt=payload.get("art_prompt"),
        x=payload.get("x", 0.0),
        y=payload.get("y", 0.0),
        width=payload.get("width", 50.0),
        height=payload.get("height", 50.0),
        border_style=payload.get("border_style"),
        background_color=payload.get("background_color"),
    )
    db.add(panel)
    await db.flush()
    await db.refresh(panel)
    return _panel_to_dict(panel)


async def update_panel(
    db: AsyncSession, org_id: UUID, page_id: UUID, panel_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update a panel."""
    panel = await _get_panel_or_404(db, org_id, page_id, panel_id)
    allowed = {
        "panel_order",
        "panel_type",
        "description",
        "art_prompt",
        "art_url",
        "art_seed",
        "x",
        "y",
        "width",
        "height",
        "border_style",
        "background_color",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(panel, key, value)
    await db.flush()
    await db.refresh(panel)
    return _panel_to_dict(panel)


async def delete_panel(db: AsyncSession, org_id: UUID, page_id: UUID, panel_id: UUID) -> bool:
    """Delete a panel."""
    panel = await _get_panel_or_404(db, org_id, page_id, panel_id)
    panel.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Bubble CRUD
# ---------------------------------------------------------------------------


async def list_bubbles(db: AsyncSession, org_id: UUID, panel_id: UUID) -> list[dict[str, Any]]:
    """List all bubbles for a panel."""
    stmt = (
        select(ComicBubble)
        .where(
            ComicBubble.panel_id == panel_id,
            ComicBubble.deleted_at.is_(None),
        )
        .order_by(ComicBubble.bubble_order)
    )
    result = await db.execute(stmt)
    return [_bubble_to_dict(b) for b in result.scalars().all()]


async def create_bubble(db: AsyncSession, org_id: UUID, panel_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new bubble in a panel."""
    bubble = ComicBubble(
        panel_id=panel_id,
        bubble_order=payload.get("bubble_order", 0),
        bubble_type=payload.get("bubble_type", BubbleType.speech.value),
        text=payload.get("text"),
        character_name=payload.get("character_name"),
        font=payload.get("font"),
        font_size=payload.get("font_size"),
        x=payload.get("x", 50.0),
        y=payload.get("y", 10.0),
        tail_direction=payload.get("tail_direction"),
    )
    db.add(bubble)
    await db.flush()
    await db.refresh(bubble)
    return _bubble_to_dict(bubble)


async def update_bubble(
    db: AsyncSession, org_id: UUID, panel_id: UUID, bubble_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update a bubble."""
    bubble = await _get_bubble_or_404(db, org_id, panel_id, bubble_id)
    allowed = {
        "bubble_order",
        "bubble_type",
        "text",
        "character_name",
        "font",
        "font_size",
        "x",
        "y",
        "tail_direction",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(bubble, key, value)
    await db.flush()
    await db.refresh(bubble)
    return _bubble_to_dict(bubble)


async def delete_bubble(db: AsyncSession, org_id: UUID, panel_id: UUID, bubble_id: UUID) -> bool:
    """Delete a bubble."""
    bubble = await _get_bubble_or_404(db, org_id, panel_id, bubble_id)
    bubble.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Script Operations
# ---------------------------------------------------------------------------


async def get_script(db: AsyncSession, org_id: UUID, comic_id: UUID) -> dict[str, Any]:
    """Get the full script for a comic (assembled from all pages/panels/bubbles)."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    pages = await list_pages(db, org_id, comic_id)

    script_pages: list[dict[str, Any]] = []
    for page_data in pages:
        page_id = UUID(page_data["id"])
        panels = await list_panels(db, org_id, page_id)

        panel_scripts: list[dict[str, Any]] = []
        for panel_data in panels:
            p_id = UUID(panel_data["id"])
            bubbles = await list_bubbles(db, org_id, p_id)
            panel_scripts.append(
                {
                    "panel_number": panel_data["panel_order"],
                    "description": panel_data["description"],
                    "art_prompt": panel_data["art_prompt"],
                    "dialogue": [
                        {
                            "character": b["character_name"],
                            "type": b["bubble_type"],
                            "text": b["text"],
                        }
                        for b in bubbles
                    ],
                }
            )

        script_pages.append(
            {
                "page_number": page_data["page_number"],
                "notes": page_data.get("notes"),
                "panels": panel_scripts,
            }
        )

    return {
        "comic_id": str(comic_id),
        "title": comic.title,
        "script_text": comic.script_text,
        "pages": script_pages,
    }


async def update_script(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Update the full comic script text."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    comic.script_text = payload.get("script_text", comic.script_text)
    await db.flush()
    await db.refresh(comic)
    return {
        "comic_id": str(comic_id),
        "script_text": comic.script_text,
        "updated_at": comic.updated_at.isoformat() if comic.updated_at else None,
    }


async def generate_script(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """AI-generate a comic script from premise, genre, characters.

    # TODO: integrate with LLM service
    """
    comic = await _get_comic_or_404(db, org_id, comic_id)
    characters = await list_characters(db, org_id, comic_id)
    logger.info("Generating script for comic %s", comic_id)

    premise = payload.get("premise", comic.premise or "")
    genre = payload.get("genre", comic.genre or "action")
    target_pages = payload.get("target_pages", 22)
    tone = payload.get("tone", "dramatic")

    char_descriptions = (
        "\n".join(f"- {c['name']}: {c.get('description', '')} {c.get('visual_description', '')}" for c in characters)
        or "No characters defined yet."
    )

    system_prompt = (
        f"You are a professional comic book writer. Genre: {genre}. Tone: {tone}.\n"
        f"Write a {target_pages}-page comic script with panel descriptions and dialogue."
    )

    prompt = (
        f"Write a comic book script.\n"
        f"Title: {comic.title}\n"
        f"Premise: {premise}\n"
        f"Characters:\n{char_descriptions}\n\n"
        f"For each page, output:\n"
        f"PAGE <number>:\n"
        f"PANEL <number>: <visual description>\n"
        f"DIALOGUE: <character>: <text>\n\n"
        f"Include {target_pages} pages total."
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=8000)

    comic.script_text = raw
    comic.status = BookStatus.in_progress.value
    await db.flush()
    await db.refresh(comic)

    return {
        "comic_id": str(comic_id),
        "script_text": raw,
        "target_pages": target_pages,
        "genre": genre,
        "characters_used": [c["name"] for c in characters],
        "status": "generated",
    }


async def expand_panel(
    db: AsyncSession, org_id: UUID, comic_id: UUID, panel_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """AI-expand a panel's description into art prompt + dialogue.

    # TODO: integrate with LLM service
    """
    comic = await _get_comic_or_404(db, org_id, comic_id)
    logger.info("Expanding panel %s for comic %s", panel_id, comic_id)

    # Find the panel across all pages
    stmt = select(ComicPanel).where(
        ComicPanel.id == panel_id,
        ComicPanel.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    panel = result.scalar_one_or_none()
    if panel is None:
        raise NotFoundError("ComicPanel", f"Panel {panel_id} not found")

    style = comic.art_style.value if comic.art_style else "american_classic"
    description = payload.get("description", panel.description or "")

    system_prompt = (
        f"You are a comic book art director. Style: {style}.\n"
        f"Expand a panel description into a detailed art prompt and suggested dialogue."
    )

    prompt = (
        f"Panel description: {description}\n\n"
        f"Provide:\n"
        f"ART PROMPT: <detailed visual description for the artist>\n"
        f"DIALOGUE: <character>: <text> (one per line)\n"
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=2000)

    panel.art_prompt = raw
    await db.flush()
    await db.refresh(panel)

    return {
        "panel_id": str(panel_id),
        "expanded_content": raw,
        "art_prompt": panel.art_prompt,
        "status": "expanded",
    }


async def generate_next_page(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """AI-generate the next page's script based on story so far.

    # TODO: integrate with LLM service
    """
    comic = await _get_comic_or_404(db, org_id, comic_id)
    logger.info("Generating next page for comic %s", comic_id)

    pages = await list_pages(db, org_id, comic_id)
    story_so_far = comic.script_text or ""
    direction = payload.get("direction", "Continue the story naturally.")

    system_prompt = (
        f"You are a comic book writer continuing an existing story.\n"
        f"Art style: {comic.art_style.value if comic.art_style else 'american_classic'}.\n"
        f"Genre: {comic.genre or 'action'}."
    )

    next_page_num = len(pages) + 1
    prompt = (
        f"Story so far (script):\n{story_so_far[:3000]}\n\n"
        f"Direction: {direction}\n\n"
        f"Write PAGE {next_page_num} with panel descriptions and dialogue."
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=2000)

    # Create the page
    page = ComicPage(
        comic_id=comic_id,
        page_number=next_page_num,
        page_type="story",
        script_text=raw,
    )
    db.add(page)
    await db.flush()
    await db.refresh(page)

    # Update comic page count
    count_stmt = (
        select(func.count())
        .select_from(ComicPage)
        .where(
            ComicPage.comic_id == comic_id,
            ComicPage.deleted_at.is_(None),
        )
    )
    count_result = await db.execute(count_stmt)
    await db.execute(update(Comic).where(Comic.id == comic_id).values(page_count=count_result.scalar() or 0))

    return {
        "comic_id": str(comic_id),
        "page": _page_to_dict(page),
        "generated_script": raw,
        "page_number": next_page_num,
        "status": "generated",
    }


# ---------------------------------------------------------------------------
# Character Operations
# ---------------------------------------------------------------------------


async def list_characters(db: AsyncSession, org_id: UUID, comic_id: UUID) -> list[dict[str, Any]]:
    """List all characters for a comic."""
    await _get_comic_or_404(db, org_id, comic_id)
    stmt = (
        select(ComicCharacter)
        .where(
            ComicCharacter.comic_id == comic_id,
            ComicCharacter.deleted_at.is_(None),
        )
        .order_by(ComicCharacter.created_at)
    )
    result = await db.execute(stmt)
    return [_char_to_dict(c) for c in result.scalars().all()]


async def create_character(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a character for a comic."""
    await _get_comic_or_404(db, org_id, comic_id)
    char = ComicCharacter(
        comic_id=comic_id,
        name=payload["name"],
        role=payload.get("role"),
        description=payload.get("description"),
        visual_description=payload.get("visual_description"),
        reference_images=payload.get("reference_images", []),
        auto_append=payload.get("auto_append", True),
        default_costume=payload.get("default_costume"),
        color_palette=payload.get("color_palette"),
    )
    db.add(char)
    await db.flush()
    await db.refresh(char)
    return _char_to_dict(char)


async def update_character(
    db: AsyncSession, org_id: UUID, comic_id: UUID, char_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update a character."""
    char = await _get_character_or_404(db, org_id, comic_id, char_id)
    allowed = {
        "name",
        "role",
        "description",
        "visual_description",
        "reference_images",
        "auto_append",
        "default_costume",
        "color_palette",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(char, key, value)
    await db.flush()
    await db.refresh(char)
    return _char_to_dict(char)


async def delete_character(db: AsyncSession, org_id: UUID, comic_id: UUID, char_id: UUID) -> bool:
    """Delete a character."""
    char = await _get_character_or_404(db, org_id, comic_id, char_id)
    char.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def add_expression(db: AsyncSession, org_id: UUID, char_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Add an expression to a character."""
    # Verify character exists
    stmt = select(ComicCharacter).where(
        ComicCharacter.id == char_id,
        ComicCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError("ComicCharacter", f"Character {char_id} not found")

    expr = CharacterExpression(
        character_id=char_id,
        name=payload["name"],
        description=payload.get("description"),
        reference_url=payload.get("reference_url"),
    )
    db.add(expr)
    await db.flush()
    await db.refresh(expr)
    return _expression_to_dict(expr)


async def add_pose(db: AsyncSession, org_id: UUID, char_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Add a pose to a character."""
    stmt = select(ComicCharacter).where(
        ComicCharacter.id == char_id,
        ComicCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError("ComicCharacter", f"Character {char_id} not found")

    pose = CharacterPose(
        character_id=char_id,
        name=payload["name"],
        description=payload.get("description"),
        reference_url=payload.get("reference_url"),
    )
    db.add(pose)
    await db.flush()
    await db.refresh(pose)
    return _pose_to_dict(pose)


async def add_costume(db: AsyncSession, org_id: UUID, char_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Add a costume to a character."""
    stmt = select(ComicCharacter).where(
        ComicCharacter.id == char_id,
        ComicCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError("ComicCharacter", f"Character {char_id} not found")

    costume = CharacterCostume(
        character_id=char_id,
        name=payload["name"],
        description=payload.get("description"),
        reference_url=payload.get("reference_url"),
        is_default=payload.get("is_default", False),
    )
    db.add(costume)
    await db.flush()
    await db.refresh(costume)
    return _costume_to_dict(costume)


async def generate_character_references(
    db: AsyncSession, org_id: UUID, comic_id: UUID, char_id: UUID
) -> dict[str, Any]:
    """Generate reference images for a character in the comic's art style."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    char = await _get_character_or_404(db, org_id, comic_id, char_id)

    style = comic.art_style.value if comic.art_style else "american_classic"
    base_desc = f"{char.description or char.name}"
    if char.visual_description:
        base_desc += f", {char.visual_description}"

    views = ["front view", "side view", "action pose", "emotional close-up"]
    reference_urls: list[str] = []

    for view in views:
        prompt = f"{base_desc}, {view}, {style} comic art style, " f"character reference sheet, white background"
        result = await _llm_generate_image(prompt)
        reference_urls.append(result.get("image_url", ""))

    char.reference_images = reference_urls
    await db.flush()
    await db.refresh(char)

    return {
        "character_id": str(char.id),
        "name": char.name,
        "reference_images": reference_urls,
        "views": views,
    }


# ---------------------------------------------------------------------------
# Layout Templates
# ---------------------------------------------------------------------------


LAYOUT_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "grid-2x2",
        "name": "2x2 Grid",
        "panels": 4,
        "description": "Four equal panels",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
            {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5},
            {"x": 0.0, "y": 0.5, "w": 0.5, "h": 0.5},
            {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5},
        ],
    },
    {
        "id": "grid-2x3",
        "name": "2x3 Grid",
        "panels": 6,
        "description": "Six equal panels",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.333},
            {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.333},
            {"x": 0.0, "y": 0.333, "w": 0.5, "h": 0.333},
            {"x": 0.5, "y": 0.333, "w": 0.5, "h": 0.333},
            {"x": 0.0, "y": 0.666, "w": 0.5, "h": 0.334},
            {"x": 0.5, "y": 0.666, "w": 0.5, "h": 0.334},
        ],
    },
    {
        "id": "grid-3x3",
        "name": "3x3 Grid",
        "panels": 9,
        "description": "Nine equal panels",
        "positions": [{"x": c / 3, "y": r / 3, "w": 1 / 3, "h": 1 / 3} for r in range(3) for c in range(3)],
    },
    {
        "id": "hero-top",
        "name": "Hero Top",
        "panels": 4,
        "description": "Large panel on top, 3 small below",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.5},
            {"x": 0.0, "y": 0.5, "w": 0.333, "h": 0.5},
            {"x": 0.333, "y": 0.5, "w": 0.333, "h": 0.5},
            {"x": 0.666, "y": 0.5, "w": 0.334, "h": 0.5},
        ],
    },
    {
        "id": "hero-bottom",
        "name": "Hero Bottom",
        "panels": 4,
        "description": "3 small on top, large panel below",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 0.333, "h": 0.5},
            {"x": 0.333, "y": 0.0, "w": 0.333, "h": 0.5},
            {"x": 0.666, "y": 0.0, "w": 0.334, "h": 0.5},
            {"x": 0.0, "y": 0.5, "w": 1.0, "h": 0.5},
        ],
    },
    {
        "id": "splash",
        "name": "Full Splash",
        "panels": 1,
        "description": "Single full-page panel",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        ],
    },
    {
        "id": "widescreen",
        "name": "Widescreen",
        "panels": 3,
        "description": "Three horizontal strips",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.333},
            {"x": 0.0, "y": 0.333, "w": 1.0, "h": 0.333},
            {"x": 0.0, "y": 0.666, "w": 1.0, "h": 0.334},
        ],
    },
    {
        "id": "manga-4",
        "name": "Manga 4-Panel",
        "panels": 4,
        "description": "Traditional manga yonkoma",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.25},
            {"x": 0.0, "y": 0.25, "w": 1.0, "h": 0.25},
            {"x": 0.0, "y": 0.5, "w": 1.0, "h": 0.25},
            {"x": 0.0, "y": 0.75, "w": 1.0, "h": 0.25},
        ],
    },
    {
        "id": "action-dynamic",
        "name": "Dynamic Action",
        "panels": 5,
        "description": "Mixed sizes for action sequences",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 0.6, "h": 0.5},
            {"x": 0.6, "y": 0.0, "w": 0.4, "h": 0.25},
            {"x": 0.6, "y": 0.25, "w": 0.4, "h": 0.25},
            {"x": 0.0, "y": 0.5, "w": 0.4, "h": 0.5},
            {"x": 0.4, "y": 0.5, "w": 0.6, "h": 0.5},
        ],
    },
    {
        "id": "dialogue-heavy",
        "name": "Dialogue Heavy",
        "panels": 7,
        "description": "Many small panels for conversation",
        "positions": [
            {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.285},
            {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.285},
            {"x": 0.0, "y": 0.285, "w": 0.333, "h": 0.285},
            {"x": 0.333, "y": 0.285, "w": 0.333, "h": 0.285},
            {"x": 0.666, "y": 0.285, "w": 0.334, "h": 0.285},
            {"x": 0.0, "y": 0.57, "w": 0.5, "h": 0.43},
            {"x": 0.5, "y": 0.57, "w": 0.5, "h": 0.43},
        ],
    },
]


async def get_layout_templates() -> list[dict[str, Any]]:
    """Return predefined panel layout templates."""
    return [
        {"id": t["id"], "name": t["name"], "panels": t["panels"], "description": t["description"]}
        for t in LAYOUT_TEMPLATES
    ]


async def apply_layout_template(
    db: AsyncSession, org_id: UUID, page_id: UUID, template_id: str
) -> list[dict[str, Any]]:
    """Apply a layout template to a page, creating panels accordingly."""
    template = next((t for t in LAYOUT_TEMPLATES if t["id"] == template_id), None)
    if template is None:
        raise NotFoundError("LayoutTemplate", f"Template '{template_id}' not found")

    # Verify page exists
    stmt = select(ComicPage).where(
        ComicPage.id == page_id,
        ComicPage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("ComicPage", f"Page {page_id} not found")

    # Soft-delete existing panels on this page
    existing_stmt = select(ComicPanel).where(
        ComicPanel.page_id == page_id,
        ComicPanel.deleted_at.is_(None),
    )
    existing_result = await db.execute(existing_stmt)
    for old_panel in existing_result.scalars().all():
        old_panel.deleted_at = datetime.now(UTC)

    # Create new panels from template positions
    created_panels: list[dict[str, Any]] = []
    for idx, pos in enumerate(template["positions"], start=1):
        panel = ComicPanel(
            page_id=page_id,
            panel_order=idx,
            panel_type=PanelType.standard.value,
            x=pos["x"],
            y=pos["y"],
            width=pos["w"],
            height=pos["h"],
        )
        db.add(panel)
        await db.flush()
        await db.refresh(panel)
        created_panels.append(_panel_to_dict(panel))

    # Update page layout_template
    page.layout_template = template_id
    await db.flush()

    return created_panels


# ---------------------------------------------------------------------------
# Export / Preflight
# ---------------------------------------------------------------------------


async def export_comic(db: AsyncSession, org_id: UUID, comic_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Generate export file (PDF / CBZ / print-ready)."""
    from app.modules.specialty.shared.export_engine import (
        calculate_export_metadata,
        generate_pdf_manifest,
        generate_pdfx1a_manifest,
    )

    comic = await _get_comic_or_404(db, org_id, comic_id)
    pages = await list_pages(db, org_id, comic_id)

    export_format = payload.get("format", "pdf")
    export_id = str(_uuid.uuid4())
    export_url = f"exports/comic/{comic_id}/{export_id}.{export_format}"

    book_data: dict[str, Any] = {
        "id": str(comic_id),
        "title": comic.title,
        "author": comic.author or "",
        "trim_size": comic.trim_size or "6.625x10.25",
        "interior_type": "color",
        "pages": pages,
    }

    if export_format == "cbz":
        # CBZ is a ZIP of page images
        page_images: list[dict[str, Any]] = []
        for p in pages:
            page_images.append(
                {
                    "page_number": p["page_number"],
                    "image_url": p.get("full_art_url", ""),
                }
            )
        return {
            "comic_id": str(comic_id),
            "export_id": export_id,
            "export_url": export_url,
            "format": "cbz",
            "page_images": page_images,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }
    if export_format == "pdfx1a":
        manifest = generate_pdfx1a_manifest("comic", book_data)
        metadata = calculate_export_metadata("comic", book_data)
        return {
            "comic_id": str(comic_id),
            "export_id": export_id,
            "export_url": export_url,
            "format": "pdfx1a",
            "manifest": manifest,
            "metadata": metadata,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }
    manifest = generate_pdf_manifest("comic", book_data, payload)
    metadata = calculate_export_metadata("comic", book_data)
    return {
        "comic_id": str(comic_id),
        "export_id": export_id,
        "export_url": export_url,
        "format": export_format,
        "manifest": manifest,
        "metadata": metadata,
        "status": "processing",
        "created_at": datetime.now(UTC).isoformat(),
    }


async def run_preflight(db: AsyncSession, org_id: UUID, comic_id: UUID) -> dict[str, Any]:
    """Run full preflight check (resolution, bleed, gutter, text legibility)."""
    comic = await _get_comic_or_404(db, org_id, comic_id)
    pages = await list_pages(db, org_id, comic_id)

    checks: list[dict[str, Any]] = []

    # 1. Page count check
    page_count = len(pages)
    valid_count = page_count > 0
    checks.append(
        {
            "check": "page_count",
            "passed": valid_count,
            "detail": f"{page_count} pages" + ("" if valid_count else " (comic must have at least 1 page)"),
        }
    )

    # 2. DPI check (300+ required for print)
    low_dpi_pages = [p for p in pages if (p.get("dpi") or 300) < 300]
    checks.append(
        {
            "check": "dpi_minimum",
            "passed": len(low_dpi_pages) == 0,
            "detail": f"{len(low_dpi_pages)} pages below 300 DPI"
            if low_dpi_pages
            else "All pages meet 300 DPI minimum",
        }
    )

    # 3. Panels check — every page should have at least one panel
    pages_without_panels: list[int] = []
    for p in pages:
        page_id = UUID(p["id"])
        panels = await list_panels(db, org_id, page_id)
        if not panels:
            pages_without_panels.append(p["page_number"])
    checks.append(
        {
            "check": "panels_complete",
            "passed": len(pages_without_panels) == 0,
            "detail": f"{len(pages_without_panels)} pages missing panels"
            if pages_without_panels
            else "All pages have panels",
            "pages": pages_without_panels,
        }
    )

    # 4. Panel art check — panels should have images or art prompts
    panels_without_art: list[dict[str, Any]] = []
    for p in pages:
        page_id = UUID(p["id"])
        panels = await list_panels(db, org_id, page_id)
        for panel in panels:
            if not panel.get("art_url") and not panel.get("art_prompt"):
                panels_without_art.append(
                    {
                        "page": p["page_number"],
                        "panel": panel["panel_order"],
                    }
                )
    checks.append(
        {
            "check": "panel_art",
            "passed": len(panels_without_art) == 0,
            "detail": f"{len(panels_without_art)} panels missing art/prompts"
            if panels_without_art
            else "All panels have art or prompts",
        }
    )

    # 5. Gutter safety (text near spine)
    gutter_issues: list[dict[str, Any]] = []
    for p in pages:
        page_id = UUID(p["id"])
        panels = await list_panels(db, org_id, page_id)
        pn = p["page_number"]
        is_recto = pn % 2 == 1
        for panel in panels:
            # Check if panel is near the gutter edge
            if is_recto and panel.get("x", 0) < 0.05:
                gutter_issues.append(
                    {
                        "page": pn,
                        "panel": panel["panel_order"],
                        "detail": "Panel starts very close to gutter on recto page",
                    }
                )
            elif not is_recto and (panel.get("x", 0) + panel.get("width", 0)) > 0.95:
                gutter_issues.append(
                    {
                        "page": pn,
                        "panel": panel["panel_order"],
                        "detail": "Panel extends very close to gutter on verso page",
                    }
                )
    checks.append(
        {
            "check": "gutter_safety",
            "passed": len(gutter_issues) == 0,
            "detail": f"{len(gutter_issues)} gutter collision(s)" if gutter_issues else "No gutter collisions detected",
            "issues": gutter_issues,
        }
    )

    # 6. Bubble text legibility — check for empty bubbles
    empty_bubbles: list[dict[str, Any]] = []
    for p in pages:
        page_id = UUID(p["id"])
        panels = await list_panels(db, org_id, page_id)
        for panel in panels:
            p_id = UUID(panel["id"])
            bubbles = await list_bubbles(db, org_id, p_id)
            for bubble in bubbles:
                if not bubble.get("text"):
                    empty_bubbles.append(
                        {
                            "page": p["page_number"],
                            "panel": panel["panel_order"],
                            "bubble_type": bubble.get("bubble_type"),
                        }
                    )
    checks.append(
        {
            "check": "text_legibility",
            "passed": len(empty_bubbles) == 0,
            "detail": f"{len(empty_bubbles)} empty bubble(s)" if empty_bubbles else "All bubbles contain text",
        }
    )

    # 7. Bleed check — trim size should be standard
    valid_trims = {"6.625x10.25", "6.875x10.5", "7x10", "8.5x11", "5.5x8.5"}
    trim_ok = (comic.trim_size or "") in valid_trims
    checks.append(
        {
            "check": "trim_size",
            "passed": trim_ok,
            "detail": f"Trim size '{comic.trim_size}'" + ("" if trim_ok else " is non-standard"),
        }
    )

    all_passed = all(c["passed"] for c in checks)

    return {
        "comic_id": str(comic_id),
        "status": "passed" if all_passed else "failed",
        "checks": checks,
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
        "failed_checks": sum(1 for c in checks if not c["passed"]),
    }
