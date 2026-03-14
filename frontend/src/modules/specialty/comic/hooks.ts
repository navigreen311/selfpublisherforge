"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type { Comic, ComicStats, CreateComicRequest } from "@/modules/specialty/types/comic";
export type { Comic, ComicStats };
export interface PaginatedResponse<T> { items: T[]; total: number; page: number; page_size: number; }
const API_BASE = "/api/v1/specialty/comic-books";
export const comicKeys = { all: ["comics"] as const, list: (p?: Record<string, unknown>) => [...comicKeys.all, "list", p] as const, detail: (id: string) => [...comicKeys.all, "detail", id] as const, pages: (id: string) => [...comicKeys.all, "pages", id] as const, characters: (id: string) => [...comicKeys.all, "characters", id] as const, stats: () => [...comicKeys.all, "stats"] as const };
export function useComics(page = 1, pageSize = 20, filters?: { status?: string; format?: string; search?: string }) { return useQuery<PaginatedResponse<Comic>>({ queryKey: comicKeys.list({ page, pageSize, ...filters }), queryFn: async () => { const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } }); return data; } }); }
export function useComicStats() { return useQuery<ComicStats>({ queryKey: comicKeys.stats(), queryFn: async () => { const { data } = await api.get(API_BASE + "/stats"); return data; } }); }
export function useComic(id: string) { return useQuery<Comic>({ queryKey: comicKeys.detail(id), queryFn: async () => { const { data } = await api.get(API_BASE + "/" + id); return data; }, enabled: !!id }); }
export function useCreateComic() { const qc = useQueryClient(); return useMutation<Comic, Error, CreateComicRequest>({ mutationFn: async (p) => { const { data } = await api.post(API_BASE, p); return data; }, onSuccess: () => { qc.invalidateQueries({ queryKey: comicKeys.all }); toast.success("Comic created"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useDeleteComic() { const qc = useQueryClient(); return useMutation<void, Error, string>({ mutationFn: async (id) => { await api.delete(API_BASE + "/" + id); }, onSuccess: () => { qc.invalidateQueries({ queryKey: comicKeys.all }); toast.success("Comic deleted"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
