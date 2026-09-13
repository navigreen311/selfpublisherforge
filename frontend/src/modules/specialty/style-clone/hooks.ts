"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type { StyleCloneProfile, PaginatedStyleCloneResponse } from "@/modules/specialty/types/style-clone";
export type { StyleCloneProfile };
const API_BASE = "/api/v1/specialty/style-clones";
export const styleCloneKeys = { all: ["style-clones"] as const, list: (p?: Record<string, unknown>) => [...styleCloneKeys.all, "list", p] as const, detail: (id: string) => [...styleCloneKeys.all, "detail", id] as const };
export function useStyleClones(page = 1, pageSize = 20, filters?: { search?: string; book_type?: string; active_only?: boolean }) { return useQuery<PaginatedStyleCloneResponse>({ queryKey: styleCloneKeys.list({ page, pageSize, ...filters }), queryFn: async () => { const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } }); return data; }, retry: false, placeholderData: { items: [], total: 0, page: 1, page_size: pageSize } }); }
export interface CreateStyleClonePayload { name: string; description?: string; reference_image_urls: string[]; book_type?: string }
export function useCreateStyleClone() { const qc = useQueryClient(); return useMutation<StyleCloneProfile, Error, CreateStyleClonePayload>({ mutationFn: async (payload) => { const { data } = await api.post(API_BASE, payload); return (data?.data ?? data) as StyleCloneProfile; }, onSuccess: () => { qc.invalidateQueries({ queryKey: styleCloneKeys.all }); toast.success("Style profile created"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useDeleteStyleClone() { const qc = useQueryClient(); return useMutation<void, Error, string>({ mutationFn: async (id) => { await api.delete(API_BASE + "/" + id); }, onSuccess: () => { qc.invalidateQueries({ queryKey: styleCloneKeys.all }); toast.success("Style profile deleted"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useAnalyzeStyle(id: string) { return useMutation<unknown, Error>({ mutationFn: async () => { const { data } = await api.post(API_BASE + "/" + id + "/analyze"); return data; }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useTestGenerate(id: string) { return useMutation<unknown, Error>({ mutationFn: async () => { const { data } = await api.post(API_BASE + "/" + id + "/test-generate"); return data; }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useCheckDrift(id: string) { return useMutation<unknown, Error>({ mutationFn: async () => { const { data } = await api.post(API_BASE + "/" + id + "/check-drift"); return data; }, onError: (e) => { toast.error(extractApiError(e)); } }); }
export function useSetDefault(id: string) { const qc = useQueryClient(); return useMutation<unknown, Error>({ mutationFn: async () => { const { data } = await api.post(API_BASE + "/" + id + "/set-default"); return data; }, onSuccess: () => { qc.invalidateQueries({ queryKey: styleCloneKeys.all }); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
