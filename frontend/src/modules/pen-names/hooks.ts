"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PenName,
  PenNameAnalytics,
  PenNameBook,
  PenNameInput,
} from "./types";

export type * from "./types";

const API = "/api/v1/pen-names";

export const penNameKeys = {
  all: ["pen-names"] as const,
  list: () => [...penNameKeys.all, "list"] as const,
  detail: (id: string) => [...penNameKeys.all, "detail", id] as const,
  books: (id: string) => [...penNameKeys.all, "books", id] as const,
  analytics: (id: string, period: string) =>
    [...penNameKeys.all, "analytics", id, period] as const,
};

export function usePenNames() {
  return useQuery<PenName[]>({
    queryKey: penNameKeys.list(),
    queryFn: async () => (await api.get(API)).data,
  });
}

export function usePenName(id: string | null | undefined) {
  return useQuery<PenName>({
    queryKey: penNameKeys.detail(id ?? ""),
    enabled: !!id,
    queryFn: async () => (await api.get(`${API}/${id}`)).data,
  });
}

export function useCreatePenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: PenNameInput) => (await api.post(API, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.all }),
  });
}

export function useUpdatePenName(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<PenNameInput>) =>
      (await api.patch(`${API}/${id}`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.all }),
  });
}

export function useDeletePenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => (await api.delete(`${API}/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.all }),
  });
}

export function usePenNameBooks(id: string | null | undefined) {
  return useQuery<{ books: PenNameBook[] }>({
    queryKey: penNameKeys.books(id ?? ""),
    enabled: !!id,
    queryFn: async () => (await api.get(`${API}/${id}/books`)).data,
  });
}

export function usePenNameAnalytics(
  id: string | null | undefined,
  period: string = "30d"
) {
  return useQuery<PenNameAnalytics>({
    queryKey: penNameKeys.analytics(id ?? "", period),
    enabled: !!id,
    queryFn: async () =>
      (await api.get(`${API}/${id}/analytics?period=${period}`)).data,
  });
}
