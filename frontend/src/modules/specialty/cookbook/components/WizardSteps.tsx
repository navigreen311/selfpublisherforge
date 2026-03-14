"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Leaf,
  BookOpen,
  Cake,
  Globe,
  Users,
  Dumbbell,
  Timer,
  Plus,
  X,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Wizard Data Type
// ---------------------------------------------------------------------------

export type CookbookType =
  | "diet_lifestyle"
  | "recipe_collection"
  | "baking_desserts"
  | "cultural_cuisine"
  | "kids_family"
  | "fitness_meal_prep"
  | "quick_easy";

export const CUISINE_DIET_OPTIONS = [
  "Ketogenic",
  "Paleo",
  "Vegetarian",
  "Vegan",
  "Mediterranean",
  "Whole30",
  "Low-Carb",
  "Gluten-Free",
  "Dairy-Free",
  "Custom",
] as const;

export interface WizardData {
  // Step 1: Details
  title: string;
  subtitle: string;
  author: string;
  cookbook_type: CookbookType | "";
  cuisine: string;
  cuisine_diet: string;
  target_audience: string;
  description: string;

  // Step 2: Format
  trim_size: string;
  interior_type: string;
  chapter_organization: string;
  initial_chapters: string[];

  // Step 3: Recipe Settings
  recipe_layout: string;
  illustration_method: string;
  include_nutrition: boolean;
  include_meal_plans: boolean;
  include_shopping_lists: boolean;
  include_index: boolean;
  include_conversion_charts: boolean;
  dietary_tags: string[];
}

export const DEFAULT_WIZARD_DATA: WizardData = {
  title: "",
  subtitle: "",
  author: "",
  cookbook_type: "",
  cuisine: "",
  cuisine_diet: "",
  target_audience: "",
  description: "",

  trim_size: "8x10",
  interior_type: "full_color",
  chapter_organization: "by_course",
  initial_chapters: [],

  recipe_layout: "classic",
  illustration_method: "ai_generated",
  include_nutrition: true,
  include_meal_plans: false,
  include_shopping_lists: false,
  include_index: true,
  include_conversion_charts: true,
  dietary_tags: [],
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const COOKBOOK_TYPES: {
  value: CookbookType;
  label: string;
  desc: string;
  icon: typeof Leaf;
}[] = [
  {
    value: "diet_lifestyle",
    label: "Diet / Lifestyle",
    desc: "Keto, Paleo, etc.",
    icon: Leaf,
  },
  {
    value: "recipe_collection",
    label: "Recipe Collection",
    desc: "100+ recipes",
    icon: BookOpen,
  },
  {
    value: "baking_desserts",
    label: "Baking & Desserts",
    desc: "Sweet treats and pastries",
    icon: Cake,
  },
  {
    value: "cultural_cuisine",
    label: "Cultural Cuisine",
    desc: "Italian, Mexican, Thai, etc.",
    icon: Globe,
  },
  {
    value: "kids_family",
    label: "Kids & Family",
    desc: "Family-friendly recipes",
    icon: Users,
  },
  {
    value: "fitness_meal_prep",
    label: "Fitness / Meal Prep",
    desc: "Healthy meal planning",
    icon: Dumbbell,
  },
  {
    value: "quick_easy",
    label: "Quick & Easy",
    desc: "30-minute meals",
    icon: Timer,
  },
];

const TRIM_SIZES = [
  { value: "6x9", label: '6" x 9" (Standard)' },
  { value: "7x10", label: '7" x 10" (Large)' },
  { value: "8x10", label: '8" x 10" (Coffee Table)' },
  { value: "8.5x11", label: '8.5" x 11" (Full Size)' },
  { value: "5.5x8.5", label: '5.5" x 8.5" (Compact)' },
];

const INTERIOR_TYPES = [
  { value: "full_color", label: "Full Color", desc: "Color throughout" },
  { value: "black_white", label: "Black & White", desc: "B&W interior" },
  {
    value: "color_inserts",
    label: "Color Inserts",
    desc: "B&W with color photo section",
  },
];

const CHAPTER_ORGANIZATIONS = [
  { value: "by_meal", label: "By Meal", desc: "Breakfast / Lunch / Dinner" },
  {
    value: "by_course",
    label: "By Course",
    desc: "Appetizer / Main / Dessert",
  },
  {
    value: "by_ingredient",
    label: "By Ingredient",
    desc: "Poultry / Seafood / Vegetables",
  },
  {
    value: "by_cuisine",
    label: "By Cuisine",
    desc: "Italian / Mexican / Asian",
  },
  {
    value: "by_season",
    label: "By Season",
    desc: "Spring / Summer / Fall / Winter",
  },
  {
    value: "by_technique",
    label: "By Technique",
    desc: "Grilling / Baking / Slow Cooking",
  },
  {
    value: "by_occasion",
    label: "By Occasion",
    desc: "Weeknight / Brunch / Holiday",
  },
  { value: "custom", label: "Custom", desc: "Define your own chapters" },
];

const CHAPTER_SUGGESTIONS: Record<string, string[]> = {
  by_meal: ["Breakfast", "Lunch", "Dinner", "Snacks"],
  by_course: [
    "Appetizers",
    "Soups & Salads",
    "Main Courses",
    "Side Dishes",
    "Desserts",
    "Beverages",
  ],
  by_ingredient: [
    "Poultry",
    "Beef & Pork",
    "Seafood",
    "Vegetables",
    "Grains & Pasta",
    "Eggs & Dairy",
  ],
  by_cuisine: [
    "Italian",
    "Mexican",
    "Asian",
    "Mediterranean",
    "American",
    "French",
  ],
  by_season: ["Spring", "Summer", "Fall", "Winter"],
  by_technique: [
    "Grilling",
    "Baking",
    "Slow Cooking",
    "Stir-Fry",
    "Raw & No-Cook",
    "Pressure Cooking",
  ],
  by_occasion: [
    "Weeknight Dinners",
    "Weekend Brunch",
    "Holiday Feasts",
    "Party Appetizers",
    "Packed Lunches",
  ],
  custom: [],
};

const RECIPE_LAYOUTS = [
  { value: "classic", label: "Classic", desc: "Photo top, recipe below" },
  { value: "magazine", label: "Magazine", desc: "Side-by-side layout" },
  { value: "minimal", label: "Minimal", desc: "Text-focused, clean" },
  {
    value: "full_photo",
    label: "Full Photo",
    desc: "Full-page photo, recipe next page",
  },
  {
    value: "step_by_step",
    label: "Step-by-Step",
    desc: "Photo per step",
  },
  { value: "card", label: "Card", desc: "Recipe card format" },
  {
    value: "two_column",
    label: "Two Column",
    desc: "Two recipes per page",
  },
];

const ILLUSTRATION_METHODS = [
  { value: "ai_generated", label: "AI Generated" },
  { value: "stock_photos", label: "Stock Photos" },
  { value: "user_uploaded", label: "User Uploaded" },
  { value: "illustrated", label: "Illustrated" },
  { value: "no_illustrations", label: "No Illustrations" },
  { value: "mixed", label: "Mixed" },
];

const DIETARY_TAGS = [
  "Vegetarian",
  "Vegan",
  "Gluten-Free",
  "Dairy-Free",
  "Nut-Free",
  "Keto",
  "Paleo",
  "Low-Sodium",
  "Sugar-Free",
  "Halal",
  "Kosher",
];

// ---------------------------------------------------------------------------
// Step Props
// ---------------------------------------------------------------------------

interface StepProps {
  data: WizardData;
  onChange: (updates: Partial<WizardData>) => void;
}

// ---------------------------------------------------------------------------
// Step 1: Details
// ---------------------------------------------------------------------------

export function Step1Details({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Cookbook Details</h2>
        <p className="text-sm text-muted-foreground">
          Define the basics of your cookbook.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="space-y-2">
          <Label htmlFor="title">
            Title <span className="text-destructive">*</span>
          </Label>
          <Input
            id="title"
            placeholder="Enter cookbook title"
            value={data.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subtitle">Subtitle</Label>
          <Input
            id="subtitle"
            placeholder="Optional subtitle"
            value={data.subtitle}
            onChange={(e) => onChange({ subtitle: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="author">Author</Label>
          <Input
            id="author"
            placeholder="Author or pen name"
            value={data.author}
            onChange={(e) => onChange({ author: e.target.value })}
          />
        </div>
      </div>

      {/* Cookbook Type Card Selector */}
      <div className="space-y-3">
        <Label>
          Cookbook Type <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {COOKBOOK_TYPES.map((type) => {
            const Icon = type.icon;
            const isSelected = data.cookbook_type === type.value;
            return (
              <Card
                key={type.value}
                className={cn(
                  "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 text-center",
                  isSelected && "ring-2 ring-primary bg-primary/5",
                )}
                onClick={() =>
                  onChange({
                    cookbook_type: type.value,
                    // Reset cuisine_diet when switching away from diet_lifestyle
                    ...(type.value !== "diet_lifestyle"
                      ? { cuisine_diet: "" }
                      : {}),
                  })
                }
              >
                <Icon className="h-5 w-5 mx-auto mb-1 text-primary" />
                <p className="text-xs font-medium">{type.label}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {type.desc}
                </p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Secondary dropdown for Diet / Lifestyle */}
      {data.cookbook_type === "diet_lifestyle" && (
        <div className="space-y-2">
          <Label htmlFor="cuisine_diet">
            Cuisine / Diet <span className="text-destructive">*</span>
          </Label>
          <select
            id="cuisine_diet"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            value={data.cuisine_diet}
            onChange={(e) => onChange({ cuisine_diet: e.target.value })}
          >
            <option value="">Select a diet or cuisine...</option>
            {CUISINE_DIET_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="cuisine">Cuisine</Label>
          <Input
            id="cuisine"
            placeholder='e.g., "Italian", "Pan-Asian"'
            value={data.cuisine}
            onChange={(e) => onChange({ cuisine: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="target_audience">Target Audience</Label>
          <Input
            id="target_audience"
            placeholder='e.g., "Home cooks", "Beginners"'
            value={data.target_audience}
            onChange={(e) => onChange({ target_audience: e.target.value })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Brief description of your cookbook"
          value={data.description}
          onChange={(e) => onChange({ description: e.target.value })}
          rows={3}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2: Format
// ---------------------------------------------------------------------------

export function Step2Format({ data, onChange }: StepProps) {
  const [customChapter, setCustomChapter] = useState("");

  const suggestions = CHAPTER_SUGGESTIONS[data.chapter_organization] ?? [];

  const toggleChapter = (chapter: string) => {
    const current = data.initial_chapters;
    if (current.includes(chapter)) {
      onChange({ initial_chapters: current.filter((c) => c !== chapter) });
    } else {
      onChange({ initial_chapters: [...current, chapter] });
    }
  };

  const addCustomChapter = () => {
    const trimmed = customChapter.trim();
    if (trimmed && !data.initial_chapters.includes(trimmed)) {
      onChange({ initial_chapters: [...data.initial_chapters, trimmed] });
      setCustomChapter("");
    }
  };

  const removeChapter = (chapter: string) => {
    onChange({
      initial_chapters: data.initial_chapters.filter((c) => c !== chapter),
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Format & Organization</h2>
        <p className="text-sm text-muted-foreground">
          Choose the physical format and chapter structure.
        </p>
      </div>

      {/* Trim Size */}
      <div className="space-y-3">
        <Label>
          Trim Size <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {TRIM_SIZES.map((size) => (
            <Card
              key={size.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 text-center",
                data.trim_size === size.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ trim_size: size.value })}
            >
              <p className="text-sm font-medium">{size.label}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Interior Type */}
      <div className="space-y-3">
        <Label>Interior Type</Label>
        <div className="grid grid-cols-3 gap-3">
          {INTERIOR_TYPES.map((type) => (
            <Card
              key={type.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.interior_type === type.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ interior_type: type.value })}
            >
              <p className="text-sm font-medium">{type.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {type.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Chapter Organization */}
      <div className="space-y-3">
        <Label>
          Chapter Organization <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 gap-3">
          {CHAPTER_ORGANIZATIONS.map((org) => (
            <Card
              key={org.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.chapter_organization === org.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() =>
                onChange({
                  chapter_organization: org.value,
                  initial_chapters: [],
                })
              }
            >
              <p className="text-sm font-medium">{org.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {org.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Initial Chapters */}
      <div className="space-y-3">
        <Label>Initial Chapters</Label>
        <p className="text-xs text-muted-foreground">
          Toggle suggested chapters or add your own.
        </p>

        {suggestions.length > 0 && (
          <div className="space-y-2">
            {suggestions.map((chapter) => (
              <div
                key={chapter}
                className="flex items-center justify-between rounded-md border p-3"
              >
                <span className="text-sm">{chapter}</span>
                <Switch
                  checked={data.initial_chapters.includes(chapter)}
                  onCheckedChange={() => toggleChapter(chapter)}
                />
              </div>
            ))}
          </div>
        )}

        {/* Custom chapters already added (not in suggestions) */}
        {data.initial_chapters
          .filter((c) => !suggestions.includes(c))
          .map((chapter) => (
            <div
              key={chapter}
              className="flex items-center justify-between rounded-md border p-3"
            >
              <span className="text-sm">{chapter}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => removeChapter(chapter)}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}

        {/* Add custom chapter */}
        <div className="flex gap-2">
          <Input
            placeholder="Add custom chapter"
            value={customChapter}
            onChange={(e) => setCustomChapter(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCustomChapter();
              }
            }}
          />
          <Button
            variant="outline"
            size="icon"
            onClick={addCustomChapter}
            disabled={!customChapter.trim()}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Recipe Settings
// ---------------------------------------------------------------------------

export function Step3RecipeSettings({ data, onChange }: StepProps) {
  const toggleDietaryTag = (tag: string) => {
    const current = data.dietary_tags;
    if (current.includes(tag)) {
      onChange({ dietary_tags: current.filter((t) => t !== tag) });
    } else {
      onChange({ dietary_tags: [...current, tag] });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Recipe Settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure recipe layout, illustrations, and features.
        </p>
      </div>

      {/* Recipe Layout */}
      <div className="space-y-3">
        <Label>
          Recipe Layout <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {RECIPE_LAYOUTS.map((layout) => (
            <Card
              key={layout.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.recipe_layout === layout.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ recipe_layout: layout.value })}
            >
              <p className="text-sm font-medium">{layout.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {layout.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Illustration Method */}
      <div className="space-y-3">
        <Label>Illustration Method</Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {ILLUSTRATION_METHODS.map((method) => (
            <Card
              key={method.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 text-center",
                data.illustration_method === method.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ illustration_method: method.value })}
            >
              <p className="text-sm font-medium">{method.label}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Feature Toggles */}
      <div className="space-y-1">
        <Label className="text-sm font-medium">Features</Label>
        <p className="text-xs text-muted-foreground mb-3">
          Choose which sections to include in your cookbook.
        </p>
        <div className="space-y-3">
          {[
            {
              key: "include_nutrition" as const,
              label: "Include Nutrition Facts",
            },
            {
              key: "include_meal_plans" as const,
              label: "Include Meal Plans",
            },
            {
              key: "include_shopping_lists" as const,
              label: "Include Shopping Lists",
            },
            {
              key: "include_index" as const,
              label: "Include Recipe Index",
            },
            {
              key: "include_conversion_charts" as const,
              label: "Include Conversion Charts",
            },
          ].map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between rounded-md border p-3"
            >
              <span className="text-sm">{item.label}</span>
              <Switch
                checked={data[item.key]}
                onCheckedChange={(v) => onChange({ [item.key]: v })}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Dietary Tags */}
      <div className="space-y-3">
        <Label>Dietary Tags</Label>
        <p className="text-xs text-muted-foreground">
          Select tags to categorize recipes in your cookbook.
        </p>
        <div className="flex flex-wrap gap-2">
          {DIETARY_TAGS.map((tag) => {
            const isSelected = data.dietary_tags.includes(tag);
            return (
              <Badge
                key={tag}
                variant={isSelected ? "default" : "outline"}
                className={cn(
                  "cursor-pointer transition-colors",
                  isSelected
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "hover:bg-accent",
                )}
                onClick={() => toggleDietaryTag(tag)}
              >
                {tag}
              </Badge>
            );
          })}
        </div>
      </div>
    </div>
  );
}
