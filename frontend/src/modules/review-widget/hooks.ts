import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface WidgetConfigRequest {
  book_id: string;
  style: "compact" | "full" | "badge";
  theme: "light" | "dark" | "auto";
  max_reviews: number;
  show_stars?: boolean;
  show_count?: boolean;
  show_reviews?: boolean;
}

export interface WidgetConfigResponse {
  embed_code: string;
  api_url: string;
}

export function useGenerateWidgetConfig() {
  return useMutation({
    mutationFn: async (payload: WidgetConfigRequest) => {
      const res = await api.post("/api/v1/reviews/widget-config", payload);
      return res.data as WidgetConfigResponse;
    },
  });
}
