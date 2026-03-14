"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

export interface Cookbook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  cookbook_type: string;
  cuisine?: string;
  target_audience?: string;
  description?: string;
  trim_size: string;
  interior_type: string;
  chapter_organization: string;
  page_count: number;
  recipe_layout: string;
  illustration_method: string;
  include_nutrition: boolean;
  include_meal_plans: boolean;
  include_shopping_lists: boolean;
  include_index: boolean;
  include_conversion_charts: boolean;
  dietary_tags: string[];
  status: "draft" | "in-progress" | "published";
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CookbookIngredient {
  amount: string;
  unit: string;
  name: string;
  notes?: string;
}

export interface CookbookInstruction {
  step_number: number;
  text: string;
  image_url?: string;
  tip?: string;
}

export interface CookbookNutrition {
  calories?: number;
  fat?: number;
  protein?: number;
  carbs?: number;
  fiber?: number;
  sodium?: number;
}

export interface CookbookRecipe {
  id: string;
  chapter_id: string;
  title: string;
  description?: string;
  image_url?: string;
  servings?: number;
  prep_time?: number;
  cook_time?: number;
  difficulty?: "beginner" | "easy" | "intermediate" | "advanced" | "expert";
  ingredients: CookbookIngredient[];
  instructions: CookbookInstruction[];
  nutrition?: CookbookNutrition;
  notes?: string;
  tips?: string;
  variations?: string[];
  source?: string;
  tags?: string[];
  dietary_flags?: string[];
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CookbookChapter {
  id: string;
  cookbook_id: string;
  title: string;
  chapter_type?: string;
  order: number;
  recipe_count: number;
  recipes: CookbookRecipe[];
  created_at: string;
  updated_at: string;
}

export interface CookbookStats {
  total_cookbooks: number;
  in_progress: number;
  published: number;
  total_recipes: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

const API_BASE = "/api/v1/specialty/cookbook-books";

export const cookbookKeys = {
  all: ["cookbooks"] as const,
  list: (params?: Record<string, unknown>) => [...cookbookKeys.all, "list", params] as const,
  detail: (id: string) => [...cookbookKeys.all, "detail", id] as const,
  chapters: (cookbookId: string) => [...cookbookKeys.all, "chapters", cookbookId] as const,
  stats: () => [...cookbookKeys.all, "stats"] as const,
};

export function useCookbooks(page = 1, pageSize = 20, filters?: { status?: string; cookbook_type?: string; search?: string }) {
  return useQuery<PaginatedResponse<Cookbook>>({
    queryKey: cookbookKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } });
      return data;
    },
  });
}

export function useCookbookStats() {
  return useQuery<CookbookStats>({
    queryKey: cookbookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(API_BASE + "/stats");
      return data;
    },
  });
}

export function useCookbook(id: string) {
  return useQuery<Cookbook>({
    queryKey: cookbookKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(API_BASE + "/" + id);
      return data;
    },
    enabled: !!id,
  });
}

export function useCookbookChapters(cookbookId: string) {
  return useQuery<CookbookChapter[]>({
    queryKey: cookbookKeys.chapters(cookbookId),
    queryFn: async () => {
      const { data } = await api.get(API_BASE + "/" + cookbookId + "/chapters");
      return data;
    },
    enabled: !!cookbookId,
  });
}

export function useCreateCookbook() {
  const queryClient = useQueryClient();
  return useMutation<Cookbook, Error, Partial<Cookbook>>({
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

export function useDeleteCookbook() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (cookbookId) => { await api.delete(API_BASE + "/" + cookbookId); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.all });
      toast.success("Cookbook deleted");
    },
    onError: (error) => { toast.error(extractApiError(error)); },
  });
}

// ---------------------------------------------------------------------------
// Chapter Mutations
// ---------------------------------------------------------------------------

export function useCreateChapter(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookChapter, Error, { title: string; chapter_type?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/chapters`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Chapter created");
    },
    onError: (error) => toast.error(extractApiError(error)),
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
    onError: (error) => toast.error(extractApiError(error)),
  });
}

// ---------------------------------------------------------------------------
// Recipe Mutations
// ---------------------------------------------------------------------------

export function useCreateRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { chapter_id: string; title: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/recipes`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Recipe created");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useUpdateRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { recipeId: string; payload: Partial<CookbookRecipe> }>({
    mutationFn: async ({ recipeId, payload }) => {
      const { data } = await api.patch(`${API_BASE}/${cookbookId}/recipes/${recipeId}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useDeleteRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (recipeId) => {
      await api.delete(`${API_BASE}/${cookbookId}/recipes/${recipeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Recipe deleted");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

// ---------------------------------------------------------------------------
// AI Actions
// ---------------------------------------------------------------------------

export function useGenerateRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { chapter_id: string; prompt?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/generate-recipe`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Recipe generated");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useGenerateRecipeImage(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ image_url: string }, Error, { recipeId: string }>({
    mutationFn: async ({ recipeId }) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/recipes/${recipeId}/generate-image`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Image generated");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useImproveInstructions(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { recipeId: string }>({
    mutationFn: async ({ recipeId }) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/recipes/${recipeId}/improve-instructions`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Instructions improved");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useCalculateNutrition(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookNutrition, Error, { recipeId: string }>({
    mutationFn: async ({ recipeId }) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/recipes/${recipeId}/calculate-nutrition`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Nutrition calculated");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useScaleRecipe(cookbookId: string) {
  const queryClient = useQueryClient();
  return useMutation<CookbookRecipe, Error, { recipeId: string; factor: number }>({
    mutationFn: async ({ recipeId, factor }) => {
      const { data } = await api.post(`${API_BASE}/${cookbookId}/recipes/${recipeId}/scale`, { factor });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookbookKeys.chapters(cookbookId) });
      toast.success("Recipe scaled");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}
