/**
 * TypeScript types for the Cookbook Studio.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type CookbookType =
  | "diet_lifestyle"
  | "recipe_collection"
  | "baking_desserts"
  | "cultural_cuisine"
  | "kids_family"
  | "fitness_meal_prep"
  | "quick_easy";

export type ChapterOrganization =
  | "by_meal"
  | "by_course"
  | "by_ingredient"
  | "by_cuisine"
  | "by_season"
  | "by_technique"
  | "by_occasion"
  | "custom";

export type RecipeLayout =
  | "classic"
  | "magazine"
  | "minimal"
  | "full_photo"
  | "step_by_step"
  | "card"
  | "two_column";

export type IllustrationMethod =
  | "ai_generated"
  | "stock_photos"
  | "user_uploaded"
  | "illustrated"
  | "no_illustrations"
  | "mixed";

export type CookbookInteriorType = "full_color" | "black_and_white" | "color_inserts";

export type RecipeDifficulty = "beginner" | "easy" | "intermediate" | "advanced" | "expert";

export type MealPlanType = "weekly" | "biweekly" | "monthly" | "custom";

export type ChapterType =
  | "recipes"
  | "introduction"
  | "techniques"
  | "ingredients_guide"
  | "meal_plans"
  | "index"
  | "about_author"
  | "acknowledgments"
  | "conversion_charts";

export type CookbookBookStatus = "draft" | "in_progress" | "published";

// ---------------------------------------------------------------------------
// Core interfaces
// ---------------------------------------------------------------------------

export interface Cookbook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author?: string;
  cookbook_type: CookbookType;
  cuisine?: string;
  cuisine_diet?: string;
  target_audience?: string;
  description?: string;
  chapter_organization: ChapterOrganization;
  recipe_layout: RecipeLayout;
  illustration_method: IllustrationMethod;
  interior_type: CookbookInteriorType;
  page_count: number;
  trim_size: string;
  include_nutrition: boolean;
  include_meal_plans: boolean;
  include_shopping_lists: boolean;
  include_index: boolean;
  include_conversion_charts: boolean;
  dietary_tags?: string[];
  status: CookbookBookStatus;
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CookbookChapter {
  id: string;
  cookbook_id: string;
  chapter_order: number;
  title: string;
  description?: string;
  introduction_text?: string;
  chapter_type: ChapterType;
  recipes?: CookbookRecipe[];
  created_at: string;
  updated_at: string;
}

export interface CookbookIngredient {
  name: string;
  amount: string;
  unit: string;
  notes?: string;
}

export interface CookbookInstructionStep {
  step: number;
  text: string;
  image_url?: string;
  tip?: string;
}

export interface CookbookNutritionInfo {
  calories: number;
  fat: number;
  protein: number;
  carbs: number;
  fiber?: number;
  sodium?: number;
  sugar?: number;
}

export interface CookbookRecipe {
  id: string;
  chapter_id: string;
  recipe_order: number;
  title: string;
  description?: string;
  servings?: string;
  prep_time_minutes?: number;
  cook_time_minutes?: number;
  total_time_minutes?: number;
  difficulty: RecipeDifficulty;
  ingredients?: CookbookIngredient[];
  instructions?: CookbookInstructionStep[];
  nutrition?: CookbookNutritionInfo;
  notes?: string;
  tips?: string;
  variations?: string[];
  tags?: string[];
  dietary_flags?: string[];
  image_url?: string;
  source?: string;
  scaling_factor: number;
  created_at: string;
  updated_at: string;
}

export interface CookbookMealPlan {
  id: string;
  cookbook_id: string;
  title: string;
  plan_type: MealPlanType;
  description?: string;
  days?: CookbookMealPlanDay[];
  total_calories_target?: number;
  dietary_goals?: Record<string, unknown>;
  shopping_list?: CookbookShoppingListItem[];
  created_at: string;
  updated_at: string;
}

export interface CookbookMealPlanDay {
  day: string;
  meals: {
    breakfast?: string;
    lunch?: string;
    dinner?: string;
    snack?: string;
  };
}

export interface CookbookShoppingListItem {
  name: string;
  amount: string;
  unit: string;
  category: string;
  checked: boolean;
}

// ---------------------------------------------------------------------------
// Wizard / creation payloads
// ---------------------------------------------------------------------------

export interface CreateCookbookRequest {
  title: string;
  subtitle?: string;
  author?: string;
  cookbook_type: CookbookType;
  cuisine?: string;
  cuisine_diet?: string;
  target_audience?: string;
  description?: string;
  chapter_organization: ChapterOrganization;
  recipe_layout: RecipeLayout;
  illustration_method: IllustrationMethod;
  interior_type: CookbookInteriorType;
  page_count: number;
  trim_size: string;
  include_nutrition: boolean;
  include_meal_plans: boolean;
  include_shopping_lists: boolean;
  include_index: boolean;
  include_conversion_charts: boolean;
  dietary_tags?: string[];
}

export interface UpdateCookbookRequest {
  title?: string;
  subtitle?: string;
  author?: string;
  cookbook_type?: CookbookType;
  status?: CookbookBookStatus;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export interface CookbookStats {
  total_cookbooks: number;
  in_progress: number;
  published: number;
  total_recipes: number;
  total_chapters: number;
}

// ---------------------------------------------------------------------------
// Paginated response
// ---------------------------------------------------------------------------

export interface CookbookPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
