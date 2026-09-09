"""Service layer for Children's Books CRUD operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.specialty_books.models_childrens import (
    ChildrensBook,
    ChildrensBookCharacter,
    ChildrensBookPage,
)

logger = logging.getLogger(__name__)

VALID_AGE_RANGES = {"0-2", "2-4", "4-6", "6-8", "8-12"}


async def list_childrens_books(
    db: AsyncSession,
    org_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    base = select(ChildrensBook).where(
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    )
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    items_stmt = base.order_by(ChildrensBook.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(items_stmt)
    items = list(result.scalars().all())
    return {"items": items, "total": total}


async def create_childrens_book(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict,
) -> ChildrensBook:
    age_range = data.get("age_range", "4-6")
    if hasattr(age_range, "value"):
        age_range = age_range.value
    if age_range not in VALID_AGE_RANGES:
        raise ValueError(f"Invalid age_range '{age_range}'. Must be one of: {', '.join(sorted(VALID_AGE_RANGES))}")

    def _val(v):
        return v.value if hasattr(v, "value") else v

    book = ChildrensBook(
        org_id=org_id,
        title=data["title"],
        subtitle=data.get("subtitle"),
        author=data.get("author", ""),
        age_range=age_range,
        trim_size=_val(data.get("trim_size", "8.5x8.5")),
        illustration_style=_val(data.get("illustration_style", "watercolor")),
        color_palette=data.get("color_palette"),
        story_mode=_val(data.get("story_mode", "prose")),
        creation_mode=_val(data.get("creation_mode", "ai_generate")),
        theme_moral=data.get("theme_moral"),
        main_character=data.get("main_character"),
        setting=data.get("setting"),
        tone=data.get("tone"),
        is_bilingual=data.get("is_bilingual", False),
        bilingual_language=data.get("bilingual_language"),
        bilingual_layout=_val(data.get("bilingual_layout")) if data.get("bilingual_layout") else None,
        fear_intensity=_val(data.get("fear_intensity", "none")),
        safety_settings=data.get("safety_settings"),
        page_count=data.get("page_count", 24),
        description=data.get("description"),
        status="draft",
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def get_childrens_book(
    db: AsyncSession,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> ChildrensBook | None:
    stmt = (
        select(ChildrensBook)
        .options(selectinload(ChildrensBook.pages), selectinload(ChildrensBook.characters))
        .where(ChildrensBook.id == book_id, ChildrensBook.org_id == org_id, ChildrensBook.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_childrens_book(
    db: AsyncSession,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
    data: dict,
) -> ChildrensBook | None:
    stmt = select(ChildrensBook).where(
        ChildrensBook.id == book_id, ChildrensBook.org_id == org_id, ChildrensBook.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if not book:
        return None
    updatable = {
        "title",
        "subtitle",
        "author",
        "age_range",
        "trim_size",
        "illustration_style",
        "color_palette",
        "story_mode",
        "creation_mode",
        "theme_moral",
        "main_character",
        "setting",
        "tone",
        "is_bilingual",
        "bilingual_language",
        "bilingual_layout",
        "fear_intensity",
        "safety_settings",
        "page_count",
        "description",
        "status",
    }
    for field, value in data.items():
        if field in updatable and value is not None:
            if hasattr(value, "value"):
                value = value.value
            setattr(book, field, value)
    await db.flush()
    await db.refresh(book)
    return book


async def delete_childrens_book(
    db: AsyncSession,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> bool:
    stmt = select(ChildrensBook).where(
        ChildrensBook.id == book_id, ChildrensBook.org_id == org_id, ChildrensBook.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if not book:
        return False
    book.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def _verify_book_ownership(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID) -> ChildrensBook | None:
    stmt = select(ChildrensBook).where(
        ChildrensBook.id == book_id, ChildrensBook.org_id == org_id, ChildrensBook.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_pages(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = (
        select(ChildrensBookPage)
        .where(ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None))
        .order_by(ChildrensBookPage.page_number)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_page(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID, data: dict):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None

    def _val(v):
        return v.value if hasattr(v, "value") else v

    page = ChildrensBookPage(
        book_id=book_id,
        page_number=data["page_number"],
        page_type=_val(data.get("page_type", "story")),
        layout=_val(data.get("layout", "image_top_text_bottom")),
        text_content=data.get("text_content"),
        translated_text=data.get("translated_text"),
        illustration_prompt=data.get("illustration_prompt"),
        illustration_url=data.get("illustration_url"),
        illustration_model=data.get("illustration_model"),
        illustration_seed=data.get("illustration_seed"),
        text_font=data.get("text_font"),
        text_size=data.get("text_size"),
        text_color=data.get("text_color"),
        text_position=data.get("text_position"),
        text_plate_enabled=data.get("text_plate_enabled", False),
    )
    db.add(page)
    await db.flush()
    await db.refresh(page)
    return page


async def update_page(db: AsyncSession, book_id: uuid.UUID, page_id: uuid.UUID, org_id: uuid.UUID, data: dict):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.id == page_id, ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if not page:
        return None
    updatable = {
        "page_number",
        "page_type",
        "layout",
        "text_content",
        "translated_text",
        "illustration_prompt",
        "illustration_url",
        "illustration_model",
        "illustration_seed",
        "text_font",
        "text_size",
        "text_color",
        "text_position",
        "text_plate_enabled",
    }
    for field, value in data.items():
        if field in updatable and value is not None:
            if hasattr(value, "value"):
                value = value.value
            setattr(page, field, value)
    await db.flush()
    await db.refresh(page)
    return page


async def delete_page(db: AsyncSession, book_id: uuid.UUID, page_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return False
    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.id == page_id, ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if not page:
        return False
    page.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def reorder_pages(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID, page_orders: list):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    pages_stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None)
    )
    result = await db.execute(pages_stmt)
    pages_by_id = {p.id: p for p in result.scalars().all()}
    for item in page_orders:
        if hasattr(item, "page_id"):
            if item.page_id in pages_by_id:
                pages_by_id[item.page_id].page_number = item.new_position
        else:
            idx = page_orders.index(item) + 1
            if item in pages_by_id:
                pages_by_id[item].page_number = idx
    await db.flush()
    reordered_stmt = (
        select(ChildrensBookPage)
        .where(ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None))
        .order_by(ChildrensBookPage.page_number)
    )
    result = await db.execute(reordered_stmt)
    return list(result.scalars().all())


async def upload_page_image(db: AsyncSession, book_id: uuid.UUID, page_id: uuid.UUID, org_id: uuid.UUID, file_url: str):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.id == page_id, ChildrensBookPage.book_id == book_id, ChildrensBookPage.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if not page:
        return None
    page.illustration_url = file_url
    await db.flush()
    await db.refresh(page)
    return page


async def list_characters(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = (
        select(ChildrensBookCharacter)
        .where(ChildrensBookCharacter.book_id == book_id, ChildrensBookCharacter.deleted_at.is_(None))
        .order_by(ChildrensBookCharacter.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_character(db: AsyncSession, book_id: uuid.UUID, org_id: uuid.UUID, data: dict):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    character = ChildrensBookCharacter(
        book_id=book_id,
        name=data["name"],
        species=data.get("species", "human"),
        description=data.get("description"),
        auto_append=data.get("auto_append", True),
        clothing_rules=data.get("clothing_rules"),
        scale_rules=data.get("scale_rules"),
        reference_images=data.get("reference_images", []),
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character


async def get_character(db: AsyncSession, book_id: uuid.UUID, char_id: uuid.UUID, org_id: uuid.UUID):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.id == char_id,
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_character(db: AsyncSession, book_id: uuid.UUID, char_id: uuid.UUID, org_id: uuid.UUID, data: dict):
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return None
    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.id == char_id,
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    character = result.scalar_one_or_none()
    if not character:
        return None
    updatable = {"name", "species", "description", "auto_append", "clothing_rules", "scale_rules", "reference_images"}
    for field, value in data.items():
        if field in updatable and value is not None:
            setattr(character, field, value)
    await db.flush()
    await db.refresh(character)
    return character


async def delete_character(db: AsyncSession, book_id: uuid.UUID, char_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    book = await _verify_book_ownership(db, book_id, org_id)
    if not book:
        return False
    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.id == char_id,
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    character = result.scalar_one_or_none()
    if not character:
        return False
    character.deleted_at = datetime.now(UTC)
    await db.flush()
    return True
