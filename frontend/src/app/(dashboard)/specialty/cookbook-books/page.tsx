"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  ChefHat,
  Clock,
  FileText,
  Globe,
  Plus,
  Search,
  UtensilsCrossed,
  Flame,
  Salad,
  Cake,
  Earth,
  PartyPopper,
  Timer,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCookbooks, useCookbookStats } from "@/modules/specialty/cookbook/hooks";
import { CookbookCard } from "@/modules/specialty/cookbook/components/CookbookCard";

// ---------------------------------------------------------------------------
// Quick-start templates
// ---------------------------------------------------------------------------

interface QuickTemplate {
  slug: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  cookbook_type: string;
  chapter_organization: string;
  recipe_layout: string;
}

const TEMPLATES: QuickTemplate[] = [
  {
    slug: "family-favorites",
    name: "Family Favorites",
    description: "A classic collection of beloved family recipes organized by meal",
    icon: <UtensilsCrossed className="h-6 w-6" />,
    cookbook_type: "recipe_collection",
    chapter_organization: "by_meal",
    recipe_layout: "classic",
  },
  {
    slug: "healthy-meal-prep",
    name: "Healthy Meal Prep",
    description: "Step-by-step meal prep guide with nutrition info",
    icon: <Timer className="h-6 w-6" />,
    cookbook_type: "fitness_meal_prep",
    chapter_organization: "by_course",
    recipe_layout: "step_by_step",
  },
  {
    slug: "baking-bible",
    name: "Baking Bible",
    description: "Comprehensive baking guide organized by technique",
    icon: <Cake className="h-6 w-6" />,
    cookbook_type: "baking_desserts",
    chapter_organization: "by_technique",
    recipe_layout: "full_photo",
  },
  {
    slug: "vegan-kitchen",
    name: "Vegan Kitchen",
    description: "Plant-based recipes organized by main ingredient",
    icon: <Salad className="h-6 w-6" />,
    cookbook_type: "diet_lifestyle",
    chapter_organization: "by_ingredient",
    recipe_layout: "magazine",
  },
  {
    slug: "world-cuisines",
    name: "World Cuisines",
    description: "A global culinary journey organized by cuisine",
    icon: <Earth className="h-6 w-6" />,
    cookbook_type: "cultural_cuisine",
    chapter_organization: "by_cuisine",
    recipe_layout: "full_photo",
  },
  {
    slug: "kids-family",
    name: "Kids & Family",
    description: "Family-friendly recipes for all ages",
    icon: <PartyPopper className="h-6 w-6" />,
    cookbook_type: "kids_family",
    chapter_organization: "by_occasion",
    recipe_layout: "classic",
  },
  {
    slug: "quick-easy-weeknight",
    name: "Quick & Easy Weeknight",
    description: "30-minute meals for busy weeknights",
    icon: <Flame className="h-6 w-6" />,
    cookbook_type: "quick_easy",
    chapter_organization: "by_meal",
    recipe_layout: "card",
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CookbookBooksPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const filters = {
    ...(search && { search }),
    ...(statusFilter !== "all" && { status: statusFilter }),
    ...(typeFilter !== "all" && { cookbook_type: typeFilter }),
  };

  const { data: stats } = useCookbookStats();
  const { data: cookbooksData, isLoading } = useCookbooks(1, 50, filters);

  const cookbooks = cookbooksData?.items ?? [];

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ChefHat className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Cookbooks</h1>
            <p className="text-muted-foreground">
              Create beautiful cookbooks with recipes, meal plans, and shopping lists
            </p>
          </div>
        </div>
        <Button asChild>
          <Link href="/specialty/cookbook-books/new">
            <Plus className="h-4 w-4 mr-2" /> Create New Cookbook
          </Link>
        </Button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.total_cookbooks ?? 0}</p>
              <p className="text-xs text-muted-foreground">Total Cookbooks</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.in_progress ?? 0}</p>
              <p className="text-xs text-muted-foreground">In Progress</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <Globe className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.published ?? 0}</p>
              <p className="text-xs text-muted-foreground">Published</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <UtensilsCrossed className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.total_recipes ?? 0}</p>
              <p className="text-xs text-muted-foreground">Total Recipes</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <FileText className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.total_chapters ?? 0}</p>
              <p className="text-xs text-muted-foreground">Total Chapters</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search cookbooks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Cookbook Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="diet_lifestyle">Diet / Lifestyle</SelectItem>
            <SelectItem value="recipe_collection">Recipe Collection</SelectItem>
            <SelectItem value="baking_desserts">Baking & Desserts</SelectItem>
            <SelectItem value="cultural_cuisine">Cultural Cuisine</SelectItem>
            <SelectItem value="kids_family">Kids & Family</SelectItem>
            <SelectItem value="fitness_meal_prep">Fitness / Meal Prep</SelectItem>
            <SelectItem value="quick_easy">Quick & Easy</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Cookbook Grid or Empty State */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="overflow-hidden animate-pulse">
              <div className="aspect-[3/4] bg-muted" />
              <div className="p-3 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : cookbooks.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {cookbooks.map((cookbook) => (
            <CookbookCard key={cookbook.id} cookbook={cookbook} />
          ))}
        </div>
      ) : (
        <div className="space-y-10">
          {/* Empty state */}
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
              <ChefHat className="h-12 w-12 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No cookbooks yet</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              Create your first cookbook with recipes, meal plans, and shopping
              lists. Start from scratch or pick a quick-start template below.
            </p>
            <Button asChild>
              <Link href="/specialty/cookbook-books/new">
                <Plus className="h-4 w-4 mr-2" /> Create Your First Cookbook
              </Link>
            </Button>
          </div>

          {/* Quick-start templates */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Start Templates</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {TEMPLATES.map((tpl) => (
                <Link
                  key={tpl.slug}
                  href={`/specialty/cookbook-books/new?template=${tpl.slug}`}
                >
                  <Card className="hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer h-full">
                    <CardContent className="p-5 flex flex-col gap-3">
                      <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        {tpl.icon}
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm">{tpl.name}</h4>
                        <p className="text-xs text-muted-foreground mt-1">
                          {tpl.description}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
