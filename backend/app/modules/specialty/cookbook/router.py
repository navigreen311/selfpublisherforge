"""FastAPI router for the Cookbook Studio.

Endpoints cover full CRUD for cookbooks, chapters, recipes, and meal plans,
plus AI recipe generation, nutrition calculation, recipe scaling, shopping
lists, index generation, and export/preflight.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import PaginatedResponse, SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.cookbook import service
from app.modules.specialty.models.enums import BookStatus, CookbookType

router = APIRouter(prefix="/specialty/cookbook-books", tags=["cookbook-books"])


# ---------------------------------------------------------------------------
# Cookbook CRUD
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[PaginatedResponse[dict]],
    summary="List cookbooks (paginated)",
)
async def list_cookbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BookStatus | None = Query(None, alias="status"),
    type_filter: CookbookType | None = Query(None, alias="type"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.list_cookbooks(
        db,
        current_user["org_id"],
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        type_filter=type_filter,
        search=search,
    )
    return SuccessResponse(data=result)


@router.post(
    "",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cookbook",
)
async def create_cookbook(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cookbook = await service.create_cookbook(db, current_user["org_id"], payload)
    return SuccessResponse(data=cookbook)


@router.get(
    "/stats",
    response_model=SuccessResponse[dict],
    summary="Get cookbook stats",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.get_stats(db, current_user["org_id"])
    return SuccessResponse(data=result)


@router.get(
    "/{cookbook_id}",
    response_model=SuccessResponse[dict],
    summary="Get cookbook detail",
)
async def get_cookbook(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cookbook = await service.get_cookbook(db, current_user["org_id"], cookbook_id)
    return SuccessResponse(data=cookbook)


@router.patch(
    "/{cookbook_id}",
    response_model=SuccessResponse[dict],
    summary="Update a cookbook",
)
async def update_cookbook(
    cookbook_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cookbook = await service.update_cookbook(db, current_user["org_id"], cookbook_id, payload)
    return SuccessResponse(data=cookbook)


@router.delete(
    "/{cookbook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a cookbook",
)
async def delete_cookbook(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_cookbook(db, current_user["org_id"], cookbook_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cookbook not found")
    return


# ---------------------------------------------------------------------------
# Chapter CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/{cookbook_id}/chapters",
    response_model=SuccessResponse[list[dict]],
    summary="List chapters",
)
async def list_chapters(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chapters = await service.list_chapters(db, current_user["org_id"], cookbook_id)
    return SuccessResponse(data=chapters)


@router.post(
    "/{cookbook_id}/chapters",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a chapter",
)
async def create_chapter(
    cookbook_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chapter = await service.create_chapter(db, current_user["org_id"], cookbook_id, payload)
    return SuccessResponse(data=chapter)


@router.patch(
    "/{cookbook_id}/chapters/{chapter_id}",
    response_model=SuccessResponse[dict],
    summary="Update a chapter",
)
async def update_chapter(
    cookbook_id: UUID,
    chapter_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chapter = await service.update_chapter(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_id,
        payload,
    )
    return SuccessResponse(data=chapter)


@router.delete(
    "/{cookbook_id}/chapters/{chapter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chapter",
)
async def delete_chapter(
    cookbook_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_chapter(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return


@router.post(
    "/{cookbook_id}/chapters/reorder",
    response_model=SuccessResponse[list[dict]],
    summary="Reorder chapters",
)
async def reorder_chapters(
    cookbook_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expects ``{"chapter_ids": [uuid, uuid, ...]}`` in desired order."""
    chapter_ids = payload.get("chapter_ids", [])
    chapters = await service.reorder_chapters(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_ids,
    )
    return SuccessResponse(data=chapters)


# ---------------------------------------------------------------------------
# Recipe CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/{cookbook_id}/chapters/{chapter_id}/recipes",
    response_model=SuccessResponse[list[dict]],
    summary="List recipes in chapter",
)
async def list_recipes(
    cookbook_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    recipes = await service.list_recipes(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_id,
    )
    return SuccessResponse(data=recipes)


@router.post(
    "/{cookbook_id}/chapters/{chapter_id}/recipes",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a recipe",
)
async def create_recipe(
    cookbook_id: UUID,
    chapter_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    recipe = await service.create_recipe(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_id,
        payload,
    )
    return SuccessResponse(data=recipe)


@router.get(
    "/{cookbook_id}/recipes/{recipe_id}",
    response_model=SuccessResponse[dict],
    summary="Get recipe detail",
)
async def get_recipe(
    cookbook_id: UUID,
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    recipe = await service.get_recipe(
        db,
        current_user["org_id"],
        recipe_id,
    )
    return SuccessResponse(data=recipe)


@router.patch(
    "/{cookbook_id}/recipes/{recipe_id}",
    response_model=SuccessResponse[dict],
    summary="Update a recipe",
)
async def update_recipe(
    cookbook_id: UUID,
    recipe_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    recipe = await service.update_recipe(
        db,
        current_user["org_id"],
        recipe_id,
        payload,
    )
    return SuccessResponse(data=recipe)


@router.delete(
    "/{cookbook_id}/recipes/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recipe",
)
async def delete_recipe(
    cookbook_id: UUID,
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_recipe(
        db,
        current_user["org_id"],
        recipe_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return


@router.post(
    "/{cookbook_id}/chapters/{chapter_id}/recipes/reorder",
    response_model=SuccessResponse[list[dict]],
    summary="Reorder recipes",
)
async def reorder_recipes(
    cookbook_id: UUID,
    chapter_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expects ``{"recipe_ids": [uuid, uuid, ...]}`` in desired order."""
    recipe_ids = payload.get("recipe_ids", [])
    recipes = await service.reorder_recipes(
        db,
        current_user["org_id"],
        cookbook_id,
        chapter_id,
        recipe_ids,
    )
    return SuccessResponse(data=recipes)


# ---------------------------------------------------------------------------
# AI Recipe Operations
# ---------------------------------------------------------------------------


@router.post(
    "/{cookbook_id}/generate-recipe",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate a recipe",
)
async def generate_recipe(
    cookbook_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_recipe(
        db,
        current_user["org_id"],
        cookbook_id,
        payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/recipes/{recipe_id}/generate-image",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate food photo",
)
async def generate_recipe_image(
    cookbook_id: UUID,
    recipe_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_recipe_image(
        db,
        current_user["org_id"],
        recipe_id,
        payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/recipes/{recipe_id}/improve",
    response_model=SuccessResponse[dict],
    summary="AI-improve recipe instructions",
)
async def improve_recipe(
    cookbook_id: UUID,
    recipe_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.improve_recipe(
        db,
        current_user["org_id"],
        recipe_id,
        payload or {},
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Nutrition
# ---------------------------------------------------------------------------


@router.post(
    "/{cookbook_id}/recipes/{recipe_id}/nutrition",
    response_model=SuccessResponse[dict],
    summary="Calculate nutrition for recipe",
)
async def calculate_nutrition(
    cookbook_id: UUID,
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.calculate_nutrition(
        db,
        current_user["org_id"],
        recipe_id,
    )
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/batch-nutrition",
    response_model=SuccessResponse[dict],
    summary="Calculate nutrition for all recipes",
)
async def batch_nutrition(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.batch_nutrition(
        db,
        current_user["org_id"],
        cookbook_id,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Scaling
# ---------------------------------------------------------------------------


@router.post(
    "/{cookbook_id}/recipes/{recipe_id}/scale",
    response_model=SuccessResponse[dict],
    summary="Scale recipe ingredients",
)
async def scale_recipe(
    cookbook_id: UUID,
    recipe_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expects ``{"factor": 2.0}`` in body."""
    factor = float(payload.get("factor", 1.0))
    result = await service.scale_recipe(
        db,
        current_user["org_id"],
        recipe_id,
        factor,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Meal Plans
# ---------------------------------------------------------------------------


@router.get(
    "/{cookbook_id}/meal-plans",
    response_model=SuccessResponse[list[dict]],
    summary="List meal plans",
)
async def list_meal_plans(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    plans = await service.list_meal_plans(db, current_user["org_id"], cookbook_id)
    return SuccessResponse(data=plans)


@router.post(
    "/{cookbook_id}/meal-plans",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal plan",
)
async def create_meal_plan(
    cookbook_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    plan = await service.create_meal_plan(db, current_user["org_id"], cookbook_id, payload)
    return SuccessResponse(data=plan)


@router.patch(
    "/{cookbook_id}/meal-plans/{plan_id}",
    response_model=SuccessResponse[dict],
    summary="Update a meal plan",
)
async def update_meal_plan(
    cookbook_id: UUID,
    plan_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    plan = await service.update_meal_plan(
        db,
        current_user["org_id"],
        cookbook_id,
        plan_id,
        payload,
    )
    return SuccessResponse(data=plan)


@router.delete(
    "/{cookbook_id}/meal-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a meal plan",
)
async def delete_meal_plan(
    cookbook_id: UUID,
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_meal_plan(
        db,
        current_user["org_id"],
        cookbook_id,
        plan_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
    return


@router.post(
    "/{cookbook_id}/meal-plans/{plan_id}/auto-fill",
    response_model=SuccessResponse[dict],
    summary="AI auto-fill meal plan",
)
async def auto_fill_meal_plan(
    cookbook_id: UUID,
    plan_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.auto_fill_meal_plan(
        db,
        current_user["org_id"],
        cookbook_id,
        plan_id,
        payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/meal-plans/{plan_id}/shopping-list",
    response_model=SuccessResponse[dict],
    summary="Generate shopping list from meal plan",
)
async def generate_shopping_list(
    cookbook_id: UUID,
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_shopping_list(
        db,
        current_user["org_id"],
        plan_id,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Index & Front Matter
# ---------------------------------------------------------------------------


@router.post(
    "/{cookbook_id}/generate-index",
    response_model=SuccessResponse[dict],
    summary="Generate recipe index",
)
async def generate_index(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_index(db, current_user["org_id"], cookbook_id)
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/generate-front-matter",
    response_model=SuccessResponse[dict],
    summary="AI-generate front matter",
)
async def generate_front_matter(
    cookbook_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_front_matter(
        db,
        current_user["org_id"],
        cookbook_id,
        payload or {},
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Export / Preflight
# ---------------------------------------------------------------------------


@router.post(
    "/{cookbook_id}/export",
    response_model=SuccessResponse[dict],
    summary="Generate export file",
)
async def export_cookbook(
    cookbook_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.export_cookbook(
        db,
        current_user["org_id"],
        cookbook_id,
        payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{cookbook_id}/preflight",
    response_model=SuccessResponse[dict],
    summary="Run preflight check",
)
async def preflight(
    cookbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_preflight(db, current_user["org_id"], cookbook_id)
    return SuccessResponse(data=result)
