"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { projectKeys } from "./hooks";

// ---------------------------------------------------------------------------
// Bulk operations hooks (Feature 6B)
// Endpoint: POST /api/v1/books/bulk
// ---------------------------------------------------------------------------

export type BulkAction =
  | "archive"
  | "delete"
  | "change_price"
  | "add_tags"
  | "export_metadata_csv";

export interface BulkRequest {
  action: BulkAction;
  book_ids: string[];
  params?: Record<string, unknown>;
}

export interface BulkResponse {
  action: BulkAction;
  requested: number;
  affected: number;
  skipped_ids: string[];
  message?: string | null;
}

export function useBulkBooks() {
  const qc = useQueryClient();
  return useMutation<BulkResponse, Error, BulkRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post<BulkResponse>(
        "/api/v1/books/bulk",
        body,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

/** Request the metadata CSV export and trigger a browser download. */
export async function exportMetadataCsv(bookIds: string[]): Promise<void> {
  const response = await api.post(
    "/api/v1/books/bulk",
    { action: "export_metadata_csv", book_ids: bookIds },
    { responseType: "blob" },
  );
  const blob = new Blob([response.data as BlobPart], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "books_metadata.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
