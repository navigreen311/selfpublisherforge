"""SQLAlchemy models for Cookbooks."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel, BaseModel
from app.modules.specialty.models.enums import (
    BookStatus,
    ChapterOrganization,
    ChapterType,
    CookbookInteriorType,
    CookbookType,
    IllustrationMethod,
    MealPlanType,
    RecipeDifficulty,
    RecipeLayout,
)


class Cookbook(TenantModel):
    """Master record for a cookbook."""

    __tablename__ = "cookbooks"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)

    cookbook_type: Mapped[str] = mapped_column(
        Enum(CookbookType, name="cookbook_type", native_enum=True),
        nullable=False,
        default=CookbookType.general,
    )
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    chapter_organization: Mapped[str] = mapped_column(
        Enum(ChapterOrganization, name="chapter_organization", native_enum=True),
        nullable=False,
        default=ChapterOrganization.by_course,
    )
    recipe_layout: Mapped[str] = mapped_column(
        Enum(RecipeLayout, name="recipe_layout", native_enum=True),
        nullable=False,
        default=RecipeLayout.classic,
    )
    illustration_method: Mapped[str] = mapped_column(
        Enum(IllustrationMethod, name="cookbook_illustration_method", native_enum=True),
        nullable=False,
        default=IllustrationMethod.ai_generated,
    )
    interior_type: Mapped[str] = mapped_column(
        Enum(CookbookInteriorType, name="cookbook_interior_type", native_enum=True),
        nullable=False,
        default=CookbookInteriorType.full_color,
    )

    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    trim_size: Mapped[str] = mapped_column(
        String(20), nullable=False, default="8x10"
    )

    include_nutrition: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    include_meal_plans: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    include_shopping_lists: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    include_index: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    include_conversion_charts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    dietary_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(BookStatus, name="book_status", native_enum=True, create_constraint=False),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
    )
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    chapters: Mapped[list[CookbookChapter]] = relationship(
        "CookbookChapter",
        back_populates="cookbook",
        cascade="all, delete-orphan",
        order_by="CookbookChapter.chapter_order",
    )
    meal_plans: Mapped[list[MealPlan]] = relationship(
        "MealPlan",
        back_populates="cookbook",
        cascade="all, delete-orphan",
    )


class CookbookChapter(BaseModel):
    """Chapter in a cookbook."""

    __tablename__ = "cookbook_chapters"

    cookbook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cookbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    introduction_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chapter_type: Mapped[str] = mapped_column(
        Enum(ChapterType, name="cookbook_chapter_type", native_enum=True),
        nullable=False,
        default=ChapterType.recipes,
    )

    # Relationships
    cookbook: Mapped[Cookbook] = relationship("Cookbook", back_populates="chapters")
    recipes: Mapped[list[Recipe]] = relationship(
        "Recipe",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Recipe.recipe_order",
    )


class Recipe(BaseModel):
    """Individual recipe in a cookbook chapter."""

    __tablename__ = "cookbook_recipes"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cookbook_chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    servings: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    difficulty: Mapped[str] = mapped_column(
        Enum(RecipeDifficulty, name="recipe_difficulty", native_enum=True),
        nullable=False,
        default=RecipeDifficulty.easy,
    )

    ingredients: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # Each ingredient: {"name": "flour", "amount": "2", "unit": "cups", "notes": "sifted"}

    instructions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # Each step: {"step": 1, "text": "Preheat oven...", "image_url": null, "tip": null}

    nutrition: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"calories": 350, "fat": 12, "protein": 8, "carbs": 45, "fiber": 3, "sodium": 400}

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tips: Mapped[str | None] = mapped_column(Text, nullable=True)
    variations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    dietary_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # e.g., ["vegetarian", "gluten_free", "dairy_free"]

    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scaling_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Relationships
    chapter: Mapped[CookbookChapter] = relationship(
        "CookbookChapter", back_populates="recipes"
    )


class MealPlan(BaseModel):
    """Meal plan associated with a cookbook."""

    __tablename__ = "cookbook_meal_plans"

    cookbook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cookbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    plan_type: Mapped[str] = mapped_column(
        Enum(MealPlanType, name="meal_plan_type", native_enum=True),
        nullable=False,
        default=MealPlanType.weekly,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    days: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # Each day: {"day": "Monday", "meals": {"breakfast": recipe_id, "lunch": recipe_id, "dinner": recipe_id, "snack": recipe_id}}

    total_calories_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dietary_goals: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    shopping_list: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    cookbook: Mapped[Cookbook] = relationship("Cookbook", back_populates="meal_plans")
