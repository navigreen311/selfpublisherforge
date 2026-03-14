"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  Cookbook,
  CookbookChapter,
  CookbookPaginatedResponse,
  CookbookStats,
  CreateCookbookRequest,
  UpdateCookbookRequest,
  CookbookMealPlan,
  CookbookRecipe,
} from "@/modules/specialty/types/cookbook";

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/cookbook-books";

export const cookbookKeys = {
  all: ["cookbooks"] as const,
  list: (params?: Record<string, unknown>) =>
    [...cookbookKeys.all, "list", params] as const,
  detail: (id: string) => [...cookbookKeys.all, "detail", id] as const,
  chapters: (cookbookId: string) =>
    [...cookbookKeys.all, "chapters", cookbookId] as const,
  recipes: (chapterId: string) =>
    [...cookbookKeys.all, "recipes", chapterId] as const,
  recipe: (recipeId: string) =>
    [...cookbookKeys.all, "recipe", recipeId] as const,
  mealPlans: (cookbookId: string) =>
    [...cookbookKeys.all, "mealPlans", cookbookId] as const,
  stats: () => [...cookbookKeys.all, "stats"] as const,
};

// ---------------------------------------------------------------------------
// List / Stats
// ---------------------------------------------------------------------------

export function useCookbooks(
  page = 1,
  pageSize = 20,
  filters?: { status?: string; cookbook_type?: string; search?: string },
) {
  return useQuery<CookbookPaginatedResponse<Cookbook>>({
    queryKey: cookbookKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, {
        params: { page, page_size: pageSize, ...filters },
      });
      return data;
    },
  });
}

export function useCookbookStats() {
  return useQuery<CookbookStats>({
    queryKey: cookbookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/stats`);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Single Cookbook CRUD
// ---------------------------------------------------------------------------

export function useCookbook(id: string) {
  return useQuery<Cookbook>({
    queryKey: cookbookKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateCookbook() {
  const queryClient = useQueryClient();
  return useMutation<Cookbook, Error, CreateCookbookRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post(API_BASE, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Cookbook created successfully");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useUpdateCookbook(id: string) {
  const queryClient = useQueryClient();
  return useMutation<Cookbook, Error, UpdateCookbookRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useDeleteCookbook() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (cookbookId) => { await api.delete(`${API_BASE}/${cookbookId}`); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Cookbook deleted");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Chapters
// ---------------------------------------------------------------------------

export function useCookbookChapters(cookbookId: string) {
  return useQuery<CookbookChapter[]>({
    queryKey: cookbookKeys.chapters(cookbookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${cookbookId}/chapters`);
      return data;
    },
    enabled: !!cookbookId,
  });
}

export function useCreateChapter(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookChapter, Error, { title: string; chapter_type: string; description?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/chapters`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Chapter created");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useUpdateChapter(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookChapter, Error, { chapterId: string; payload: Partial<CookbookChapter> }>({
    mutationFn: async ({ chapterId, payload }) => {
      const { data } = await api.patch(`${API_BASE}/${cookbookId}/chapters/${chapterId}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Chapter updated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useDeleteChapter(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (chapterId) => {
      await api.delete(`${API_BASE}/${cookbookId}/chapters/${chapterId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Chapter deleted");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Recipes
// ---------------------------------------------------------------------------

export function useChapterRecipes(chapterId: string) {
  return useQuery<CookbookRecipe[]>({
    queryKey: cookbookKeys.recipes(chapterId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/chapters/${chapterId}/recipes`);
      return data;
    },
    enabled: !!chapterId,
  });
}

export function useRecipe(recipeId: string) {
  return useQuery<CookbookRecipe>({
    queryKey: cookbookKeys.recipe(recipeId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/recipes/${recipeId}`);
      return data;
    },
    enabled: !!recipeId,
  });
}

export function useCreateRecipe(chapterId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, Partial<CookbookRecipe>>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/chapters/${chapterId}/recipes`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.recipes(chapterId) });
      toast.success("Recipe created");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useUpdateRecipe(recipeId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, Partial<CookbookRecipe>>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/recipes/${recipeId}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.recipe(recipeId) });
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Recipe updated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useDeleteRecipe(recipeId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: async () => { await api.delete(`${API_BASE}/recipes/${recipeId}`); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Recipe deleted");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// AI Generation
// ---------------------------------------------------------------------------

export function useGenerateRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { chapter_id: string; prompt?: string; cookbook_type?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/generate-recipe`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Recipe generated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useGenerateRecipeImage(recipeId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ image_url: string }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/recipes/${recipeId}/generate-image`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.recipe(recipeId) });
      toast.success("Recipe image generated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Nutrition & Scaling
// ---------------------------------------------------------------------------

export function useCalculateNutrition(recipeId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/recipes/${recipeId}/calculate-nutrition`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.recipe(recipeId) });
      toast.success("Nutrition calculated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useScaleRecipe(recipeId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { scaling_factor: number }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/recipes/${recipeId}/scale`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.recipe(recipeId) });
      toast.success("Recipe scaled");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Meal Plans
// ---------------------------------------------------------------------------

export function useMealPlans(cookbookId: string) {
  return useQuery<CookbookMealPlan[]>({
    queryKey: cookbookKeys.mealPlans(cookbookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${cookbookId}/meal-plans`);
      return data;
    },
    enabled: !!cookbookId,
  });
}

export function useCreateMealPlan(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookMealPlan, Error, { title: string; plan_type: string; description?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/meal-plans`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.mealPlans(cookbookId) });
      toast.success("Meal plan created");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useAutoFillMealPlan(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookMealPlan, Error, { planId: string }>({
    mutationFn: async ({ planId }) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/meal-plans/${planId}/auto-fill`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.mealPlans(cookbookId) });
      toast.success("Meal plan auto-filled");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function useGenerateShoppingList(planId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ shopping_list: unknown[] }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/meal-plans/${planId}/generate-shopping-list`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Shopping list generated");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Export & Preflight
// ---------------------------------------------------------------------------

export function useExportCookbook(cookbookId: string) {
  return useMutation<Blob, Error, { format?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/export`, payload, { responseType: "blob" });
      return data;
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cookbook-${cookbookId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Cookbook exported");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

export function usePreflight(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ passed: boolean; issues: { severity: string; message: string }[] }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/preflight`);
      return data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.detail(cookbookId) });
      if (result.passed) {
        toast.success("Preflight passed - ready to export");
      } else {
        toast.warning(`Preflight found ${result.issues.length} issue(s)`);
      }
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}
