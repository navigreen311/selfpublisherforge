import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PenName,
  PenNameAnalytics,
  PenNameBook,
  PenNameCreatePayload,
  PenNameUpdatePayload,
} from "./types";

const penNameKeys = {
  all: ["pen-names"] as const,
  list: () => [...penNameKeys.all, "list"] as const,
  detail: (id: string) => [...penNameKeys.all, "detail", id] as const,
  books: (id: string) => [...penNameKeys.all, "books", id] as const,
  analytics: (id: string, period: string) =>
    [...penNameKeys.all, "analytics", id, period] as const,
};

export function usePenNames() {
  return useQuery({
    queryKey: penNameKeys.list(),
    queryFn: async () => {
      const res = await api.get("/api/v1/pen-names");
      return res.data as PenName[];
    },
  });
}

export function useCreatePenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: PenNameCreatePayload) => {
      const res = await api.post("/api/v1/pen-names", data);
      return res.data as PenName;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.list() }),
  });
}

export function useUpdatePenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PenNameUpdatePayload }) => {
      const res = await api.patch(`/api/v1/pen-names/${id}`, data);
      return res.data as PenName;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.list() }),
  });
}

export function useDeletePenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/pen-names/${id}`);
      return id;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.list() }),
  });
}

export function useSetDefaultPenName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/api/v1/pen-names/${id}/set-default`);
      return res.data as PenName;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: penNameKeys.list() }),
  });
}

export function usePenNameBooks(id: string | null) {
  return useQuery({
    queryKey: penNameKeys.books(id ?? ""),
    enabled: Boolean(id),
    queryFn: async () => {
      const res = await api.get(`/api/v1/pen-names/${id}/books`);
      return (res.data?.books ?? []) as PenNameBook[];
    },
  });
}

export function usePenNameAnalytics(id: string | null, period: string = "30d") {
  return useQuery({
    queryKey: penNameKeys.analytics(id ?? "", period),
    enabled: Boolean(id),
    queryFn: async () => {
      const res = await api.get(`/api/v1/pen-names/${id}/analytics`, {
        params: { period },
      });
      return res.data as PenNameAnalytics;
    },
  });
}
