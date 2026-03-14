"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ---------------------------------------------------------------------------
// Types (self-contained for meal plan feature)
// ---------------------------------------------------------------------------

export interface CookbookBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  status: "draft" | "in-progress" | "published";
  created_at: string;
  updated_at: string;
}

export interface CookbookRecipeItem {
  id: string;
  title: string;
  calories?: number;
  servings?: number;
  prep_time?: number;
  cook_time?: number;
  nutrition?: { calories?: number };
}

export interface CookbookMealPlan {
  id: string;
  cookbook_id: string;
  title: string;
  plan_type: "weekly" | "biweekly" | "monthly";
  calorie_target: number;
  data: unknown;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/cookbook-books";

export const cookbookMealPlanKeys = {
  all: ["cookbooks"] as const,
  detail: (id: string) => [...cookbookMealPlanKeys.all, "detail", id] as const,
  recipes: (cookbookId: string) =>
    [...cookbookMealPlanKeys.all, "all-recipes", cookbookId] as const,
  mealPlans: (cookbookId: string) =>
    [...cookbookMealPlanKeys.all, "meal-plans", cookbookId] as const,
};

// ---------------------------------------------------------------------------
// Cookbook Detail
// ---------------------------------------------------------------------------

export function useCookbook(id: string) {
  return useQuery<CookbookBook>({
    queryKey: cookbookMealPlanKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// ---------------------------------------------------------------------------
// All Recipes for a Cookbook (flat list for MealPlanBuilder)
// ---------------------------------------------------------------------------

export function useChapterRecipes(cookbookId: string) {
  return useQuery<CookbookRecipeItem[]>({
    queryKey: cookbookMealPlanKeys.recipes(cookbookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${cookbookId}/recipes`);
      return data;
    },
    enabled: !!cookbookId,
  });
}

// ---------------------------------------------------------------------------
// Meal Plans
// ---------------------------------------------------------------------------

export function useMealPlans(cookbookId: string) {
  return useQuery<CookbookMealPlan[]>({
    queryKey: cookbookMealPlanKeys.mealPlans(cookbookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${cookbookId}/meal-plans`);
      return data;
    },
    enabled: !!cookbookId,
  });
}

export function useSaveMealPlan(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    CookbookMealPlan,
    Error,
    { title: string; type: string; calorieTarget: number; weeks: unknown }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/meal-plans`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookMealPlanKeys.mealPlans(cookbookId) });
      toast.success("Meal plan saved");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}
