"""Cross-tenant isolation for the cookbook chapter/recipe/meal-plan surface.

Only Cookbook carries org_id; chapters, recipes and meal plans reach it by
join. The lookup helpers used to filter on ids alone, so a UUID belonging to
another organisation resolved for any caller. These tests pin that shut.
"""

import uuid

import pytest

from app.core.exceptions import NotFoundError
from app.modules.specialty.cookbook import service
from app.modules.specialty.models.cookbook import Cookbook, CookbookChapter, Recipe


async def _seed(db, org_id):
    cookbook = Cookbook(
        id=uuid.uuid4(),
        org_id=org_id,
        title="Org Cookbook",
        cookbook_type="cultural_cuisine",
        chapter_organization="by_course",
        recipe_layout="classic",
        illustration_method="ai_generated",
        interior_type="full_color",
        page_count=100,
        trim_size="8x10",
        include_nutrition=False,
        include_meal_plans=False,
        include_shopping_lists=False,
        include_index=False,
        include_conversion_charts=False,
        status="draft",
    )
    chapter = CookbookChapter(
        id=uuid.uuid4(),
        cookbook_id=cookbook.id,
        title="Mains",
        chapter_type="recipes",
        chapter_order=1,
    )
    recipe = Recipe(
        id=uuid.uuid4(),
        chapter_id=chapter.id,
        title="Secret Recipe",
        recipe_order=1,
        difficulty="easy",
        scaling_factor=1.0,
    )
    db.add_all([cookbook, chapter, recipe])
    await db.commit()
    return cookbook, chapter, recipe


@pytest.mark.asyncio
async def test_recipe_lookup_is_scoped_to_the_owning_org(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    _, _, recipe = await _seed(db_session, org_a)

    # the owner can read it
    owned = await service._get_recipe_or_404(db_session, org_a, recipe.id)
    assert owned.id == recipe.id

    # another organisation holding the same UUID cannot
    with pytest.raises(NotFoundError):
        await service._get_recipe_or_404(db_session, org_b, recipe.id)


@pytest.mark.asyncio
async def test_chapter_lookup_is_scoped_to_the_owning_org(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    cookbook, chapter, _ = await _seed(db_session, org_a)

    owned = await service._get_chapter_or_404(db_session, org_a, cookbook.id, chapter.id)
    assert owned.id == chapter.id

    with pytest.raises(NotFoundError):
        await service._get_chapter_or_404(db_session, org_b, cookbook.id, chapter.id)


@pytest.mark.asyncio
async def test_global_search_does_not_return_another_orgs_recipes(db_session):
    """Global search joins Recipe -> CookbookChapter -> Cookbook for org_id.

    The previous implementation imported Recipe from a module path that does
    not exist, so it always raised and returned []; the scoping guard beneath
    it collapsed to a literal True.
    """
    from app.modules.search import service as search_service

    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    await _seed(db_session, org_a)

    owner_hits = await search_service._search_recipes(db_session, org_a, "%Secret%")
    other_hits = await search_service._search_recipes(db_session, org_b, "%Secret%")

    assert [h.title for h in owner_hits] == ["Secret Recipe"]
    assert other_hits == []
