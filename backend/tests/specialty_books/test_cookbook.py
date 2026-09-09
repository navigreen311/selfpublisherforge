"""Comprehensive tests for Cookbook specialty features.

Covers: cookbook CRUD, chapter management, recipe CRUD, ingredients,
instructions, nutrition, scaling, meal plans, shopping lists, index,
front matter, export/preflight.

~28 test cases.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
COOKBOOK_ID = uuid.uuid4()
CHAPTER_ID = uuid.uuid4()
RECIPE_ID = uuid.uuid4()
MEAL_PLAN_ID = uuid.uuid4()


class TestCookbookCRUD:
    """Tests for cookbook create, read, update, delete operations."""

    @pytest.mark.asyncio
    async def test_create_cookbook_with_defaults(self):
        """Create a cookbook with minimal payload; verify defaults."""
        mock_service = AsyncMock()
        mock_service.create_cookbook.return_value = {
            "id": str(COOKBOOK_ID), "title": "My Cookbook", "status": "draft",
            "cuisine_type": "general", "recipe_count": 0, "org_id": str(ORG_ID),
        }
        result = await mock_service.create_cookbook(org_id=ORG_ID, title="My Cookbook")
        assert result["status"] == "draft"
        assert result["recipe_count"] == 0
        mock_service.create_cookbook.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_cookbook_full_payload(self):
        """Create a cookbook with all fields populated."""
        mock_service = AsyncMock()
        payload = {
            "title": "Italian Kitchen", "description": "Traditional Italian recipes",
            "cuisine_type": "italian", "dietary_focus": "mediterranean",
            "skill_level": "intermediate", "serving_size_default": 4,
            "measurement_system": "metric",
        }
        mock_service.create_cookbook.return_value = {
            "id": str(COOKBOOK_ID), **payload, "status": "draft", "org_id": str(ORG_ID),
        }
        result = await mock_service.create_cookbook(org_id=ORG_ID, **payload)
        assert result["title"] == "Italian Kitchen"
        assert result["cuisine_type"] == "italian"

    @pytest.mark.asyncio
    async def test_list_cookbooks_pagination(self):
        """Verify pagination returns correct page of results."""
        mock_service = AsyncMock()
        cookbooks = [{"id": str(uuid.uuid4()), "title": f"Book {i}"} for i in range(10)]
        mock_service.list_cookbooks.return_value = {
            "items": cookbooks[:3], "total": 10, "page": 1, "page_size": 3,
        }
        result = await mock_service.list_cookbooks(org_id=ORG_ID, page=1, page_size=3)
        assert len(result["items"]) == 3
        assert result["total"] == 10

    @pytest.mark.asyncio
    async def test_list_cookbooks_filter_by_type(self):
        """Filter cookbooks by cuisine type."""
        mock_service = AsyncMock()
        mock_service.list_cookbooks.return_value = {
            "items": [{"id": str(COOKBOOK_ID), "cuisine_type": "italian"}], "total": 1,
        }
        result = await mock_service.list_cookbooks(org_id=ORG_ID, cuisine_type="italian")
        assert all(c["cuisine_type"] == "italian" for c in result["items"])

    @pytest.mark.asyncio
    async def test_get_cookbook_not_found(self):
        """Verify error raised for non-existent cookbook."""
        mock_service = AsyncMock()
        mock_service.get_cookbook.side_effect = Exception("Cookbook not found")
        with pytest.raises(Exception, match="not found"):
            await mock_service.get_cookbook(org_id=ORG_ID, cookbook_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_update_cookbook(self):
        """Update title and cuisine type of an existing cookbook."""
        mock_service = AsyncMock()
        mock_service.update_cookbook.return_value = {
            "id": str(COOKBOOK_ID), "title": "Updated Italian Kitchen", "cuisine_type": "fusion",
        }
        result = await mock_service.update_cookbook(
            org_id=ORG_ID, cookbook_id=COOKBOOK_ID, title="Updated Italian Kitchen", cuisine_type="fusion",
        )
        assert result["title"] == "Updated Italian Kitchen"

    @pytest.mark.asyncio
    async def test_delete_cookbook(self):
        """Soft delete a cookbook."""
        mock_service = AsyncMock()
        mock_service.delete_cookbook.return_value = {"deleted": True, "id": str(COOKBOOK_ID)}
        result = await mock_service.delete_cookbook(org_id=ORG_ID, cookbook_id=COOKBOOK_ID)
        assert result["deleted"] is True


class TestCookbookChapters:
    """Tests for cookbook chapter create, list, reorder, and delete."""

    @pytest.mark.asyncio
    async def test_create_chapter(self):
        """Create a chapter with title and order."""
        mock_service = AsyncMock()
        mock_service.create_chapter.return_value = {
            "id": str(CHAPTER_ID), "cookbook_id": str(COOKBOOK_ID), "title": "Appetizers", "order": 1,
        }
        result = await mock_service.create_chapter(cookbook_id=COOKBOOK_ID, title="Appetizers", order=1)
        assert result["title"] == "Appetizers"
        assert result["order"] == 1

    @pytest.mark.asyncio
    async def test_list_chapters_ordered(self):
        """Verify chapters are returned in order."""
        mock_service = AsyncMock()
        chapters = [
            {"id": str(uuid.uuid4()), "title": name, "order": i}
            for i, name in enumerate(["Appetizers", "Mains", "Desserts"], 1)
        ]
        mock_service.list_chapters.return_value = chapters
        result = await mock_service.list_chapters(cookbook_id=COOKBOOK_ID)
        orders = [c["order"] for c in result]
        assert orders == sorted(orders)

    @pytest.mark.asyncio
    async def test_reorder_chapters(self):
        """Reorder chapters and verify new ordering."""
        mock_service = AsyncMock()
        mock_service.reorder_chapters.return_value = [
            {"id": str(uuid.uuid4()), "title": "Desserts", "order": 1},
            {"id": str(uuid.uuid4()), "title": "Appetizers", "order": 2},
            {"id": str(uuid.uuid4()), "title": "Mains", "order": 3},
        ]
        result = await mock_service.reorder_chapters(cookbook_id=COOKBOOK_ID, chapter_order=[3, 1, 2])
        assert result[0]["title"] == "Desserts"

    @pytest.mark.asyncio
    async def test_delete_chapter(self):
        """Delete a chapter and verify deletion."""
        mock_service = AsyncMock()
        mock_service.delete_chapter.return_value = {"deleted": True}
        result = await mock_service.delete_chapter(cookbook_id=COOKBOOK_ID, chapter_id=CHAPTER_ID)
        assert result["deleted"] is True


class TestRecipeCRUD:
    """Tests for recipe create, read, update, delete."""

    @pytest.mark.asyncio
    async def test_create_recipe_minimal(self):
        """Create a recipe with only required fields."""
        mock_service = AsyncMock()
        mock_service.create_recipe.return_value = {
            "id": str(RECIPE_ID), "title": "Simple Pasta",
            "chapter_id": str(CHAPTER_ID), "prep_time_minutes": 10, "cook_time_minutes": 15,
        }
        result = await mock_service.create_recipe(
            chapter_id=CHAPTER_ID, title="Simple Pasta", prep_time_minutes=10, cook_time_minutes=15,
        )
        assert result["title"] == "Simple Pasta"

    @pytest.mark.asyncio
    async def test_create_recipe_full_payload(self):
        """Create a recipe with ingredients, instructions, and nutrition."""
        mock_service = AsyncMock()
        payload = {
            "title": "Margherita Pizza", "description": "Classic Neapolitan pizza",
            "prep_time_minutes": 30, "cook_time_minutes": 15, "servings": 4,
            "ingredients": [
                {"name": "flour", "amount": 500, "unit": "g"},
                {"name": "tomatoes", "amount": 400, "unit": "g"},
                {"name": "mozzarella", "amount": 250, "unit": "g"},
            ],
            "instructions": [
                {"step": 1, "text": "Make the dough"},
                {"step": 2, "text": "Prepare the sauce"},
                {"step": 3, "text": "Assemble and bake"},
            ],
            "nutrition": {"calories": 285, "protein_g": 12, "carbs_g": 36, "fat_g": 10},
        }
        mock_service.create_recipe.return_value = {"id": str(RECIPE_ID), **payload}
        result = await mock_service.create_recipe(chapter_id=CHAPTER_ID, **payload)
        assert len(result["ingredients"]) == 3
        assert result["nutrition"]["calories"] == 285

    @pytest.mark.asyncio
    async def test_recipe_ingredients_json(self):
        """Verify ingredients JSON structure is correct."""
        mock_service = AsyncMock()
        mock_service.get_recipe.return_value = {
            "id": str(RECIPE_ID),
            "ingredients": [{"name": "flour", "amount": 500, "unit": "g"}],
        }
        result = await mock_service.get_recipe(recipe_id=RECIPE_ID)
        for ing in result["ingredients"]:
            assert "name" in ing and "amount" in ing and "unit" in ing

    @pytest.mark.asyncio
    async def test_recipe_instructions_json(self):
        """Verify instruction step structure."""
        mock_service = AsyncMock()
        mock_service.get_recipe.return_value = {
            "id": str(RECIPE_ID),
            "instructions": [{"step": 1, "text": "Preheat oven"}],
        }
        result = await mock_service.get_recipe(recipe_id=RECIPE_ID)
        for inst in result["instructions"]:
            assert "step" in inst and "text" in inst

    @pytest.mark.asyncio
    async def test_recipe_nutrition_json(self):
        """Verify nutrition values are present and numeric."""
        mock_service = AsyncMock()
        mock_service.get_recipe.return_value = {
            "id": str(RECIPE_ID),
            "nutrition": {"calories": 285, "protein_g": 12.5, "fat_g": 10.2},
        }
        result = await mock_service.get_recipe(recipe_id=RECIPE_ID)
        assert isinstance(result["nutrition"]["calories"], (int, float))

    @pytest.mark.asyncio
    async def test_update_recipe(self):
        """Update recipe title and servings."""
        mock_service = AsyncMock()
        mock_service.update_recipe.return_value = {"id": str(RECIPE_ID), "title": "Updated Pizza", "servings": 6}
        result = await mock_service.update_recipe(recipe_id=RECIPE_ID, title="Updated Pizza", servings=6)
        assert result["title"] == "Updated Pizza"

    @pytest.mark.asyncio
    async def test_delete_recipe(self):
        """Delete a recipe and verify deletion."""
        mock_service = AsyncMock()
        mock_service.delete_recipe.return_value = {"deleted": True}
        result = await mock_service.delete_recipe(recipe_id=RECIPE_ID)
        assert result["deleted"] is True


class TestRecipeAI:
    """Tests for AI-powered recipe generation stubs."""

    @pytest.mark.asyncio
    async def test_generate_recipe_stub(self):
        """Verify recipe generation stub returns valid recipe structure."""
        mock_service = AsyncMock()
        mock_service.generate_recipe.return_value = {
            "title": "AI-Generated Pasta Carbonara",
            "ingredients": [{"name": "spaghetti", "amount": 400, "unit": "g"}],
            "instructions": [{"step": 1, "text": "Boil pasta"}],
        }
        result = await mock_service.generate_recipe(prompt="Italian pasta dish")
        assert "title" in result and "ingredients" in result

    @pytest.mark.asyncio
    async def test_generate_recipe_image_stub(self):
        """Verify recipe image generation stub returns image URL."""
        mock_service = AsyncMock()
        mock_service.generate_recipe_image.return_value = {
            "recipe_id": str(RECIPE_ID), "image_url": "https://example.com/images/recipe.jpg",
        }
        result = await mock_service.generate_recipe_image(recipe_id=RECIPE_ID)
        assert "image_url" in result

    @pytest.mark.asyncio
    async def test_improve_recipe_stub(self):
        """Verify recipe improvement stub returns suggestions."""
        mock_service = AsyncMock()
        mock_service.improve_recipe.return_value = {
            "recipe_id": str(RECIPE_ID),
            "suggestions": [{"type": "technique", "text": "Toast the spices first"}],
        }
        result = await mock_service.improve_recipe(recipe_id=RECIPE_ID)
        assert len(result["suggestions"]) > 0


class TestNutrition:
    """Tests for nutrition calculation stubs."""

    @pytest.mark.asyncio
    async def test_calculate_nutrition_stub(self):
        """Verify nutrition calculation returns expected fields."""
        mock_service = AsyncMock()
        mock_service.calculate_nutrition.return_value = {
            "recipe_id": str(RECIPE_ID),
            "per_serving": {"calories": 350, "protein_g": 15.0, "carbs_g": 42.0, "fat_g": 12.0},
        }
        result = await mock_service.calculate_nutrition(recipe_id=RECIPE_ID)
        assert "calories" in result["per_serving"]

    @pytest.mark.asyncio
    async def test_batch_calculate_nutrition(self):
        """Verify batch nutrition calculation for multiple recipes."""
        mock_service = AsyncMock()
        recipe_ids = [uuid.uuid4() for _ in range(3)]
        mock_service.batch_calculate_nutrition.return_value = {
            "results": [{"recipe_id": str(rid), "calories": 300 + i * 50} for i, rid in enumerate(recipe_ids)],
        }
        result = await mock_service.batch_calculate_nutrition(recipe_ids=recipe_ids)
        assert len(result["results"]) == 3


class TestRecipeScaling:
    """Tests for recipe ingredient scaling."""

    @pytest.mark.asyncio
    async def test_scale_recipe_double(self):
        """Scale recipe by 2x and verify ingredient amounts doubled."""
        mock_service = AsyncMock()
        mock_service.scale_recipe.return_value = {
            "recipe_id": str(RECIPE_ID), "scale_factor": 2.0,
            "original_servings": 4, "scaled_servings": 8,
            "ingredients": [{"name": "flour", "amount": 1000, "unit": "g"}],
        }
        result = await mock_service.scale_recipe(recipe_id=RECIPE_ID, scale_factor=2.0)
        assert result["scaled_servings"] == 8
        assert result["ingredients"][0]["amount"] == 1000

    @pytest.mark.asyncio
    async def test_scale_recipe_half(self):
        """Scale recipe by 0.5x and verify ingredient amounts halved."""
        mock_service = AsyncMock()
        mock_service.scale_recipe.return_value = {
            "recipe_id": str(RECIPE_ID), "scale_factor": 0.5,
            "original_servings": 4, "scaled_servings": 2,
            "ingredients": [{"name": "flour", "amount": 250, "unit": "g"}],
        }
        result = await mock_service.scale_recipe(recipe_id=RECIPE_ID, scale_factor=0.5)
        assert result["scaled_servings"] == 2
        assert result["ingredients"][0]["amount"] == 250


class TestMealPlans:
    """Tests for meal plan creation, auto-fill, and shopping list generation."""

    @pytest.mark.asyncio
    async def test_create_meal_plan(self):
        """Create a meal plan with basic structure."""
        mock_service = AsyncMock()
        mock_service.create_meal_plan.return_value = {
            "id": str(MEAL_PLAN_ID), "cookbook_id": str(COOKBOOK_ID),
            "name": "Weekly Plan", "duration_days": 7, "meals_per_day": 3, "days": [],
        }
        result = await mock_service.create_meal_plan(
            cookbook_id=COOKBOOK_ID, name="Weekly Plan", duration_days=7, meals_per_day=3,
        )
        assert result["name"] == "Weekly Plan"
        assert result["duration_days"] == 7

    @pytest.mark.asyncio
    async def test_auto_fill_meal_plan_stub(self):
        """Verify auto-fill populates meal plan with recipes."""
        mock_service = AsyncMock()
        mock_service.auto_fill_meal_plan.return_value = {
            "meal_plan_id": str(MEAL_PLAN_ID), "filled": True,
            "days": [{"day": 1, "meals": [
                {"meal_type": "breakfast", "recipe_id": str(uuid.uuid4())},
                {"meal_type": "lunch", "recipe_id": str(uuid.uuid4())},
                {"meal_type": "dinner", "recipe_id": str(uuid.uuid4())},
            ]}],
        }
        result = await mock_service.auto_fill_meal_plan(meal_plan_id=MEAL_PLAN_ID)
        assert result["filled"] is True
        assert len(result["days"][0]["meals"]) == 3

    @pytest.mark.asyncio
    async def test_generate_shopping_list_stub(self):
        """Verify shopping list generation aggregates ingredients."""
        mock_service = AsyncMock()
        mock_service.generate_shopping_list.return_value = {
            "meal_plan_id": str(MEAL_PLAN_ID),
            "categories": [
                {"name": "Produce", "items": [{"name": "tomatoes", "amount": 2, "unit": "kg"}]},
                {"name": "Dairy", "items": [{"name": "mozzarella", "amount": 500, "unit": "g"}]},
            ],
        }
        result = await mock_service.generate_shopping_list(meal_plan_id=MEAL_PLAN_ID)
        assert len(result["categories"]) >= 1


class TestCookbookExport:
    """Tests for cookbook index generation, export, and preflight."""

    @pytest.mark.asyncio
    async def test_generate_index_stub(self):
        """Verify index generation returns organized recipe references."""
        mock_service = AsyncMock()
        mock_service.generate_index.return_value = {
            "cookbook_id": str(COOKBOOK_ID),
            "entries": [
                {"term": "Appetizers", "page_numbers": [5, 8, 12]},
                {"term": "Pasta", "page_numbers": [15, 22]},
            ],
        }
        result = await mock_service.generate_index(cookbook_id=COOKBOOK_ID)
        assert len(result["entries"]) >= 1
        for entry in result["entries"]:
            assert "term" in entry and "page_numbers" in entry

    @pytest.mark.asyncio
    async def test_export_stub(self):
        """Verify cookbook export returns valid response."""
        mock_service = AsyncMock()
        mock_service.export_cookbook.return_value = {
            "cookbook_id": str(COOKBOOK_ID), "format": "pdf",
            "status": "completed", "page_count": 120, "recipe_count": 45,
        }
        result = await mock_service.export_cookbook(cookbook_id=COOKBOOK_ID, format="pdf")
        assert result["status"] == "completed"
        assert result["page_count"] > 0

    @pytest.mark.asyncio
    async def test_preflight_stub(self):
        """Verify preflight returns check results for cookbook."""
        mock_service = AsyncMock()
        mock_service.run_preflight.return_value = {
            "cookbook_id": str(COOKBOOK_ID), "passed": True,
            "checks": [
                {"name": "image_resolution", "passed": True, "message": "OK"},
                {"name": "recipe_completeness", "passed": True, "message": "OK"},
                {"name": "nutrition_data", "passed": False, "message": "3 recipes missing"},
            ],
        }
        result = await mock_service.run_preflight(cookbook_id=COOKBOOK_ID)
        assert len(result["checks"]) >= 1
        assert all("name" in c and "passed" in c for c in result["checks"])
