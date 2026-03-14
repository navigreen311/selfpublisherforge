/**
 * React Query mutation hook for the Review Feedback analysis endpoint.
 *
 * Posts reader complaints to the backend `analyze_feedback` pipeline and
 * returns categorised actions.
 */

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ─── Types ────────────────────────────────────────────────────────────────────

export type BookType = "childrens-books" | "coloring-books" | "puzzle-books";

export interface FeedbackAction {
  complaint: string;
  category: string;
  suggested_fix: string;
  action: string;
}

export interface AnalyzeFeedbackInput {
  complaints: string[];
  book_type: BookType;
  book_id: string;
}

export interface AnalyzeFeedbackResult {
  actions: FeedbackAction[];
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

const BASE = "/api/v1/specialty/shared";

export function useAnalyzeFeedback() {
  return useMutation({
    mutationFn: async (input: AnalyzeFeedbackInput) => {
      const { data } = await api.post<AnalyzeFeedbackResult>(
        `${BASE}/review-feedback/analyze`,
        {
          complaints: input.complaints,
          book_type: input.book_type,
          book_id: input.book_id,
        },
      );
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Analyzed ${data.actions.length} complaint(s)`);
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
