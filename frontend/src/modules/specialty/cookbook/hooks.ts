"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
export interface Cookbook { id: string; org_id: string; title: string; subtitle?: string; author: string; cookbook_type: string; cuisine?: string; target_audience?: string; description?: string; trim_size: string; interior_type: string; chapter_organization: string; page_count: number; recipe_layout: string; illustration_method: string; include_nutrition: boolean; include_meal_plans: boolean; include_shopping_lists: boolean; include_index: boolean; include_conversion_charts: boolean; dietary_tags: string[]; status: "draft" | "in-progress" | "published"; qa_score?: number; cover_image_url?: string; created_at: string; updated_at: string; }
export interface CookbookChapter { id: string; cookbook_id: string; title: string; order: number; recipe_count: number; created_at: string; updated_at: string; }
export interface CookbookStats { total_cookbooks: number; in_progress: number; published: number; total_recipes: number; }
export interface PaginatedResponse<T> { items: T[]; total: number; page: number; page_size: number; }
const API_BASE = "/api/v1/specialty/cookbook-books";
export const cookbookKeys = { all: ["cookbooks"] as const, list: (p?: Record<string, unknown>) => [...cookbookKeys.all, "list", p] as const, detail: (id: string) => [...cookbookKeys.all, "detail", id] as const, chapters: (id: string) => [...cookbookKeys.all, "chapters", id] as const, stats: () => [...cookbookKeys.all, "stats"] as const };
export function useCookbooks(page = 1, pageSize = 20, filters?: { status?: string; cookbook_type?: string; search?: string }) { return useQuery<PaginatedResponse<Cookbook>>({ queryKey: cookbookKeys.list({ page, pageSize, ...filters }), queryFn: async () => { const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } }); return data; } }); }
export function useCookbookStats() { return useQuery<CookbookStats>({ queryKey: cookbookKeys.stats(), queryFn: async () => { const { data } = await api.get(API_BASE + "/stats"); return data; } }); }
export function useCookbook(id: string) { return useQuery<Cookbook>({ queryKey: cookbookKeys.detail(id), queryFn: async () => { const { data } = await api.get(API_BASE + "/" + id); return data; }, enabled: !!id }); }
export function useCookbookChapters(id: string) { return useQuery<CookbookChapter[]>({ queryKey: cookbookKeys.chapters(id), queryFn: async () => { const { data } = await api.get(API_BASE + "/" + id + "/chapters"); return data; }, enabled: !!id }); }
export function useDeleteCookbook() { const qc = useQueryClient(); return useMutation<void, Error, string>({ mutationFn: async (id) => { await api.delete(API_BASE + "/" + id); }, onSuccess: () => { qc.invalidateQueries({ queryKey: cookbookKeys.all }); toast.success("Cookbook deleted"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
