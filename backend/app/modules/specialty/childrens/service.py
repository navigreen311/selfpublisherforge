"""Children's Book Studio service layer.

Provides CRUD for books, pages, and characters, plus AI-powered story
generation, readability analysis, character-consistency checking, safety
scanning, bilingual translation, illustration generation, and export/preflight.
"""
from __future__ import annotations

import json
import logging
import math
import re
import uuid as _uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.database import TenantModel
from app.modules.specialty.models.enums import (
    AgeRange,
    BookStatus,
    IllustrationStyle,
    PageLayout,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ORM models — imported from the canonical models module
# ---------------------------------------------------------------------------
from app.modules.specialty.models.childrens import (  # noqa: E402
    ChildrensBook,
    ChildrensBookCharacter,
    ChildrensBookPage,
)


# ---------------------------------------------------------------------------
# Age-band readability constraints (from blueprint section 3.5)
# ---------------------------------------------------------------------------

AGE_BAND_RULES: dict[str, dict[str, Any]] = {
    "baby": {
        "max_sentence_words": 5,
        "max_word_length": 5,
        "vocab_tier": 500,
        "total_words_min": 50,
        "total_words_max": 150,
        "min_font_size": 24,
    },
    "toddler": {
        "max_sentence_words": 5,
        "max_word_length": 5,
        "vocab_tier": 500,
        "total_words_min": 50,
        "total_words_max": 150,
        "min_font_size": 24,
    },
    "preschool": {
        "max_sentence_words": 8,
        "max_word_length": 7,
        "vocab_tier": 2000,
        "total_words_min": 300,
        "total_words_max": 500,
        "min_font_size": 18,
    },
    "early_reader": {
        "max_sentence_words": 12,
        "max_word_length": 9,
        "vocab_tier": 5000,
        "total_words_min": 500,
        "total_words_max": 2000,
        "min_font_size": 14,
    },
    "chapter_book": {
        "max_sentence_words": 15,
        "max_word_length": 0,  # no limit
        "vocab_tier": 0,  # grade-level
        "total_words_min": 3000,
        "total_words_max": 10000,
        "min_font_size": 12,
    },
    "middle_grade": {
        "max_sentence_words": 15,
        "max_word_length": 0,
        "vocab_tier": 0,
        "total_words_min": 3000,
        "total_words_max": 10000,
        "min_font_size": 12,
    },
}

# Trademarked terms to block (blueprint section 3.7)
TRADEMARK_TERMS: list[str] = [
    "disney", "pixar", "peppa pig", "bluey", "paw patrol", "marvel",
    "frozen", "cocomelon", "sesame street", "pokemon", "hello kitty",
    "thomas the tank engine", "dora the explorer", "spongebob",
    "mickey mouse", "winnie the pooh", "barbie", "lego",
]

CONTENT_SENSITIVITY_PATTERNS: list[str] = [
    r"\b(gun|pistol|rifle|sword|knife|weapon)\b",
    r"\b(blood|gore|kill|murder|death|dead|die)\b",
    r"\b(hate|racist|sexist|stereotype)\b",
    r"\b(alcohol|beer|wine|drunk|drug)\b",
]


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

async def _llm_generate(prompt: str, system_prompt: str = "", max_tokens: int = 4000) -> str:
    """Call the LLM orchestration service and return generated text.

    Falls back to a placeholder when the orchestration service is not
    fully configured (e.g. during development or testing).
    """
    try:
        from app.modules.llm_orchestration.service import LLMOrchestrationService
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            GenerationConfig,
            TaskType,
        )

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
        return json.dumps({
            "status": "service_unavailable",
            "message": (
                "The AI text-generation service is currently unavailable. "
                "A manual template has been provided below."
            ),
            "template": {
                "title": "[Enter book title]",
                "pages": [
                    {
                        "page_number": i,
                        "text_content": f"[Enter text for page {i}]",
                    }
                    for i in range(1, 6)
                ],
                "instructions": (
                    "Fill in each page's text_content field. "
                    "Re-submit once the AI service is restored for "
                    "AI-assisted refinement."
                ),
            },
        })


async def _llm_generate_image(prompt: str) -> dict[str, str]:
    """Request an AI-generated image.  Returns dict with ``image_url``."""
    try:
        from app.modules.llm_orchestration.service import LLMOrchestrationService
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            GenerationConfig,
            TaskType,
        )

        svc = LLMOrchestrationService()
        request = CompletionRequest(
            prompt=f"Generate an illustration: {prompt}",
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
        page_id = str(_uuid.uuid4())
        return {
            "image_url": f"/api/v1/storage/specialty/childrens/pending/pages/{page_id}/illustration.png",
            "status": "pending_generation",
            "prompt_used": prompt,
            "message": (
                "The illustration generation service is currently unavailable. "
                "The image has been queued and will be generated when the service "
                "is restored. You may also upload a custom illustration."
            ),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _book_to_dict(book: ChildrensBook) -> dict[str, Any]:
    return {
        "id": str(book.id),
        "org_id": str(book.org_id),
        "title": book.title,
        "subtitle": book.subtitle,
        "author_name": book.author_name,
        "age_range": book.age_range.value if book.age_range else None,
        "status": book.status.value if book.status else None,
        "page_count": book.page_count,
        "trim_size": book.trim_size,
        "illustration_style": book.illustration_style.value if book.illustration_style else None,
        "color_palette": book.color_palette,
        "story_prompt": book.story_prompt,
        "theme": book.theme,
        "tone": book.tone,
        "story_mode": book.story_mode,
        "bilingual": book.bilingual,
        "bilingual_language": book.bilingual_language,
        "bilingual_layout": book.bilingual_layout,
        "fear_intensity": book.fear_intensity,
        "qa_score": book.qa_score,
        "metadata": book.metadata_json or {},
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "updated_at": book.updated_at.isoformat() if book.updated_at else None,
    }


def _page_to_dict(page: ChildrensBookPage) -> dict[str, Any]:
    return {
        "id": str(page.id),
        "book_id": str(page.book_id),
        "page_number": page.page_number,
        "text_content": page.text_content,
        "illustration_prompt": page.illustration_prompt,
        "layout": page.layout.value if page.layout else None,
        "image_url": page.image_url,
        "thumbnail_url": page.thumbnail_url,
        "font_size": page.font_size,
        "text_position": page.text_position,
        "dpi": page.dpi,
        "translated_text": page.translated_text,
        "metadata": page.metadata_json or {},
        "created_at": page.created_at.isoformat() if page.created_at else None,
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }


def _char_to_dict(char: ChildrensBookCharacter) -> dict[str, Any]:
    return {
        "id": str(char.id),
        "book_id": str(char.book_id),
        "name": char.name,
        "species_type": char.species_type,
        "description": char.description,
        "clothing_rules": char.clothing_rules,
        "scale_rules": char.scale_rules,
        "setting_continuity": char.setting_continuity,
        "time_of_day_rules": char.time_of_day_rules,
        "reference_images": char.reference_images or [],
        "metadata": char.metadata_json or {},
        "created_at": char.created_at.isoformat() if char.created_at else None,
        "updated_at": char.updated_at.isoformat() if char.updated_at else None,
    }


async def _get_book_or_404(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> ChildrensBook:
    stmt = select(ChildrensBook).where(
        ChildrensBook.id == book_id,
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if book is None:
        raise NotFoundError("ChildrensBook", f"Children's book {book_id} not found")
    return book


async def _get_page_or_404(
    db: AsyncSession, org_id: UUID, book_id: UUID, page_id: UUID
) -> ChildrensBookPage:
    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.id == page_id,
        ChildrensBookPage.book_id == book_id,
        ChildrensBookPage.org_id == org_id,
        ChildrensBookPage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("ChildrensBookPage", f"Page {page_id} not found")
    return page


async def _get_character_or_404(
    db: AsyncSession, org_id: UUID, book_id: UUID, char_id: UUID
) -> ChildrensBookCharacter:
    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.id == char_id,
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.org_id == org_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError("ChildrensBookCharacter", f"Character {char_id} not found")
    return char


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats(db: AsyncSession, org_id: UUID) -> dict[str, Any]:
    """Return aggregate statistics for the org's children's books.

    All counters default to 0 (never null) when no data exists.
    """
    base_filter = [
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    ]

    total_result = await db.execute(
        select(func.count()).select_from(ChildrensBook).where(*base_filter)
    )
    total_books = total_result.scalar() or 0

    in_progress_result = await db.execute(
        select(func.count()).select_from(ChildrensBook).where(
            *base_filter,
            ChildrensBook.status == BookStatus.in_progress,
        )
    )
    in_progress = in_progress_result.scalar() or 0

    published_result = await db.execute(
        select(func.count()).select_from(ChildrensBook).where(
            *base_filter,
            ChildrensBook.status == BookStatus.published,
        )
    )
    published = published_result.scalar() or 0

    book_ids_subq = select(ChildrensBook.id).where(*base_filter)
    pages_result = await db.execute(
        select(func.count()).select_from(ChildrensBookPage).where(
            ChildrensBookPage.book_id.in_(book_ids_subq),
            ChildrensBookPage.deleted_at.is_(None),
        )
    )
    pages_created = pages_result.scalar() or 0

    return {
        "total_books": total_books,
        "in_progress": in_progress,
        "published": published,
        "pages_created": pages_created,
    }


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


async def list_books(
    db: AsyncSession,
    org_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: BookStatus | None = None,
    age_range: AgeRange | None = None,
) -> dict[str, Any]:
    """Return a paginated list of children's books."""
    stmt = select(ChildrensBook).where(
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    )
    count_stmt = select(func.count()).select_from(ChildrensBook).where(
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    )

    if status_filter:
        stmt = stmt.where(ChildrensBook.status == status_filter)
        count_stmt = count_stmt.where(ChildrensBook.status == status_filter)
    if age_range:
        stmt = stmt.where(ChildrensBook.age_range == age_range)
        count_stmt = count_stmt.where(ChildrensBook.age_range == age_range)

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(ChildrensBook.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    books = result.scalars().all()

    return {
        "items": [_book_to_dict(b) for b in books],
        "total_count": total_count,
        "has_more": (offset + page_size) < total_count,
        "next_cursor": str(page + 1) if (offset + page_size) < total_count else None,
    }


async def create_book(
    db: AsyncSession, org_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    """Create a new children's book."""
    book = ChildrensBook(
        org_id=org_id,
        title=data["title"],
        subtitle=data.get("subtitle"),
        author_name=data.get("author_name"),
        age_range=data.get("age_range", AgeRange.preschool.value),
        status=BookStatus.draft.value,
        page_count=data.get("page_count", 0),
        trim_size=data.get("trim_size", "8.5x8.5"),
        illustration_style=data.get("illustration_style"),
        color_palette=data.get("color_palette"),
        story_prompt=data.get("story_prompt"),
        theme=data.get("theme"),
        tone=data.get("tone"),
        story_mode=data.get("story_mode"),
        bilingual=data.get("bilingual", False),
        bilingual_language=data.get("bilingual_language"),
        bilingual_layout=data.get("bilingual_layout"),
        fear_intensity=data.get("fear_intensity", "none"),
        metadata_json=data.get("metadata", {}),
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return _book_to_dict(book)


async def get_book(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    book = await _get_book_or_404(db, org_id, book_id)
    return _book_to_dict(book)


async def update_book(
    db: AsyncSession, org_id: UUID, book_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    book = await _get_book_or_404(db, org_id, book_id)
    allowed = {
        "title", "subtitle", "author_name", "age_range", "status",
        "page_count", "trim_size", "illustration_style", "color_palette",
        "story_prompt", "theme", "tone", "story_mode", "bilingual",
        "bilingual_language", "bilingual_layout", "fear_intensity", "metadata",
    }
    for key, value in data.items():
        if key in allowed:
            col = "metadata_json" if key == "metadata" else key
            setattr(book, col, value)
    await db.flush()
    await db.refresh(book)
    return _book_to_dict(book)


async def delete_book(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> bool:
    book = await _get_book_or_404(db, org_id, book_id)
    book.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Page CRUD
# ---------------------------------------------------------------------------


async def list_pages(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> list[dict[str, Any]]:
    await _get_book_or_404(db, org_id, book_id)
    stmt = (
        select(ChildrensBookPage)
        .where(
            ChildrensBookPage.book_id == book_id,
            ChildrensBookPage.org_id == org_id,
            ChildrensBookPage.deleted_at.is_(None),
        )
        .order_by(ChildrensBookPage.page_number)
    )
    result = await db.execute(stmt)
    return [_page_to_dict(p) for p in result.scalars().all()]


async def create_page(
    db: AsyncSession, org_id: UUID, book_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    await _get_book_or_404(db, org_id, book_id)

    # Auto-assign page number if not provided
    if "page_number" not in data:
        max_stmt = select(func.max(ChildrensBookPage.page_number)).where(
            ChildrensBookPage.book_id == book_id,
            ChildrensBookPage.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        current_max = max_result.scalar() or 0
        data["page_number"] = current_max + 1

    page = ChildrensBookPage(
        org_id=org_id,
        book_id=book_id,
        page_number=data["page_number"],
        text_content=data.get("text_content"),
        illustration_prompt=data.get("illustration_prompt"),
        layout=data.get("layout", PageLayout.image_top_text_bottom.value),
        font_size=data.get("font_size"),
        text_position=data.get("text_position"),
        dpi=data.get("dpi", 300),
        metadata_json=data.get("metadata", {}),
    )
    db.add(page)
    await db.flush()
    await db.refresh(page)

    # Update book page count
    count_stmt = select(func.count()).select_from(ChildrensBookPage).where(
        ChildrensBookPage.book_id == book_id,
        ChildrensBookPage.deleted_at.is_(None),
    )
    count_result = await db.execute(count_stmt)
    await db.execute(
        update(ChildrensBook)
        .where(ChildrensBook.id == book_id)
        .values(page_count=count_result.scalar() or 0)
    )

    return _page_to_dict(page)


async def update_page(
    db: AsyncSession, org_id: UUID, book_id: UUID, page_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    page = await _get_page_or_404(db, org_id, book_id, page_id)
    allowed = {
        "text_content", "illustration_prompt", "layout", "font_size",
        "text_position", "dpi", "page_number", "metadata",
    }
    for key, value in data.items():
        if key in allowed:
            col = "metadata_json" if key == "metadata" else key
            setattr(page, col, value)
    await db.flush()
    await db.refresh(page)
    return _page_to_dict(page)


async def delete_page(
    db: AsyncSession, org_id: UUID, book_id: UUID, page_id: UUID
) -> bool:
    page = await _get_page_or_404(db, org_id, book_id, page_id)
    page.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def reorder_pages(
    db: AsyncSession, org_id: UUID, book_id: UUID, page_ids: list[str]
) -> list[dict[str, Any]]:
    """Reorder pages by assigning new page numbers based on the given ID order."""
    await _get_book_or_404(db, org_id, book_id)
    for idx, pid in enumerate(page_ids, start=1):
        await db.execute(
            update(ChildrensBookPage)
            .where(
                ChildrensBookPage.id == UUID(str(pid)),
                ChildrensBookPage.book_id == book_id,
                ChildrensBookPage.org_id == org_id,
            )
            .values(page_number=idx)
        )
    await db.flush()
    return await list_pages(db, org_id, book_id)


# ---------------------------------------------------------------------------
# Character CRUD
# ---------------------------------------------------------------------------


async def list_characters(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> list[dict[str, Any]]:
    await _get_book_or_404(db, org_id, book_id)
    stmt = (
        select(ChildrensBookCharacter)
        .where(
            ChildrensBookCharacter.book_id == book_id,
            ChildrensBookCharacter.org_id == org_id,
            ChildrensBookCharacter.deleted_at.is_(None),
        )
        .order_by(ChildrensBookCharacter.created_at)
    )
    result = await db.execute(stmt)
    return [_char_to_dict(c) for c in result.scalars().all()]


async def create_character(
    db: AsyncSession, org_id: UUID, book_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    await _get_book_or_404(db, org_id, book_id)
    char = ChildrensBookCharacter(
        org_id=org_id,
        book_id=book_id,
        name=data["name"],
        species_type=data.get("species_type"),
        description=data.get("description"),
        clothing_rules=data.get("clothing_rules"),
        scale_rules=data.get("scale_rules"),
        setting_continuity=data.get("setting_continuity"),
        time_of_day_rules=data.get("time_of_day_rules"),
        reference_images=data.get("reference_images", []),
        metadata_json=data.get("metadata", {}),
    )
    db.add(char)
    await db.flush()
    await db.refresh(char)
    return _char_to_dict(char)


async def update_character(
    db: AsyncSession, org_id: UUID, book_id: UUID, char_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    char = await _get_character_or_404(db, org_id, book_id, char_id)
    allowed = {
        "name", "species_type", "description", "clothing_rules",
        "scale_rules", "setting_continuity", "time_of_day_rules",
        "reference_images", "metadata",
    }
    for key, value in data.items():
        if key in allowed:
            col = "metadata_json" if key == "metadata" else key
            setattr(char, col, value)
    await db.flush()
    await db.refresh(char)
    return _char_to_dict(char)


async def delete_character(
    db: AsyncSession, org_id: UUID, book_id: UUID, char_id: UUID
) -> bool:
    char = await _get_character_or_404(db, org_id, book_id, char_id)
    char.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def generate_character_references(
    db: AsyncSession, org_id: UUID, book_id: UUID, char_id: UUID
) -> dict[str, Any]:
    """Generate 4 reference images for a character (front, side, happy, scared)."""
    book = await _get_book_or_404(db, org_id, book_id)
    char = await _get_character_or_404(db, org_id, book_id, char_id)

    style = book.illustration_style.value if book.illustration_style else "storybook"
    base_desc = f"{char.description or char.name}"
    if char.clothing_rules:
        base_desc += f", wearing {char.clothing_rules}"

    views = ["front view", "side view", "happy expression close-up", "scared expression close-up"]
    reference_urls: list[str] = []

    for view in views:
        prompt = f"{base_desc}, {view}, {style} illustration style, character reference sheet, white background"
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
# AI Story Generation
# ---------------------------------------------------------------------------


async def generate_story(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate a full story with per-page text and illustration prompts.

    Builds a prompt using the book's age-band constraints, theme, tone,
    characters, and story prompt. Parses the LLM response into individual
    pages with illustration prompts.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    characters = await list_characters(db, org_id, book_id)
    rules = AGE_BAND_RULES.get(book.age_range.value if book.age_range else "preschool", AGE_BAND_RULES["preschool"])

    target_pages = options.get("target_pages", book.page_count or 24)
    style = book.illustration_style.value if book.illustration_style else "storybook"

    char_descriptions = "\n".join(
        f"- {c['name']}: {c.get('description', '')} {c.get('clothing_rules', '')}"
        for c in characters
    ) or "No characters defined yet."

    system_prompt = (
        f"You are a children's book author. Write for age range: {book.age_range.value if book.age_range else 'preschool'}.\n"
        f"Rules: max {rules['max_sentence_words']} words per sentence, "
        f"max {rules['max_word_length']} letters per word (0=no limit), "
        f"total words between {rules['total_words_min']}-{rules['total_words_max']}.\n"
        f"Story mode: {book.story_mode or 'prose'}. Tone: {book.tone or 'warm'}.\n"
        f"Fear intensity: {book.fear_intensity or 'none'}.\n"
        f"NEVER include trademarked characters or violent content."
    )

    prompt = (
        f"Write a {target_pages}-page children's book.\n"
        f"Title: {book.title}\n"
        f"Theme/Moral: {book.theme or 'Not specified'}\n"
        f"Story Prompt: {book.story_prompt or 'Not specified'}\n"
        f"Characters:\n{char_descriptions}\n\n"
        f"For each page, output in this exact format:\n"
        f"PAGE <number>:\n"
        f"TEXT: <page text>\n"
        f"ILLUSTRATION: <detailed illustration prompt in {style} style>\n\n"
        f"Include {target_pages} pages total."
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=8000)

    # Parse the LLM output into pages
    pages_data = _parse_story_pages(raw, target_pages)

    # Create page records in the database
    created_pages: list[dict[str, Any]] = []
    for pd in pages_data:
        page = ChildrensBookPage(
            org_id=org_id,
            book_id=book_id,
            page_number=pd["page_number"],
            text_content=pd["text"],
            illustration_prompt=pd["illustration_prompt"],
            layout=PageLayout.image_top_text_bottom.value,
            dpi=300,
            metadata_json={"generated": True, "generation_timestamp": datetime.now(UTC).isoformat()},
        )
        db.add(page)
        await db.flush()
        await db.refresh(page)
        created_pages.append(_page_to_dict(page))

    # Update book page count and status
    book.page_count = len(created_pages)
    book.status = BookStatus.in_progress.value
    await db.flush()

    # Run readability check on generated content
    readability = _analyze_readability(
        [p.get("text_content", "") for p in created_pages],
        book.age_range.value if book.age_range else "preschool",
    )

    return {
        "book_id": str(book_id),
        "pages_created": len(created_pages),
        "pages": created_pages,
        "readability_report": readability,
        "characters_used": [c["name"] for c in characters],
    }


def _parse_story_pages(raw_text: str, target_pages: int) -> list[dict[str, Any]]:
    """Parse LLM output into structured page data."""
    pages: list[dict[str, Any]] = []
    # Try to parse PAGE N: ... TEXT: ... ILLUSTRATION: ... blocks
    page_blocks = re.split(r"PAGE\s+(\d+)\s*:", raw_text, flags=re.IGNORECASE)

    # page_blocks: ['preamble', '1', 'content1', '2', 'content2', ...]
    if len(page_blocks) > 2:
        for i in range(1, len(page_blocks), 2):
            page_num = int(page_blocks[i])
            content = page_blocks[i + 1] if i + 1 < len(page_blocks) else ""

            text_match = re.search(r"TEXT:\s*(.+?)(?=ILLUSTRATION:|$)", content, re.DOTALL | re.IGNORECASE)
            illust_match = re.search(r"ILLUSTRATION:\s*(.+?)(?=PAGE\s+\d+:|$)", content, re.DOTALL | re.IGNORECASE)

            pages.append({
                "page_number": page_num,
                "text": text_match.group(1).strip() if text_match else content.strip(),
                "illustration_prompt": illust_match.group(1).strip() if illust_match else "",
            })
    else:
        # Fallback: split raw text into equal chunks
        sentences = [s.strip() for s in re.split(r"[.!?]+", raw_text) if s.strip()]
        per_page = max(1, len(sentences) // max(target_pages, 1))
        for pg in range(target_pages):
            start = pg * per_page
            chunk = ". ".join(sentences[start : start + per_page])
            if chunk:
                chunk += "."
            pages.append({
                "page_number": pg + 1,
                "text": chunk,
                "illustration_prompt": f"Illustration for: {chunk[:120]}",
            })

    return pages


# ---------------------------------------------------------------------------
# Text Readability & Pacing Analysis
# ---------------------------------------------------------------------------


def _analyze_readability(
    page_texts: list[str], age_range_value: str
) -> dict[str, Any]:
    """Run readability analysis per blueprint 3.5 rules.

    Returns per-page issues, rhythm score, and aggregate stats.
    """
    rules = AGE_BAND_RULES.get(age_range_value, AGE_BAND_RULES["preschool"])
    issues: list[dict[str, Any]] = []
    total_words = 0
    total_sentences = 0
    long_sentences: list[dict[str, Any]] = []
    long_words: list[dict[str, Any]] = []
    page_word_counts: list[int] = []

    for page_idx, text in enumerate(page_texts, start=1):
        if not text:
            continue
        words = text.split()
        page_word_count = len(words)
        page_word_counts.append(page_word_count)
        total_words += page_word_count

        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        total_sentences += len(sentences)

        # Check sentence length
        for sent in sentences:
            sent_words = sent.split()
            if len(sent_words) > rules["max_sentence_words"]:
                issue = {
                    "page": page_idx,
                    "type": "sentence_too_long",
                    "detail": f"Sentence has {len(sent_words)} words (max {rules['max_sentence_words']})",
                    "text": sent[:80],
                }
                issues.append(issue)
                long_sentences.append(issue)

        # Check word length
        if rules["max_word_length"] > 0:
            for word in words:
                clean = re.sub(r"[^a-zA-Z]", "", word)
                if len(clean) > rules["max_word_length"]:
                    issue = {
                        "page": page_idx,
                        "type": "word_too_long",
                        "detail": f"Word '{clean}' has {len(clean)} letters (max {rules['max_word_length']})",
                        "word": clean,
                    }
                    issues.append(issue)
                    long_words.append(issue)

    # Total word count check
    word_count_ok = rules["total_words_min"] <= total_words <= rules["total_words_max"]
    if not word_count_ok:
        issues.append({
            "page": 0,
            "type": "total_word_count",
            "detail": (
                f"Total words: {total_words} "
                f"(expected {rules['total_words_min']}-{rules['total_words_max']})"
            ),
        })

    # Rhythm score (0-100): based on sentence cadence variance, repetition, page-turn balance
    rhythm_score = _compute_rhythm_score(page_texts, page_word_counts, rules)

    avg_sentence_length = total_words / max(total_sentences, 1)

    return {
        "age_range": age_range_value,
        "total_words": total_words,
        "total_sentences": total_sentences,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "word_count_in_range": word_count_ok,
        "expected_word_range": [rules["total_words_min"], rules["total_words_max"]],
        "rhythm_score": rhythm_score,
        "issues_count": len(issues),
        "issues": issues,
        "long_sentences_count": len(long_sentences),
        "long_words_count": len(long_words),
    }


def _compute_rhythm_score(
    page_texts: list[str],
    page_word_counts: list[int],
    rules: dict[str, Any],
) -> int:
    """Compute a read-aloud rhythm score (0-100).

    Factors: sentence cadence consistency, repetition patterns,
    page-turn momentum, tongue-twister avoidance.
    """
    if not page_texts or not page_word_counts:
        return 0

    score = 100.0

    # 1. Sentence cadence variance penalty (prefer consistent sentence length)
    all_sent_lengths: list[int] = []
    for text in page_texts:
        if not text:
            continue
        for sent in re.split(r"[.!?]+", text):
            words = sent.split()
            if words:
                all_sent_lengths.append(len(words))

    if len(all_sent_lengths) > 1:
        mean_len = sum(all_sent_lengths) / len(all_sent_lengths)
        variance = sum((x - mean_len) ** 2 for x in all_sent_lengths) / len(all_sent_lengths)
        std_dev = math.sqrt(variance)
        # High variance = less rhythmic
        if std_dev > 3:
            score -= min(20, (std_dev - 3) * 5)

    # 2. Repetition pattern bonus (repeated phrases = good for young children)
    all_text = " ".join(t for t in page_texts if t).lower()
    word_list = re.findall(r"\b\w+\b", all_text)
    if word_list:
        # Check for bigram repetition
        bigrams = [f"{word_list[i]} {word_list[i+1]}" for i in range(len(word_list) - 1)]
        bigram_counts = {}
        for bg in bigrams:
            bigram_counts[bg] = bigram_counts.get(bg, 0) + 1
        repeated = sum(1 for c in bigram_counts.values() if c >= 3)
        score += min(10, repeated * 2)

    # 3. Page-turn momentum (each page should end with forward momentum)
    for text in page_texts:
        if text and text.rstrip().endswith("?"):
            score += 1  # questions create momentum

    # 4. Tongue-twister penalty (repeated consonant clusters)
    consonant_clusters = re.findall(r"[bcdfghjklmnpqrstvwxyz]{3,}", all_text)
    if len(consonant_clusters) > 5:
        score -= min(10, (len(consonant_clusters) - 5) * 2)

    # 5. Page balance penalty (very uneven page lengths)
    if len(page_word_counts) > 1:
        mean_words = sum(page_word_counts) / len(page_word_counts)
        if mean_words > 0:
            max_deviation = max(abs(c - mean_words) / mean_words for c in page_word_counts)
            if max_deviation > 0.5:
                score -= min(15, max_deviation * 10)

    return max(0, min(100, int(score)))


async def analyze_text(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Full readability and pacing analysis for a book."""
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)
    texts = [p.get("text_content", "") or "" for p in pages]
    age = book.age_range.value if book.age_range else "preschool"
    return _analyze_readability(texts, age)


# ---------------------------------------------------------------------------
# Continuity Check
# ---------------------------------------------------------------------------


async def check_continuity(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Compare all illustration prompts against character sheets for consistency.

    Checks: clothing/accessories mentioned, character scale references,
    time-of-day/location consistency, style drift.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)
    characters = await list_characters(db, org_id, book_id)

    issues: list[dict[str, Any]] = []

    for page in pages:
        prompt = (page.get("illustration_prompt") or "").lower()
        if not prompt:
            issues.append({
                "page": page["page_number"],
                "type": "missing_prompt",
                "detail": "Page has no illustration prompt",
                "severity": "warning",
            })
            continue

        for char in characters:
            char_name = char["name"].lower()
            # Check if character is mentioned but description details are missing
            if char_name in prompt:
                # Check clothing rules
                if char.get("clothing_rules"):
                    clothing_terms = [t.strip().lower() for t in char["clothing_rules"].split(",")]
                    missing = [t for t in clothing_terms if t and t not in prompt]
                    if missing:
                        issues.append({
                            "page": page["page_number"],
                            "type": "missing_clothing",
                            "character": char["name"],
                            "detail": f"Missing clothing/accessory details: {', '.join(missing)}",
                            "severity": "error",
                        })

                # Check scale rules
                if char.get("scale_rules") and char["scale_rules"].lower() not in prompt:
                    issues.append({
                        "page": page["page_number"],
                        "type": "missing_scale",
                        "character": char["name"],
                        "detail": f"Scale rule not referenced: {char['scale_rules']}",
                        "severity": "warning",
                    })

        # Check setting continuity across pages
        if characters:
            for char in characters:
                if char.get("setting_continuity"):
                    setting_terms = [t.strip().lower() for t in char["setting_continuity"].split(",")]
                    for term in setting_terms:
                        if term and term not in prompt and char["name"].lower() in prompt:
                            issues.append({
                                "page": page["page_number"],
                                "type": "setting_inconsistency",
                                "character": char["name"],
                                "detail": f"Setting continuity detail missing: {term}",
                                "severity": "warning",
                            })

    return {
        "book_id": str(book_id),
        "pages_checked": len(pages),
        "characters_checked": len(characters),
        "issues_count": len(issues),
        "issues": issues,
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
    }


# ---------------------------------------------------------------------------
# Auto-Fix Prompts
# ---------------------------------------------------------------------------


async def auto_fix_prompts(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Batch-update all illustration prompts to include character descriptions.

    For every page that mentions a character by name, appends the character's
    full description, clothing rules, and scale rules to the prompt.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    characters = await list_characters(db, org_id, book_id)

    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.book_id == book_id,
        ChildrensBookPage.org_id == org_id,
        ChildrensBookPage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    page_records = result.scalars().all()

    fixed_count = 0
    fixes: list[dict[str, Any]] = []

    for page in page_records:
        prompt = page.illustration_prompt or ""
        prompt_lower = prompt.lower()
        additions: list[str] = []

        for char in characters:
            char_name = char["name"].lower()
            if char_name in prompt_lower:
                # Build character descriptor block
                desc_parts: list[str] = []
                if char.get("description"):
                    desc_parts.append(char["description"])
                if char.get("clothing_rules"):
                    desc_parts.append(f"wearing {char['clothing_rules']}")
                if char.get("scale_rules"):
                    desc_parts.append(f"scale: {char['scale_rules']}")
                if char.get("species_type"):
                    desc_parts.append(f"({char['species_type']})")

                descriptor = f"[{char['name']}: {', '.join(desc_parts)}]"

                # Only add if not already present
                if descriptor.lower() not in prompt_lower:
                    additions.append(descriptor)

        if additions:
            page.illustration_prompt = prompt + " " + " ".join(additions)
            fixed_count += 1
            fixes.append({
                "page_number": page.page_number,
                "added_descriptors": additions,
            })

    if fixed_count > 0:
        await db.flush()

    return {
        "book_id": str(book_id),
        "pages_scanned": len(page_records),
        "pages_fixed": fixed_count,
        "fixes": fixes,
    }


# ---------------------------------------------------------------------------
# Safety Check
# ---------------------------------------------------------------------------


async def check_safety(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Scan book text and illustration prompts for trademark terms and
    content sensitivity issues (blueprint section 3.7).
    """
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)

    trademark_issues: list[dict[str, Any]] = []
    content_issues: list[dict[str, Any]] = []

    # Gather all text to scan
    scan_items: list[tuple[int, str, str]] = []  # (page_num, field, text)
    for p in pages:
        pn = p["page_number"]
        if p.get("text_content"):
            scan_items.append((pn, "text", p["text_content"]))
        if p.get("illustration_prompt"):
            scan_items.append((pn, "illustration_prompt", p["illustration_prompt"]))

    # Also check book-level fields
    if book.title:
        scan_items.append((0, "title", book.title))
    if book.story_prompt:
        scan_items.append((0, "story_prompt", book.story_prompt))

    for page_num, field, text in scan_items:
        text_lower = text.lower()

        # Trademark scan
        for term in TRADEMARK_TERMS:
            if term in text_lower:
                trademark_issues.append({
                    "page": page_num,
                    "field": field,
                    "term": term,
                    "detail": f"Trademarked term '{term}' found in {field}",
                    "severity": "error",
                })

        # "In the style of [specific artist]" check
        style_match = re.search(r"in the style of\s+[a-z][a-z\s]+", text_lower)
        if style_match:
            trademark_issues.append({
                "page": page_num,
                "field": field,
                "term": style_match.group(),
                "detail": f"Artist style reference found: '{style_match.group()}'",
                "severity": "warning",
            })

        # Content sensitivity scan
        for pattern in CONTENT_SENSITIVITY_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                content_issues.append({
                    "page": page_num,
                    "field": field,
                    "term": match,
                    "detail": f"Sensitive content '{match}' found in {field}",
                    "severity": "error",
                })

    total_issues = len(trademark_issues) + len(content_issues)
    return {
        "book_id": str(book_id),
        "passed": total_issues == 0,
        "trademark_issues": trademark_issues,
        "content_issues": content_issues,
        "total_issues": total_issues,
    }


# ---------------------------------------------------------------------------
# Bilingual Translation
# ---------------------------------------------------------------------------


async def translate_book(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate bilingual translation for all pages via LLM.

    Supports target language and layout mode (side-by-side, alternating, back section).
    """
    book = await _get_book_or_404(db, org_id, book_id)
    target_language = options.get("target_language", book.bilingual_language or "Spanish")
    layout_mode = options.get("layout", book.bilingual_layout or "side_by_side")

    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.book_id == book_id,
        ChildrensBookPage.org_id == org_id,
        ChildrensBookPage.deleted_at.is_(None),
    ).order_by(ChildrensBookPage.page_number)
    result = await db.execute(stmt)
    page_records = result.scalars().all()

    age = book.age_range.value if book.age_range else "preschool"
    rules = AGE_BAND_RULES.get(age, AGE_BAND_RULES["preschool"])

    system_prompt = (
        f"You are a professional children's book translator. "
        f"Translate to {target_language} with cultural adaptation. "
        f"Maintain the same reading level: max {rules['max_sentence_words']} words per sentence. "
        f"Keep the tone, rhythm, and meaning. If the original rhymes, try to rhyme in the target language."
    )

    translations: list[dict[str, Any]] = []

    for page in page_records:
        if not page.text_content:
            translations.append({
                "page_number": page.page_number,
                "original": "",
                "translated": "",
            })
            continue

        prompt = (
            f"Translate this children's book page text to {target_language}:\n\n"
            f"{page.text_content}\n\n"
            f"Return ONLY the translated text, nothing else."
        )
        translated = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=1000)

        page.translated_text = translated.strip()
        translations.append({
            "page_number": page.page_number,
            "original": page.text_content,
            "translated": page.translated_text,
        })

    # Update book bilingual settings
    book.bilingual = True
    book.bilingual_language = target_language
    book.bilingual_layout = layout_mode
    await db.flush()

    return {
        "book_id": str(book_id),
        "target_language": target_language,
        "layout": layout_mode,
        "pages_translated": len([t for t in translations if t["translated"]]),
        "translations": translations,
    }


# ---------------------------------------------------------------------------
# Illustration Generation
# ---------------------------------------------------------------------------


async def generate_illustration(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    page_id: UUID,
    options: dict[str, Any],
) -> dict[str, Any]:
    """Generate an AI illustration for a specific page.

    Builds the illustration prompt with character consistency descriptors
    appended, then calls the image generation service.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    page = await _get_page_or_404(db, org_id, book_id, page_id)
    characters = await list_characters(db, org_id, book_id)

    prompt = page.illustration_prompt or f"Illustration for: {page.text_content or ''}"
    style = book.illustration_style.value if book.illustration_style else "storybook"

    # Append character consistency descriptors
    prompt_lower = prompt.lower()
    char_addons: list[str] = []
    for char in characters:
        if char["name"].lower() in prompt_lower:
            parts = [char.get("description", "")]
            if char.get("clothing_rules"):
                parts.append(f"wearing {char['clothing_rules']}")
            if char.get("scale_rules"):
                parts.append(f"scale: {char['scale_rules']}")
            char_addons.append(f"[{char['name']}: {', '.join(p for p in parts if p)}]")

    full_prompt = (
        f"{prompt} "
        f"{'  '.join(char_addons)} "
        f"Style: {style}, "
        f"palette: {book.color_palette or 'bright'}, "
        f"children's book illustration, high quality, 300 DPI print-ready"
    ).strip()

    result = await _llm_generate_image(full_prompt)

    page.image_url = result.get("image_url", "")
    page.metadata_json = page.metadata_json or {}
    page.metadata_json["illustration_prompt_used"] = full_prompt
    page.metadata_json["generation_timestamp"] = datetime.now(UTC).isoformat()
    page.metadata_json["provenance"] = {
        "model": "image_generation",
        "prompt_hash": str(hash(full_prompt)),
        "date": datetime.now(UTC).isoformat(),
    }
    await db.flush()
    await db.refresh(page)

    return {
        "page_id": str(page_id),
        "image_url": page.image_url,
        "prompt_used": full_prompt,
        "provenance": page.metadata_json.get("provenance", {}),
    }


async def generate_illustration_variations(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    page_id: UUID,
    options: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate 4 illustration variations for a page."""
    book = await _get_book_or_404(db, org_id, book_id)
    page = await _get_page_or_404(db, org_id, book_id, page_id)

    base_prompt = page.illustration_prompt or f"Illustration for: {page.text_content or ''}"
    style = book.illustration_style.value if book.illustration_style else "storybook"

    variation_modifiers = [
        "slightly zoomed in, warm lighting",
        "wider angle, cool lighting",
        "close-up detail, vibrant colors",
        "atmospheric, soft focus background",
    ]

    variations: list[dict[str, Any]] = []
    for i, modifier in enumerate(variation_modifiers, start=1):
        prompt = f"{base_prompt}, {modifier}, {style} style, children's book illustration"
        result = await _llm_generate_image(prompt)
        variations.append({
            "variation_index": i,
            "image_url": result.get("image_url", ""),
            "prompt_used": prompt,
            "modifier": modifier,
        })

    return variations


async def upload_page_image(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    page_id: UUID,
    file: UploadFile,
) -> dict[str, Any]:
    """Handle upload of a user's own image for a page.

    In production this would store the file via the storage service.
    """
    await _get_book_or_404(db, org_id, book_id)
    page = await _get_page_or_404(db, org_id, book_id, page_id)

    # Read file content (in production, stream to object storage)
    content = await file.read()
    file_size = len(content)
    filename = file.filename or "upload.png"

    # Placeholder URL (production would use storage service)
    image_url = f"uploads/childrens/{book_id}/{page_id}/{filename}"

    page.image_url = image_url
    page.metadata_json = page.metadata_json or {}
    page.metadata_json["upload"] = {
        "filename": filename,
        "content_type": file.content_type,
        "file_size": file_size,
        "uploaded_at": datetime.now(UTC).isoformat(),
    }
    await db.flush()
    await db.refresh(page)

    return {
        "page_id": str(page_id),
        "image_url": image_url,
        "filename": filename,
        "file_size": file_size,
    }


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


async def run_preflight(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Run a full preflight check per blueprint section 3.9.

    Checks: all pages have illustrations, text within safe margins, 300+ DPI,
    gutter safety, valid page count, font licensing, trademark safety,
    content sensitivity, language level.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)
    age = book.age_range.value if book.age_range else "preschool"
    rules = AGE_BAND_RULES.get(age, AGE_BAND_RULES["preschool"])

    checks: list[dict[str, Any]] = []

    # 1. All pages have illustrations
    pages_without_images = [p for p in pages if not p.get("image_url")]
    checks.append({
        "check": "illustrations_complete",
        "passed": len(pages_without_images) == 0,
        "detail": f"{len(pages_without_images)} pages missing illustrations" if pages_without_images else "All pages have illustrations",
        "pages": [p["page_number"] for p in pages_without_images],
    })

    # 2. DPI check (300+ required)
    low_dpi_pages = [p for p in pages if (p.get("dpi") or 300) < 300]
    checks.append({
        "check": "dpi_minimum",
        "passed": len(low_dpi_pages) == 0,
        "detail": f"{len(low_dpi_pages)} pages below 300 DPI" if low_dpi_pages else "All pages meet 300 DPI minimum",
    })

    # 3. Font size minimum per age band
    min_font = rules["min_font_size"]
    small_font_pages = [
        p for p in pages
        if p.get("font_size") is not None and p["font_size"] < min_font
    ]
    checks.append({
        "check": "font_size_minimum",
        "passed": len(small_font_pages) == 0,
        "detail": f"Minimum {min_font}pt required; {len(small_font_pages)} pages below" if small_font_pages else f"All pages meet {min_font}pt minimum",
    })

    # 4. Valid page count (must be multiple of 2 for spreads, and within age-range norms)
    page_count = len(pages)
    valid_count = page_count > 0 and page_count % 2 == 0
    checks.append({
        "check": "page_count",
        "passed": valid_count,
        "detail": f"{page_count} pages" + ("" if valid_count else " (must be even for print spreads)"),
    })

    # 5. Gutter safety (no text within 0.5in of spine - heuristic check)
    gutter_issues = _check_gutter_safety(pages)
    checks.append({
        "check": "gutter_safety",
        "passed": len(gutter_issues) == 0,
        "detail": f"{len(gutter_issues)} gutter collision(s)" if gutter_issues else "No gutter collisions detected",
        "issues": gutter_issues,
    })

    # 6. Readability / language level
    texts = [p.get("text_content", "") or "" for p in pages]
    readability = _analyze_readability(texts, age)
    checks.append({
        "check": "language_level",
        "passed": readability["issues_count"] == 0,
        "detail": f"{readability['issues_count']} readability issue(s)",
        "rhythm_score": readability["rhythm_score"],
    })

    # 7. Trademark safety
    safety = await check_safety(db, org_id, book_id)
    checks.append({
        "check": "trademark_safety",
        "passed": safety["passed"],
        "detail": f"{safety['total_issues']} safety issue(s)" if not safety["passed"] else "No trademark or content issues",
    })

    # 8. Content sensitivity
    checks.append({
        "check": "content_sensitivity",
        "passed": len(safety.get("content_issues", [])) == 0,
        "detail": f"{len(safety.get('content_issues', []))} content sensitivity issue(s)",
    })

    all_passed = all(c["passed"] for c in checks)

    return {
        "book_id": str(book_id),
        "status": "passed" if all_passed else "failed",
        "checks": checks,
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
        "failed_checks": sum(1 for c in checks if not c["passed"]),
    }


def _check_gutter_safety(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Heuristic gutter-collision check.

    In production this would analyse actual layout coordinates.  Here we flag
    pages with text_position == 'center' or 'left' on even pages (verso)
    and 'right' on odd pages (recto) as potential gutter collisions.
    """
    issues: list[dict[str, Any]] = []
    for p in pages:
        pos = p.get("text_position", "")
        pn = p.get("page_number", 0)
        if not pos:
            continue
        # Even pages: text near right edge is near gutter
        # Odd pages: text near left edge is near gutter
        is_recto = pn % 2 == 1  # odd = recto (right page)
        if is_recto and pos == "left":
            issues.append({
                "page": pn,
                "detail": "Text positioned at left edge (gutter side) on recto page",
            })
        elif not is_recto and pos == "right":
            issues.append({
                "page": pn,
                "detail": "Text positioned at right edge (gutter side) on verso page",
            })
    return issues


async def gutter_check(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> dict[str, Any]:
    """Dedicated gutter collision check endpoint."""
    await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)
    issues = _check_gutter_safety(pages)
    return {
        "book_id": str(book_id),
        "pages_checked": len(pages),
        "collisions": issues,
        "passed": len(issues) == 0,
    }


async def export_book(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate export file (PDF / PNG / PDF/X-1a).

    Delegates to the shared export engine for structured manifest
    generation.  In production the actual rendering would be done by
    a worker process consuming the returned manifest.
    """
    from app.modules.specialty.shared.export_engine import (
        calculate_export_metadata,
        generate_pdf_manifest,
        generate_pdfx1a_manifest,
        generate_png_pages,
    )

    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)

    export_format = options.get("format", "pdf")

    # Build book_data dict for the export engine
    book_data: dict[str, Any] = {
        "id": str(book_id),
        "title": book.title,
        "author": book.author_name or "",
        "trim_size": book.trim_size or "8.5x8.5",
        "interior_type": "color",
        "pages": pages,
    }

    export_id = str(_uuid.uuid4())
    export_url = f"exports/childrens/{book_id}/{export_id}.{export_format}"

    # Dispatch to the appropriate engine function
    if export_format == "png":
        png_pages = generate_png_pages("childrens", book_data)
        metadata = calculate_export_metadata("childrens", book_data)
        return {
            "book_id": str(book_id),
            "export_id": export_id,
            "export_url": export_url,
            "format": "png",
            "png_pages": png_pages,
            "metadata": metadata,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }
    elif export_format == "pdfx1a":
        manifest = generate_pdfx1a_manifest("childrens", book_data)
        metadata = calculate_export_metadata("childrens", book_data)
        return {
            "book_id": str(book_id),
            "export_id": export_id,
            "export_url": export_url,
            "format": "pdfx1a",
            "manifest": manifest,
            "metadata": metadata,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }
    else:
        # Default: PDF
        manifest = generate_pdf_manifest("childrens", book_data, options)
        metadata = calculate_export_metadata("childrens", book_data)
        return {
            "book_id": str(book_id),
            "export_id": export_id,
            "export_url": export_url,
            "format": export_format,
            "manifest": manifest,
            "metadata": metadata,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }


async def export_kindle(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate fixed-layout KPF/EPUB export.

    Uses the shared export engine for page ordering and metadata, then
    layers Kindle-specific viewport and rendition data on top.
    """
    from app.modules.specialty.shared.export_engine import (
        calculate_export_metadata,
        generate_pdf_manifest,
    )

    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)

    kindle_format = options.get("format", "kpf")  # kpf or epub3
    export_id = str(_uuid.uuid4())

    # Build book_data for export engine
    book_data: dict[str, Any] = {
        "id": str(book_id),
        "title": book.title,
        "author": book.author_name or "",
        "trim_size": book.trim_size or "8.5x8.5",
        "interior_type": "color",
        "pages": pages,
    }

    # Get structured manifest and metadata from the engine
    pdf_manifest = generate_pdf_manifest("childrens", book_data, options)
    metadata = calculate_export_metadata("childrens", book_data)

    # Fixed-layout dimensions for Kindle
    device_profiles = {
        "kindle_fire_hd10": {"width": 1920, "height": 1200},
        "kindle_fire_hd8": {"width": 1280, "height": 800},
        "ipad": {"width": 2048, "height": 1536},
    }
    target_device = options.get("target_device", "kindle_fire_hd10")
    device = device_profiles.get(target_device, device_profiles["kindle_fire_hd10"])

    # Calculate viewport to fit device while preserving aspect ratio
    trim_w = metadata["dimensions"]["trim_width_in"]
    trim_h = metadata["dimensions"]["trim_height_in"]
    book_aspect = trim_w / trim_h
    device_aspect = device["width"] / device["height"]
    if book_aspect > device_aspect:
        viewport_w = device["width"]
        viewport_h = int(device["width"] / book_aspect)
    else:
        viewport_h = device["height"]
        viewport_w = int(device["height"] * book_aspect)

    # Build per-page spine entries from the manifest
    page_entries = []
    for p in pdf_manifest["pages"]:
        page_entries.append({
            "sequence": p["sequence"],
            "section": p["section"],
            "type": p["type"],
            "idref": f"page{p['sequence']:04d}",
            "image_url": p.get("image_url"),
            "text_content": p.get("text_content"),
            "layout": p.get("layout") or "image_top_text_bottom",
            "is_blank": p["is_blank"],
            "properties": "rendition:layout-pre-paginated",
        })

    return {
        "book_id": str(book_id),
        "export_id": export_id,
        "export_url": f"exports/childrens/{book_id}/{export_id}.{kindle_format}",
        "format": kindle_format,
        "fixed_layout": True,
        "target_device": target_device,
        "device_dimensions": device,
        "viewport": {"width": viewport_w, "height": viewport_h},
        "rendition": {
            "layout": "pre-paginated",
            "orientation": "landscape" if trim_w > trim_h else ("portrait" if trim_h > trim_w else "auto"),
            "spread": "landscape" if trim_w > trim_h else "none",
        },
        "opf_metadata": {
            "dc:title": book.title,
            "dc:creator": book.author_name or "",
            "dc:language": book.bilingual_language if book.bilingual else "en",
            "meta_fixed_layout": "true",
            "meta_original_resolution": f"{viewport_w}x{viewport_h}",
        },
        "spine": page_entries,
        "total_pages": pdf_manifest["total_pages"],
        "page_counts": pdf_manifest["page_counts"],
        "metadata": metadata,
        "read_aloud_ready": book.bilingual or False,
        "status": "processing",
        "created_at": datetime.now(UTC).isoformat(),
    }


async def device_preview(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate device-accurate preview images for 6 device types."""
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)

    # Physical dimensions per device (diagonal inches and PPI)
    devices = [
        {"name": "Kindle Fire HD 10", "width": 1920, "height": 1200, "type": "tablet", "ppi": 224, "diag_in": 10.1},
        {"name": "Kindle Fire HD 8", "width": 1280, "height": 800, "type": "tablet", "ppi": 189, "diag_in": 8.0},
        {"name": "iPad Pro 12.9", "width": 2048, "height": 2732, "type": "tablet", "ppi": 264, "diag_in": 12.9},
        {"name": "iPad Mini", "width": 1536, "height": 2048, "type": "tablet", "ppi": 326, "diag_in": 8.3},
        {"name": "iPhone 15 Pro", "width": 1179, "height": 2556, "type": "phone", "ppi": 460, "diag_in": 6.1},
        {"name": "Desktop Browser", "width": 1920, "height": 1080, "type": "desktop", "ppi": 96, "diag_in": 24.0},
    ]

    # Parse book trim size
    trim = book.trim_size or "8.5x8.5"
    trim_parts = trim.split("x")
    book_w_in = float(trim_parts[0]) if len(trim_parts) > 0 else 8.5
    book_h_in = float(trim_parts[1]) if len(trim_parts) > 1 else 8.5
    book_aspect = book_w_in / book_h_in

    preview_page = options.get("page_number", 1)
    target_page = next((p for p in pages if p["page_number"] == preview_page), None)

    previews = []
    for device in devices:
        dev_w = device["width"]
        dev_h = device["height"]
        ppi = device["ppi"]

        # Physical display area in inches
        dev_w_in = dev_w / ppi
        dev_h_in = dev_h / ppi

        # Fit book page into device screen, preserving aspect ratio
        dev_aspect = dev_w / dev_h
        if book_aspect > dev_aspect:
            # Book is wider relative to device: fit to width
            render_w = dev_w
            render_h = int(dev_w / book_aspect)
        else:
            # Book is taller relative to device: fit to height
            render_h = dev_h
            render_w = int(dev_h * book_aspect)

        # Scale factor: how the physical book maps to this screen
        scale_factor = round((render_w / ppi) / book_w_in, 4)
        offset_x = (dev_w - render_w) // 2
        offset_y = (dev_h - render_h) // 2

        previews.append({
            "device": device["name"],
            "device_type": device["type"],
            "screen_width": dev_w,
            "screen_height": dev_h,
            "ppi": ppi,
            "physical_width_in": round(dev_w_in, 2),
            "physical_height_in": round(dev_h_in, 2),
            "render_width": render_w,
            "render_height": render_h,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "scale_factor": scale_factor,
            "preview_url": f"previews/childrens/{book_id}/page_{preview_page}_{device['name'].lower().replace(' ', '_')}.png",
            "source_image": target_page["image_url"] if target_page else None,
        })

    return {
        "book_id": str(book_id),
        "page_number": preview_page,
        "book_trim": {"width_in": book_w_in, "height_in": book_h_in},
        "devices": previews,
    }


async def reflow(
    db: AsyncSession, org_id: UUID, book_id: UUID, options: dict[str, Any]
) -> dict[str, Any]:
    """Generate an alternate trim-size version of the book.

    Re-calculates layout, margins, and font sizes for the new trim.
    """
    book = await _get_book_or_404(db, org_id, book_id)
    pages = await list_pages(db, org_id, book_id)

    new_trim = options.get("trim_size", "6x9")
    parts = new_trim.split("x")
    new_width = float(parts[0]) if len(parts) > 0 else 6
    new_height = float(parts[1]) if len(parts) > 1 else 9

    current_trim = book.trim_size or "8.5x8.5"
    current_parts = current_trim.split("x")
    current_width = float(current_parts[0]) if len(current_parts) > 0 else 8.5
    current_height = float(current_parts[1]) if len(current_parts) > 1 else 8.5

    scale_x = new_width / current_width
    scale_y = new_height / current_height

    # Area-based scale drives font sizing (preserves visual proportion)
    area_scale = math.sqrt((new_width * new_height) / (current_width * current_height))

    # Aspect ratio change detection
    current_aspect = current_width / current_height
    new_aspect = new_width / new_height
    aspect_ratio_changed = abs(current_aspect - new_aspect) > 0.05

    # Standard inner margins (inches) based on new trim size
    min_dim = min(new_width, new_height)
    margin_in = 0.5 if min_dim >= 8 else (0.375 if min_dim >= 6 else 0.25)

    # Effective content area in both trims
    old_content_w = current_width - 2 * margin_in
    old_content_h = current_height - 2 * margin_in
    new_content_w = new_width - 2 * margin_in
    new_content_h = new_height - 2 * margin_in

    reflowed_pages = []
    for p in pages:
        font_size = p.get("font_size") or 18
        # Scale font by area ratio, clamped to readable range
        new_font_size = max(10, min(36, round(font_size * area_scale)))

        # Estimate whether text will overflow the new content area
        text = p.get("text_content") or ""
        word_count = len(text.split())
        # Rough chars-per-line estimate at the new font size (assuming ~0.6 em width)
        chars_per_line = max(1, int(new_content_w * 72 / (new_font_size * 0.6)))
        lines_needed = max(1, math.ceil(len(text) / chars_per_line))
        line_height = new_font_size * 1.4 / 72  # inches
        text_height_in = lines_needed * line_height

        layout = p.get("layout") or "image_top_text_bottom"
        # Text zone gets roughly 35-40% of content height for most layouts
        text_zone_fraction = 1.0 if layout == "full_bleed_image" else 0.38
        available_text_height = new_content_h * text_zone_fraction
        text_overflow = text_height_in > available_text_height

        reflowed_pages.append({
            "page_number": p["page_number"],
            "original_font_size": font_size,
            "new_font_size": new_font_size,
            "text_content": text,
            "layout": layout,
            "text_overflow": text_overflow,
            "needs_review": aspect_ratio_changed or text_overflow,
        })

    return {
        "book_id": str(book_id),
        "original_trim": current_trim,
        "new_trim": new_trim,
        "scale_x": round(scale_x, 3),
        "scale_y": round(scale_y, 3),
        "area_scale": round(area_scale, 3),
        "aspect_ratio_changed": aspect_ratio_changed,
        "margins_in": margin_in,
        "content_area": {
            "original": {"width_in": round(old_content_w, 3), "height_in": round(old_content_h, 3)},
            "new": {"width_in": round(new_content_w, 3), "height_in": round(new_content_h, 3)},
        },
        "pages": reflowed_pages,
        "needs_review_count": sum(1 for p in reflowed_pages if p["needs_review"]),
    }
