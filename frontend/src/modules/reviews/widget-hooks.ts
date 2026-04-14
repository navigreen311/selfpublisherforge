"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

const WIDGET_PREFIX = "/api/v1/review-widgets";

export type WidgetStyle = "card_grid" | "carousel" | "compact_list";
export type WidgetTheme = "light" | "dark" | "auto";

export interface ReviewWidget {
  id: string;
  book_id: string;
  style: WidgetStyle;
  theme: WidgetTheme;
  max_reviews: number;
  min_rating: number;
  show_options?: Record<string, unknown> | null;
  embed_code: string;
}

export interface WidgetCreateInput {
  book_id: string;
  style: WidgetStyle;
  theme: WidgetTheme;
  max_reviews: number;
  min_rating: number;
  show_options?: Record<string, unknown>;
}

export const widgetKeys = {
  all: ["review-widgets"] as const,
  list: () => [...widgetKeys.all, "list"] as const,
  detail: (id: string) => [...widgetKeys.all, "detail", id] as const,
};

export function useReviewWidgets() {
  return useQuery<ReviewWidget[]>({
    queryKey: widgetKeys.list(),
    queryFn: async () => {
      const { data } = await api.get(WIDGET_PREFIX);
      return data;
    },
  });
}

export function useCreateReviewWidget() {
  const qc = useQueryClient();
  return useMutation<ReviewWidget, Error, WidgetCreateInput>({
    mutationFn: async (body) => {
      const { data } = await api.post(WIDGET_PREFIX, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: widgetKeys.list() });
    },
  });
}

export function useDeleteReviewWidget() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${WIDGET_PREFIX}/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: widgetKeys.list() });
    },
  });
}
