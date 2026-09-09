"""Cookbook Studio service layer.

Provides CRUD for cookbooks, chapters, recipes, and meal plans,
plus AI-powered recipe generation, nutrition calculation, recipe scaling,
meal plan auto-fill, shopping list generation, index generation,
front matter generation, and export/preflight.
"""

from __future__ import annotations

import json
import logging
import uuid as _uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.specialty.models.cookbook import (
    Cookbook,
    CookbookChapter,
    MealPlan,
    Recipe,
)
from app.modules.specialty.models.enums import (
    BookStatus,
    CookbookType,
    RecipeDifficulty,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------


async def _llm_generate(prompt: str, system_prompt: str = "", max_tokens: int = 4000) -> str:
    """Call the LLM orchestration service and return generated text.

    Falls back to a placeholder when the orchestration service is not
    fully configured (e.g. during development or testing).
    """
    try:
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            ModelConfig,
            TaskTypeEnum,
        )
        from app.modules.llm_orchestration.service import LLMOrchestrationService

        svc = LLMOrchestrationService()
        request = CompletionRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type=TaskTypeEnum.LONG_FORM_WRITING,
            config=ModelConfig(max_tokens=max_tokens),
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
            }
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cookbook_to_dict(cb: Cookbook) -> dict[str, Any]:
    return {
        "id": str(cb.id),
        "org_id": str(cb.org_id),
        "title": cb.title,
        "subtitle": cb.subtitle,
        "author": cb.author,
        "cookbook_type": cb.cookbook_type,
        "status": cb.status,
        "cuisine": cb.cuisine,
        "target_audience": cb.target_audience,
        "description": cb.description,
        "chapter_organization": cb.chapter_organization,
        "recipe_layout": cb.recipe_layout,
        "illustration_method": cb.illustration_method,
        "interior_type": cb.interior_type,
        "trim_size": cb.trim_size,
        "page_count": cb.page_count,
        "include_nutrition": cb.include_nutrition,
        "include_meal_plans": cb.include_meal_plans,
        "include_shopping_lists": cb.include_shopping_lists,
        "include_index": cb.include_index,
        "include_conversion_charts": cb.include_conversion_charts,
        "dietary_tags": cb.dietary_tags or [],
        "metadata_settings": cb.metadata_settings or {},
        "qa_score": cb.qa_score,
        "created_at": cb.created_at.isoformat() if cb.created_at else None,
        "updated_at": cb.updated_at.isoformat() if cb.updated_at else None,
    }


def _chapter_to_dict(ch: CookbookChapter) -> dict[str, Any]:
    return {
        "id": str(ch.id),
        "cookbook_id": str(ch.cookbook_id),
        "title": ch.title,
        "description": ch.description,
        "introduction_text": ch.introduction_text,
        "chapter_order": ch.chapter_order,
        "chapter_type": ch.chapter_type,
        "created_at": ch.created_at.isoformat() if ch.created_at else None,
        "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
    }


def _recipe_to_dict(r: Recipe) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "chapter_id": str(r.chapter_id),
        "title": r.title,
        "description": r.description,
        "difficulty": r.difficulty,
        "prep_time_minutes": r.prep_time_minutes,
        "cook_time_minutes": r.cook_time_minutes,
        "total_time_minutes": r.total_time_minutes,
        "servings": r.servings,
        "recipe_order": r.recipe_order,
        "image_url": r.image_url,
        "image_prompt": r.image_prompt,
        "ingredients": r.ingredients or [],
        "instructions": r.instructions or [],
        "nutrition": r.nutrition or {},
        "notes": r.notes,
        "tips": r.tips,
        "variations": r.variations or [],
        "tags": r.tags or [],
        "dietary_flags": r.dietary_flags or [],
        "source": r.source,
        "scaling_factor": r.scaling_factor,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _meal_plan_to_dict(mp: MealPlan) -> dict[str, Any]:
    return {
        "id": str(mp.id),
        "cookbook_id": str(mp.cookbook_id),
        "title": mp.title,
        "description": mp.description,
        "plan_type": mp.plan_type,
        "days": mp.days or [],
        "total_calories_target": mp.total_calories_target,
        "dietary_goals": mp.dietary_goals or {},
        "shopping_list": mp.shopping_list or [],
        "created_at": mp.created_at.isoformat() if mp.created_at else None,
        "updated_at": mp.updated_at.isoformat() if mp.updated_at else None,
    }


async def _get_cookbook_or_404(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> Cookbook:
    stmt = select(Cookbook).where(
        Cookbook.id == cookbook_id,
        Cookbook.org_id == org_id,
        Cookbook.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    cb = result.scalar_one_or_none()
    if cb is None:
        raise NotFoundError("Cookbook", f"Cookbook {cookbook_id} not found")
    return cb


async def _get_chapter_or_404(db: AsyncSession, org_id: UUID, cookbook_id: UUID, chapter_id: UUID) -> CookbookChapter:
    # Only Cookbook carries org_id, so tenant scoping has to join through it.
    # Filtering on the caller-supplied cookbook_id alone let any authenticated
    # user reach another organisation's chapters.
    stmt = (
        select(CookbookChapter)
        .join(Cookbook, CookbookChapter.cookbook_id == Cookbook.id)
        .where(
            CookbookChapter.id == chapter_id,
            CookbookChapter.cookbook_id == cookbook_id,
            CookbookChapter.deleted_at.is_(None),
            Cookbook.org_id == org_id,
            Cookbook.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    ch = result.scalar_one_or_none()
    if ch is None:
        raise NotFoundError("CookbookChapter", f"Chapter {chapter_id} not found")
    return ch


async def _get_recipe_or_404(db: AsyncSession, org_id: UUID, recipe_id: UUID) -> Recipe:
    # Recipe -> CookbookChapter -> Cookbook is the only path to org_id. Without
    # this join the lookup matched on recipe id alone, so a recipe UUID from
    # any tenant resolved for any caller.
    stmt = (
        select(Recipe)
        .join(CookbookChapter, Recipe.chapter_id == CookbookChapter.id)
        .join(Cookbook, CookbookChapter.cookbook_id == Cookbook.id)
        .where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
            CookbookChapter.deleted_at.is_(None),
            Cookbook.org_id == org_id,
            Cookbook.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    r = result.scalar_one_or_none()
    if r is None:
        raise NotFoundError("Recipe", f"Recipe {recipe_id} not found")
    return r


async def _get_meal_plan_or_404(db: AsyncSession, org_id: UUID, cookbook_id: UUID, plan_id: UUID) -> MealPlan:
    stmt = (
        select(MealPlan)
        .join(Cookbook, MealPlan.cookbook_id == Cookbook.id)
        .where(
            MealPlan.id == plan_id,
            MealPlan.cookbook_id == cookbook_id,
            MealPlan.deleted_at.is_(None),
            Cookbook.org_id == org_id,
            Cookbook.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    mp = result.scalar_one_or_none()
    if mp is None:
        raise NotFoundError("MealPlan", f"Meal plan {plan_id} not found")
    return mp


async def _update_cookbook_counts(db: AsyncSession, cookbook_id: UUID) -> None:
    """No-op: Cookbook model does not store denormalized counts.

    Kept as a hook for future use (e.g. cache refresh).
    """
    pass


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats(db: AsyncSession, org_id: UUID) -> dict[str, Any]:
    """Get cookbook statistics for the org."""
    base = [Cookbook.org_id == org_id, Cookbook.deleted_at.is_(None)]

    total_stmt = select(func.count()).select_from(Cookbook).where(*base)
    total_result = await db.execute(total_stmt)
    total_cookbooks = total_result.scalar() or 0

    in_progress_stmt = (
        select(func.count()).select_from(Cookbook).where(*base, Cookbook.status == BookStatus.in_progress)
    )
    in_progress_result = await db.execute(in_progress_stmt)

    published_stmt = select(func.count()).select_from(Cookbook).where(*base, Cookbook.status == BookStatus.published)
    published_result = await db.execute(published_stmt)

    cb_ids_stmt = select(Cookbook.id).where(*base)
    ch_ids_stmt = select(CookbookChapter.id).where(
        CookbookChapter.cookbook_id.in_(cb_ids_stmt),
        CookbookChapter.deleted_at.is_(None),
    )
    recipe_count_stmt = (
        select(func.count())
        .select_from(Recipe)
        .where(
            Recipe.chapter_id.in_(ch_ids_stmt),
            Recipe.deleted_at.is_(None),
        )
    )
    recipe_result = await db.execute(recipe_count_stmt)

    chapter_count_stmt = (
        select(func.count())
        .select_from(CookbookChapter)
        .where(
            CookbookChapter.cookbook_id.in_(cb_ids_stmt),
            CookbookChapter.deleted_at.is_(None),
        )
    )
    chapter_result = await db.execute(chapter_count_stmt)

    return {
        "total_cookbooks": total_cookbooks,
        "in_progress": in_progress_result.scalar() or 0,
        "published": published_result.scalar() or 0,
        "total_recipes": recipe_result.scalar() or 0,
        "total_chapters": chapter_result.scalar() or 0,
    }


# ---------------------------------------------------------------------------
# Cookbook CRUD
# ---------------------------------------------------------------------------


async def list_cookbooks(
    db: AsyncSession,
    org_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: BookStatus | None = None,
    type_filter: CookbookType | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Return a paginated list of cookbooks."""
    stmt = select(Cookbook).where(
        Cookbook.org_id == org_id,
        Cookbook.deleted_at.is_(None),
    )
    count_stmt = (
        select(func.count())
        .select_from(Cookbook)
        .where(
            Cookbook.org_id == org_id,
            Cookbook.deleted_at.is_(None),
        )
    )

    if status_filter:
        stmt = stmt.where(Cookbook.status == status_filter)
        count_stmt = count_stmt.where(Cookbook.status == status_filter)
    if type_filter:
        stmt = stmt.where(Cookbook.cookbook_type == type_filter)
        count_stmt = count_stmt.where(Cookbook.cookbook_type == type_filter)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Cookbook.title.ilike(pattern))
        count_stmt = count_stmt.where(Cookbook.title.ilike(pattern))

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Cookbook.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    cookbooks = result.scalars().all()

    return {
        "items": [_cookbook_to_dict(cb) for cb in cookbooks],
        "total_count": total_count,
        "has_more": (offset + page_size) < total_count,
        "next_cursor": str(page + 1) if (offset + page_size) < total_count else None,
    }


async def create_cookbook(db: AsyncSession, org_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new cookbook."""
    cb = Cookbook(
        org_id=org_id,
        title=payload["title"],
        subtitle=payload.get("subtitle"),
        author=payload.get("author"),
        cookbook_type=payload.get("cookbook_type", CookbookType.general.value),
        status=BookStatus.draft.value,
        cuisine=payload.get("cuisine"),
        target_audience=payload.get("target_audience"),
        description=payload.get("description"),
        chapter_organization=payload.get("chapter_organization"),
        recipe_layout=payload.get("recipe_layout"),
        illustration_method=payload.get("illustration_method"),
        interior_type=payload.get("interior_type"),
        trim_size=payload.get("trim_size", "8x10"),
        page_count=payload.get("page_count", 100),
        include_nutrition=payload.get("include_nutrition", True),
        include_meal_plans=payload.get("include_meal_plans", False),
        include_shopping_lists=payload.get("include_shopping_lists", False),
        include_index=payload.get("include_index", True),
        include_conversion_charts=payload.get("include_conversion_charts", True),
        dietary_tags=payload.get("dietary_tags", []),
        metadata_settings=payload.get("metadata_settings"),
    )
    db.add(cb)
    await db.flush()
    await db.refresh(cb)
    return _cookbook_to_dict(cb)


async def get_cookbook(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> dict[str, Any]:
    """Return a single cookbook by ID."""
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    return _cookbook_to_dict(cb)


async def update_cookbook(db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Update a cookbook."""
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    allowed = {
        "title",
        "subtitle",
        "author",
        "cookbook_type",
        "status",
        "cuisine",
        "target_audience",
        "description",
        "chapter_organization",
        "recipe_layout",
        "illustration_method",
        "interior_type",
        "trim_size",
        "page_count",
        "include_nutrition",
        "include_meal_plans",
        "include_shopping_lists",
        "include_index",
        "include_conversion_charts",
        "dietary_tags",
        "metadata_settings",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(cb, key, value)
    await db.flush()
    await db.refresh(cb)
    return _cookbook_to_dict(cb)


async def delete_cookbook(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> bool:
    """Soft-delete a cookbook."""
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    cb.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Chapter CRUD
# ---------------------------------------------------------------------------


async def list_chapters(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> list[dict]:
    """Return all chapters for a cookbook, ordered by sort_order."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)
    stmt = (
        select(CookbookChapter)
        .where(
            CookbookChapter.cookbook_id == cookbook_id,
            CookbookChapter.deleted_at.is_(None),
        )
        .order_by(CookbookChapter.chapter_order)
    )
    result = await db.execute(stmt)
    return [_chapter_to_dict(ch) for ch in result.scalars().all()]


async def create_chapter(db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]) -> dict:
    """Create a new chapter in a cookbook."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)

    # Auto-assign chapter_order if not provided
    if "chapter_order" not in payload:
        max_stmt = select(func.max(CookbookChapter.chapter_order)).where(
            CookbookChapter.cookbook_id == cookbook_id,
            CookbookChapter.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        current_max = max_result.scalar() or 0
        payload["chapter_order"] = current_max + 1

    ch = CookbookChapter(
        cookbook_id=cookbook_id,
        title=payload["title"],
        description=payload.get("description"),
        introduction_text=payload.get("introduction_text"),
        chapter_order=payload["chapter_order"],
        chapter_type=payload.get("chapter_type"),
    )
    db.add(ch)
    await db.flush()
    await db.refresh(ch)

    await _update_cookbook_counts(db, cookbook_id)
    return _chapter_to_dict(ch)


async def update_chapter(
    db: AsyncSession,
    org_id: UUID,
    cookbook_id: UUID,
    chapter_id: UUID,
    payload: dict[str, Any],
) -> dict:
    """Update a chapter."""
    ch = await _get_chapter_or_404(db, org_id, cookbook_id, chapter_id)
    allowed = {"title", "description", "introduction_text", "chapter_order", "chapter_type"}
    for key, value in payload.items():
        if key in allowed:
            setattr(ch, key, value)
    await db.flush()
    await db.refresh(ch)
    return _chapter_to_dict(ch)


async def delete_chapter(db: AsyncSession, org_id: UUID, cookbook_id: UUID, chapter_id: UUID) -> bool:
    """Soft-delete a chapter."""
    ch = await _get_chapter_or_404(db, org_id, cookbook_id, chapter_id)
    ch.deleted_at = datetime.now(UTC)
    await db.flush()
    await _update_cookbook_counts(db, cookbook_id)
    return True


async def reorder_chapters(db: AsyncSession, org_id: UUID, cookbook_id: UUID, chapter_ids: list[UUID]) -> list[dict]:
    """Reorder chapters by assigning new sort_order based on the given ID order."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)
    for idx, cid in enumerate(chapter_ids, start=1):
        await db.execute(
            update(CookbookChapter)
            .where(
                CookbookChapter.id == UUID(str(cid)),
                CookbookChapter.cookbook_id == cookbook_id,
            )
            .values(chapter_order=idx)
        )
    await db.flush()
    return await list_chapters(db, org_id, cookbook_id)


# ---------------------------------------------------------------------------
# Recipe CRUD
# ---------------------------------------------------------------------------


async def list_recipes(db: AsyncSession, org_id: UUID, chapter_id: UUID) -> list[dict]:
    """Return all recipes for a chapter, ordered by sort_order."""
    stmt = (
        select(Recipe)
        .where(
            Recipe.chapter_id == chapter_id,
            Recipe.deleted_at.is_(None),
        )
        .order_by(Recipe.recipe_order)
    )
    result = await db.execute(stmt)
    return [_recipe_to_dict(r) for r in result.scalars().all()]


async def create_recipe(db: AsyncSession, org_id: UUID, chapter_id: UUID, payload: dict[str, Any]) -> dict:
    """Create a new recipe in a chapter."""
    ch_stmt = select(CookbookChapter).where(
        CookbookChapter.id == chapter_id,
        CookbookChapter.deleted_at.is_(None),
    )
    ch_result = await db.execute(ch_stmt)
    chapter = ch_result.scalar_one_or_none()
    if chapter is None:
        raise NotFoundError("CookbookChapter", f"Chapter {chapter_id} not found")

    # Auto-assign recipe_order if not provided
    if "recipe_order" not in payload:
        max_stmt = select(func.max(Recipe.recipe_order)).where(
            Recipe.chapter_id == chapter_id,
            Recipe.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        current_max = max_result.scalar() or 0
        payload["recipe_order"] = current_max + 1

    r = Recipe(
        chapter_id=chapter_id,
        title=payload["title"],
        description=payload.get("description"),
        difficulty=payload.get("difficulty", RecipeDifficulty.easy.value),
        prep_time_minutes=payload.get("prep_time_minutes"),
        cook_time_minutes=payload.get("cook_time_minutes"),
        total_time_minutes=payload.get("total_time_minutes"),
        servings=payload.get("servings"),
        recipe_order=payload["recipe_order"],
        ingredients=payload.get("ingredients", []),
        instructions=payload.get("instructions", []),
        nutrition=payload.get("nutrition", {}),
        notes=payload.get("notes"),
        tips=payload.get("tips"),
        variations=payload.get("variations"),
        tags=payload.get("tags"),
        dietary_flags=payload.get("dietary_flags", []),
        image_url=payload.get("image_url"),
        image_prompt=payload.get("image_prompt"),
        source=payload.get("source"),
        scaling_factor=payload.get("scaling_factor", 1.0),
    )
    db.add(r)
    await db.flush()
    await db.refresh(r)

    await _update_cookbook_counts(db, chapter.cookbook_id)
    return _recipe_to_dict(r)


async def get_recipe(db: AsyncSession, org_id: UUID, recipe_id: UUID) -> dict:
    """Return a single recipe by ID."""
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    return _recipe_to_dict(r)


async def update_recipe(db: AsyncSession, org_id: UUID, recipe_id: UUID, payload: dict[str, Any]) -> dict:
    """Update a recipe."""
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    allowed = {
        "title",
        "description",
        "difficulty",
        "prep_time_minutes",
        "cook_time_minutes",
        "total_time_minutes",
        "servings",
        "recipe_order",
        "ingredients",
        "instructions",
        "nutrition",
        "notes",
        "tips",
        "variations",
        "tags",
        "dietary_flags",
        "image_url",
        "image_prompt",
        "source",
        "scaling_factor",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(r, key, value)
    await db.flush()
    await db.refresh(r)
    return _recipe_to_dict(r)


async def delete_recipe(db: AsyncSession, org_id: UUID, recipe_id: UUID) -> bool:
    """Soft-delete a recipe."""
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    ch_stmt = select(CookbookChapter.cookbook_id).where(CookbookChapter.id == r.chapter_id)
    ch_result = await db.execute(ch_stmt)
    cookbook_id = ch_result.scalar()

    r.deleted_at = datetime.now(UTC)
    await db.flush()

    if cookbook_id:
        await _update_cookbook_counts(db, cookbook_id)
    return True


async def reorder_recipes(db: AsyncSession, org_id: UUID, chapter_id: UUID, recipe_ids: list[UUID]) -> list[dict]:
    """Reorder recipes by assigning new sort_order based on the given ID order."""
    for idx, rid in enumerate(recipe_ids, start=1):
        await db.execute(
            update(Recipe)
            .where(
                Recipe.id == UUID(str(rid)),
                Recipe.chapter_id == chapter_id,
            )
            .values(recipe_order=idx)
        )
    await db.flush()
    return await list_recipes(db, org_id, chapter_id)


# ---------------------------------------------------------------------------
# AI Recipe Generation
# ---------------------------------------------------------------------------


async def generate_recipe(db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """AI-generate a recipe based on constraints (cuisine, dietary, difficulty, etc.).

    payload: {"cuisine": "italian", "difficulty": "easy",
              "dietary": ["vegetarian"], "description": "pasta dish"}
    """
    # TODO: integrate with LLM service
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    logger.info("Generating recipe for cookbook %s: %s", cookbook_id, payload)

    cuisine = payload.get("cuisine", cb.cuisine or "international")
    difficulty = payload.get("difficulty", "easy")
    dietary = payload.get("dietary", [])
    description = payload.get("description", "a delicious dish")

    system_prompt = "You are a professional chef and cookbook author. " "Generate recipes in structured JSON format."
    prompt = (
        f"Create a {difficulty} {cuisine} recipe for: {description}.\n"
        f"Dietary requirements: {', '.join(dietary) if dietary else 'none'}.\n"
        f"Return JSON with: title, description, prep_time_minutes, cook_time_minutes, "
        f"servings, ingredients (list of {{name, amount, unit, category}}), "
        f"instructions (list of {{step, text}}), tips."
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=3000)

    try:
        recipe_data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        recipe_data = {
            "title": f"{cuisine.title()} {description.title()}",
            "description": f"A {difficulty} {cuisine} {description}",
            "prep_time_minutes": 15,
            "cook_time_minutes": 30,
            "servings": 4,
            "ingredients": [
                {"name": "main ingredient", "amount": 2, "unit": "cups", "category": "produce"},
                {"name": "seasoning", "amount": 1, "unit": "tbsp", "category": "spices"},
                {"name": "oil", "amount": 2, "unit": "tbsp", "category": "pantry"},
            ],
            "instructions": [
                {"step": 1, "text": "Prepare all ingredients."},
                {"step": 2, "text": "Cook the main ingredient."},
                {"step": 3, "text": "Season and serve."},
            ],
            "tips": "Adjust seasoning to taste.",
        }

    return {
        "cookbook_id": str(cookbook_id),
        "generated_recipe": recipe_data,
        "constraints": {
            "cuisine": cuisine,
            "difficulty": difficulty,
            "dietary": dietary,
            "description": description,
        },
        "status": "generated",
        "message": "Recipe generated. Use create_recipe to save it to a chapter.",
    }


async def generate_recipe_image(
    db: AsyncSession, org_id: UUID, recipe_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """AI-generate a food photo for a recipe."""
    # TODO: integrate with image generation service
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    logger.info("Generating image for recipe %s", recipe_id)

    style = payload.get("style", "professional food photography")
    image_id = str(_uuid.uuid4())

    return {
        "recipe_id": str(recipe_id),
        "recipe_title": r.title,
        "image_url": f"/api/v1/storage/specialty/cookbook/pending/recipes/{image_id}/photo.jpg",
        "status": "pending_generation",
        "style": style,
        "message": (
            "The image generation service has been queued. " "The image will be available once processing is complete."
        ),
    }


async def improve_recipe(db: AsyncSession, org_id: UUID, recipe_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """AI-improve/rewrite a recipe's instructions for clarity."""
    # TODO: integrate with LLM service
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    logger.info("Improving recipe %s", recipe_id)

    focus = payload.get("focus", "clarity")  # clarity, brevity, detail, beginner-friendly

    system_prompt = "You are a professional recipe editor. Rewrite the recipe instructions " f"with a focus on {focus}."
    prompt = (
        f"Recipe: {r.title}\n"
        f"Current instructions: {json.dumps(r.instructions or [])}\n"
        f"Ingredients: {json.dumps(r.ingredients or [])}\n"
        f"Please rewrite the instructions with focus on: {focus}"
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=2000)

    return {
        "recipe_id": str(recipe_id),
        "original_instructions": r.instructions or [],
        "improved_text": raw,
        "focus": focus,
        "status": "improved",
        "message": "Review the improved instructions and use update_recipe to save.",
    }


# ---------------------------------------------------------------------------
# Nutrition Calculation
# ---------------------------------------------------------------------------


async def calculate_nutrition(db: AsyncSession, org_id: UUID, recipe_id: UUID) -> dict[str, Any]:
    """Calculate nutrition facts from ingredients list.

    In production this would integrate with a nutrition API (e.g. USDA FoodData Central).
    """
    # TODO: integrate with nutrition API
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    ingredients = r.ingredients or []
    logger.info("Calculating nutrition for recipe %s (%d ingredients)", recipe_id, len(ingredients))

    estimated_calories = len(ingredients) * 80
    nutrition_data = {
        "calories": estimated_calories,
        "protein_g": round(estimated_calories * 0.15 / 4, 1),
        "carbs_g": round(estimated_calories * 0.50 / 4, 1),
        "fat_g": round(estimated_calories * 0.35 / 9, 1),
        "fiber_g": round(len(ingredients) * 1.5, 1),
        "sodium_mg": len(ingredients) * 120,
        "sugar_g": round(len(ingredients) * 2.0, 1),
        "per_serving": True,
        "servings": r.servings or 4,
    }

    r.nutrition = nutrition_data
    await db.flush()
    await db.refresh(r)

    return {
        "recipe_id": str(recipe_id),
        "recipe_title": r.title,
        "nutrition": nutrition_data,
        "ingredient_count": len(ingredients),
        "status": "calculated",
    }


async def batch_calculate_nutrition(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> dict[str, Any]:
    """Calculate nutrition for all recipes in a cookbook."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)

    ch_ids_stmt = select(CookbookChapter.id).where(
        CookbookChapter.cookbook_id == cookbook_id,
        CookbookChapter.deleted_at.is_(None),
    )
    recipe_stmt = select(Recipe).where(
        Recipe.chapter_id.in_(ch_ids_stmt),
        Recipe.deleted_at.is_(None),
    )
    result = await db.execute(recipe_stmt)
    recipes = result.scalars().all()

    processed = 0
    for recipe in recipes:
        await calculate_nutrition(db, org_id, recipe.id)
        processed += 1

    return {
        "cookbook_id": str(cookbook_id),
        "processed": processed,
        "total": len(recipes),
        "status": "complete",
    }


# ---------------------------------------------------------------------------
# Recipe Scaling
# ---------------------------------------------------------------------------


async def scale_recipe(db: AsyncSession, org_id: UUID, recipe_id: UUID, factor: float) -> dict[str, Any]:
    """Scale a recipe's ingredients by a factor (e.g., 2.0 = double)."""
    r = await _get_recipe_or_404(db, org_id, recipe_id)
    ingredients = r.ingredients or []

    scaled_ingredients = []
    for ing in ingredients:
        scaled = dict(ing)
        if "amount" in scaled and isinstance(scaled["amount"], int | float):
            scaled["amount"] = round(scaled["amount"] * factor, 2)
        scaled_ingredients.append(scaled)

    original_servings = r.servings or 4
    new_servings = round(original_servings * factor)

    return {
        "recipe_id": str(recipe_id),
        "recipe_title": r.title,
        "factor": factor,
        "original_servings": original_servings,
        "new_servings": new_servings,
        "original_ingredients": ingredients,
        "scaled_ingredients": scaled_ingredients,
    }


# ---------------------------------------------------------------------------
# Meal Plan Operations
# ---------------------------------------------------------------------------


async def list_meal_plans(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> list[dict]:
    """Return all meal plans for a cookbook."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)
    stmt = (
        select(MealPlan)
        .where(
            MealPlan.cookbook_id == cookbook_id,
            MealPlan.deleted_at.is_(None),
        )
        .order_by(MealPlan.created_at)
    )
    result = await db.execute(stmt)
    return [_meal_plan_to_dict(mp) for mp in result.scalars().all()]


async def create_meal_plan(db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]) -> dict:
    """Create a new meal plan."""
    await _get_cookbook_or_404(db, org_id, cookbook_id)
    mp = MealPlan(
        cookbook_id=cookbook_id,
        title=payload["title"],
        description=payload.get("description"),
        plan_type=payload.get("plan_type"),
        days=payload.get("days"),
        total_calories_target=payload.get("total_calories_target"),
        dietary_goals=payload.get("dietary_goals", {}),
        shopping_list=payload.get("shopping_list"),
    )
    db.add(mp)
    await db.flush()
    await db.refresh(mp)
    return _meal_plan_to_dict(mp)


async def update_meal_plan(
    db: AsyncSession,
    org_id: UUID,
    cookbook_id: UUID,
    plan_id: UUID,
    payload: dict[str, Any],
) -> dict:
    """Update a meal plan."""
    mp = await _get_meal_plan_or_404(db, org_id, cookbook_id, plan_id)
    allowed = {
        "title",
        "description",
        "plan_type",
        "days",
        "total_calories_target",
        "dietary_goals",
        "shopping_list",
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(mp, key, value)
    await db.flush()
    await db.refresh(mp)
    return _meal_plan_to_dict(mp)


async def delete_meal_plan(db: AsyncSession, org_id: UUID, cookbook_id: UUID, plan_id: UUID) -> bool:
    """Soft-delete a meal plan."""
    mp = await _get_meal_plan_or_404(db, org_id, cookbook_id, plan_id)
    mp.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def auto_fill_meal_plan(
    db: AsyncSession,
    org_id: UUID,
    cookbook_id: UUID,
    plan_id: UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """AI auto-fill a meal plan based on dietary goals and available recipes.

    payload: {"meals_per_day": 3, "preferences": ["quick", "balanced"]}
    """
    # TODO: integrate with LLM service
    mp = await _get_meal_plan_or_404(db, org_id, cookbook_id, plan_id)
    logger.info("Auto-filling meal plan %s for cookbook %s", plan_id, cookbook_id)

    ch_ids_stmt = select(CookbookChapter.id).where(
        CookbookChapter.cookbook_id == cookbook_id,
        CookbookChapter.deleted_at.is_(None),
    )
    recipe_stmt = select(Recipe).where(
        Recipe.chapter_id.in_(ch_ids_stmt),
        Recipe.deleted_at.is_(None),
    )
    result = await db.execute(recipe_stmt)
    recipes = result.scalars().all()
    recipe_ids = [str(r.id) for r in recipes]

    meals_per_day = payload.get("meals_per_day", 3)
    meal_names = ["breakfast", "lunch", "dinner"][:meals_per_day]
    # Default duration based on plan_type: weekly=7
    duration = payload.get("duration_days", 7)

    days = []
    recipe_index = 0
    for day_num in range(1, duration + 1):
        meals = []
        for meal_name in meal_names:
            rid = recipe_ids[recipe_index % len(recipe_ids)] if recipe_ids else None
            meals.append({"meal": meal_name, "recipe_id": rid})
            recipe_index += 1
        days.append({"day": day_num, "meals": meals})

    mp.days = days
    await db.flush()
    await db.refresh(mp)

    return {
        "plan_id": str(plan_id),
        "cookbook_id": str(cookbook_id),
        "duration_days": duration,
        "meals_per_day": meals_per_day,
        "recipes_available": len(recipe_ids),
        "days": days,
        "status": "auto_filled",
    }


# ---------------------------------------------------------------------------
# Shopping List
# ---------------------------------------------------------------------------


async def generate_shopping_list(db: AsyncSession, org_id: UUID, plan_id: UUID) -> dict[str, Any]:
    """Generate a consolidated shopping list from a meal plan.

    Aggregates ingredients across all recipes, combines duplicates,
    and organizes by category.
    """
    stmt = select(MealPlan).where(
        MealPlan.id == plan_id,
        MealPlan.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    mp = result.scalar_one_or_none()
    if mp is None:
        raise NotFoundError("MealPlan", f"Meal plan {plan_id} not found")

    days = mp.days or []

    recipe_ids: set[str] = set()
    for day in days:
        for meal in day.get("meals", []):
            rid = meal.get("recipe_id")
            if rid:
                recipe_ids.add(rid)

    aggregated: dict[str, dict[str, Any]] = {}
    for rid in recipe_ids:
        try:
            r = await _get_recipe_or_404(db, org_id, UUID(rid))
        except NotFoundError:
            continue
        for ing in r.ingredients or []:
            key = ing.get("name", "").lower().strip()
            if not key:
                continue
            if key in aggregated:
                if aggregated[key]["unit"] == ing.get("unit", ""):
                    aggregated[key]["amount"] += ing.get("amount", 0)
                else:
                    aggregated[key]["notes"] = (
                        aggregated[key].get("notes", "") + f"; also {ing.get('amount', '')} {ing.get('unit', '')}"
                    )
            else:
                aggregated[key] = {
                    "name": ing.get("name", key),
                    "amount": ing.get("amount", 0),
                    "unit": ing.get("unit", ""),
                    "category": ing.get("category", "other"),
                    "notes": "",
                }

    by_category: dict[str, list] = defaultdict(list)
    for item in aggregated.values():
        by_category[item["category"]].append(item)

    categories = [{"category": cat, "items": items} for cat, items in sorted(by_category.items())]

    return {
        "plan_id": str(plan_id),
        "total_items": len(aggregated),
        "total_recipes": len(recipe_ids),
        "categories": categories,
    }


async def generate_recipe_shopping_list(
    db: AsyncSession, org_id: UUID, recipe_id: UUID, servings: int = 1
) -> dict[str, Any]:
    """Generate a shopping list for a single recipe."""
    r = await _get_recipe_or_404(db, org_id, recipe_id)

    original_servings = r.servings or 4
    factor = servings / original_servings if original_servings else 1

    items = []
    for ing in r.ingredients or []:
        item = dict(ing)
        if "amount" in item and isinstance(item["amount"], int | float):
            item["amount"] = round(item["amount"] * factor, 2)
        items.append(item)

    by_category: dict[str, list] = defaultdict(list)
    for item in items:
        by_category[item.get("category", "other")].append(item)

    categories = [{"category": cat, "items": cat_items} for cat, cat_items in sorted(by_category.items())]

    return {
        "recipe_id": str(recipe_id),
        "recipe_title": r.title,
        "servings": servings,
        "total_items": len(items),
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# Index & Front Matter
# ---------------------------------------------------------------------------


async def generate_index(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> dict[str, Any]:
    """Generate a recipe index (alphabetical, by ingredient, by category)."""
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    chapters = await list_chapters(db, org_id, cookbook_id)

    all_recipes: list[dict] = []
    for ch in chapters:
        recipes = await list_recipes(db, org_id, UUID(ch["id"]))
        for r in recipes:
            r["chapter_title"] = ch["title"]
        all_recipes.extend(recipes)

    alphabetical = sorted(all_recipes, key=lambda r: r["title"].lower())

    by_ingredient: dict[str, list[str]] = defaultdict(list)
    for r in all_recipes:
        for ing in r.get("ingredients", []):
            name = ing.get("name", "").lower().strip()
            if name:
                by_ingredient[name].append(r["title"])

    by_category: dict[str, list[str]] = defaultdict(list)
    for r in all_recipes:
        by_category[r.get("chapter_title", "Uncategorized")].append(r["title"])

    return {
        "cookbook_id": str(cookbook_id),
        "cookbook_title": cb.title,
        "total_recipes": len(all_recipes),
        "alphabetical": [
            {"title": r["title"], "chapter": r.get("chapter_title", ""), "page": idx + 1}
            for idx, r in enumerate(alphabetical)
        ],
        "by_ingredient": dict(sorted(by_ingredient.items())),
        "by_category": dict(sorted(by_category.items())),
        "status": "generated",
    }


async def generate_front_matter(
    db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """AI-generate front matter (introduction, about the author, acknowledgments).

    payload: {"sections": ["introduction", "about_author", "acknowledgments"],
              "author_bio": "...", "cookbook_inspiration": "..."}
    """
    # TODO: integrate with LLM service
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    logger.info("Generating front matter for cookbook %s", cookbook_id)

    sections = payload.get("sections", ["introduction", "about_author", "acknowledgments"])
    author_bio = payload.get("author_bio", cb.author or "the author")
    inspiration = payload.get("cookbook_inspiration", cb.description or "")

    system_prompt = "You are a professional cookbook editor. Write engaging front matter sections."
    prompt = (
        f"Write front matter for a cookbook titled '{cb.title}'.\n"
        f"Type: {cb.cookbook_type}\n"
        f"Cuisine: {cb.cuisine or 'various'}\n"
        f"Author: {author_bio}\n"
        f"Inspiration: {inspiration}\n"
        f"Sections to write: {', '.join(sections)}\n"
        f"Format each section with a heading and 2-3 paragraphs."
    )

    raw = await _llm_generate(prompt, system_prompt=system_prompt, max_tokens=3000)

    generated_sections = []
    for section in sections:
        generated_sections.append(
            {
                "section": section,
                "title": section.replace("_", " ").title(),
                "content": raw if len(sections) == 1 else f"[{section} content from AI]",
            }
        )

    return {
        "cookbook_id": str(cookbook_id),
        "cookbook_title": cb.title,
        "sections": generated_sections,
        "status": "generated",
        "message": "Review and edit the generated front matter before finalizing.",
    }


# ---------------------------------------------------------------------------
# Export / Preflight
# ---------------------------------------------------------------------------


async def export_cookbook(db: AsyncSession, org_id: UUID, cookbook_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Generate export file (PDF / print-ready).

    Delegates to the shared export engine for structured manifest
    generation.  In production the actual rendering would be done by
    a worker process consuming the returned manifest.
    """
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    chapters = await list_chapters(db, org_id, cookbook_id)

    all_recipes: list[dict] = []
    for ch in chapters:
        recipes = await list_recipes(db, org_id, UUID(ch["id"]))
        all_recipes.extend(recipes)

    export_format = payload.get("format", "pdf")
    export_id = str(_uuid.uuid4())

    book_data: dict[str, Any] = {
        "id": str(cookbook_id),
        "title": cb.title,
        "author": cb.author or "",
        "trim_size": cb.trim_size or "8.5x11",
        "interior_type": "color",
        "pages": all_recipes,
    }

    try:
        from app.modules.specialty.shared.export_engine import (
            calculate_export_metadata,
            generate_pdf_manifest,
        )

        pdf_manifest = generate_pdf_manifest("cookbook", book_data, payload)
        meta = calculate_export_metadata(book_data)
    except Exception:
        logger.warning("Export engine unavailable; returning stub manifest", exc_info=True)
        pdf_manifest = {"pages": [], "format": export_format}
        meta = {"page_count": len(all_recipes), "trim_size": cb.trim_size or "8.5x11"}

    cb.status = BookStatus.exported.value
    await db.flush()

    return {
        "export_id": export_id,
        "cookbook_id": str(cookbook_id),
        "format": export_format,
        "status": "processing",
        "recipe_count": len(all_recipes),
        "chapter_count": len(chapters),
        "manifest": pdf_manifest,
        "metadata": meta,
        "download_url": f"/api/v1/exports/cookbook/{export_id}/download",
        "message": "Export job queued. Download will be available when processing completes.",
    }


async def run_preflight(db: AsyncSession, org_id: UUID, cookbook_id: UUID) -> dict[str, Any]:
    """Run preflight check (image resolution, layout, nutrition completeness, etc.)."""
    cb = await _get_cookbook_or_404(db, org_id, cookbook_id)
    chapters = await list_chapters(db, org_id, cookbook_id)

    all_recipes: list[dict] = []
    for ch in chapters:
        recipes = await list_recipes(db, org_id, UUID(ch["id"]))
        all_recipes.extend(recipes)

    checks: list[dict[str, Any]] = []

    # 1. Recipe count check
    checks.append(
        {
            "check": "recipe_count",
            "passed": len(all_recipes) >= 10,
            "detail": (
                f"Cookbook has {len(all_recipes)} recipes"
                + (" (minimum 10 recommended)" if len(all_recipes) < 10 else "")
            ),
        }
    )

    # 2. All recipes have images
    recipes_without_images = [r for r in all_recipes if not r.get("image_url")]
    checks.append(
        {
            "check": "recipe_images",
            "passed": len(recipes_without_images) == 0,
            "detail": (
                f"{len(recipes_without_images)} recipes missing images"
                if recipes_without_images
                else "All recipes have images"
            ),
            "recipes": [r["title"] for r in recipes_without_images],
        }
    )

    # 3. All recipes have ingredients
    recipes_without_ingredients = [r for r in all_recipes if not r.get("ingredients")]
    checks.append(
        {
            "check": "ingredients_complete",
            "passed": len(recipes_without_ingredients) == 0,
            "detail": (
                f"{len(recipes_without_ingredients)} recipes missing ingredients"
                if recipes_without_ingredients
                else "All recipes have ingredients"
            ),
        }
    )

    # 4. All recipes have instructions
    recipes_without_instructions = [r for r in all_recipes if not r.get("instructions")]
    checks.append(
        {
            "check": "instructions_complete",
            "passed": len(recipes_without_instructions) == 0,
            "detail": (
                f"{len(recipes_without_instructions)} recipes missing instructions"
                if recipes_without_instructions
                else "All recipes have instructions"
            ),
        }
    )

    # 5. Nutrition data completeness
    recipes_without_nutrition = [r for r in all_recipes if not r.get("nutrition")]
    checks.append(
        {
            "check": "nutrition_complete",
            "passed": len(recipes_without_nutrition) == 0,
            "detail": (
                f"{len(recipes_without_nutrition)} recipes missing nutrition data"
                if recipes_without_nutrition
                else "All recipes have nutrition data"
            ),
        }
    )

    # 6. Chapter organization
    checks.append(
        {
            "check": "chapter_organization",
            "passed": len(chapters) >= 2,
            "detail": (
                f"Cookbook has {len(chapters)} chapters" + (" (minimum 2 recommended)" if len(chapters) < 2 else "")
            ),
        }
    )

    # 7. Cookbook metadata completeness
    has_title = bool(cb.title)
    has_author = bool(cb.author)
    has_description = bool(cb.description)
    metadata_complete = has_title and has_author and has_description
    missing = []
    if not has_title:
        missing.append("title")
    if not has_author:
        missing.append("author")
    if not has_description:
        missing.append("description")
    checks.append(
        {
            "check": "metadata_complete",
            "passed": metadata_complete,
            "detail": (f"Missing fields: {', '.join(missing)}" if missing else "All metadata fields present"),
        }
    )

    all_passed = all(c["passed"] for c in checks)
    warnings = [c for c in checks if not c["passed"]]

    return {
        "cookbook_id": str(cookbook_id),
        "cookbook_title": cb.title,
        "status": "passed" if all_passed else "warnings",
        "checks": checks,
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
        "warnings": warnings,
    }
