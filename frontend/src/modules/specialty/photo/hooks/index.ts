"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type { PhotoReference, PhotoUsageType, PaginatedResponse } from "@/modules/specialty/types/photo";
export type { PhotoReference, PhotoUsageType };
const API_BASE = "/api/v1/specialty/photo-references";
export const photoKeys = { all: ["photos"] as const, list: (p?: Record<string, unknown>) => [...photoKeys.all, "list", p] as const };
export function usePhotoReferences(page = 1, pageSize = 20, filters?: { book_type?: string; book_id?: string; usage_type?: string; search?: string }) { return useQuery<PaginatedResponse<PhotoReference>>({ queryKey: photoKeys.list({ page, pageSize, ...filters }), queryFn: async () => { const { data } = await api.get(API_BASE, { params: { page, page_size: pageSize, ...filters } }); return data; } }); }
export function useDeletePhoto() { const qc = useQueryClient(); return useMutation<void, Error, string>({ mutationFn: async (id) => { await api.delete(API_BASE + "/" + id); }, onSuccess: () => { qc.invalidateQueries({ queryKey: photoKeys.all }); toast.success("Photo deleted"); }, onError: (e) => { toast.error(extractApiError(e)); } }); }
