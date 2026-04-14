"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  BookBreakdown,
  PlatformBreakdown,
  RoyaltyImportResult,
  RoyaltyRecordList,
  RoyaltySummary,
  TaxDocument,
  TaxDocumentList,
} from "./types";

const ROYALTIES = "/api/v1/royalties";
const TAX = "/api/v1/tax";

export const royaltyKeys = {
  all: ["royalties"] as const,
  summary: (year: number, period: string) =>
    [...royaltyKeys.all, "summary", year, period] as const,
  records: (params: Record<string, unknown>) =>
    [...royaltyKeys.all, "records", params] as const,
  platformBreakdown: (year: number) =>
    [...royaltyKeys.all, "platform-breakdown", year] as const,
  bookBreakdown: (year: number) =>
    [...royaltyKeys.all, "book-breakdown", year] as const,
};

export const taxKeys = {
  all: ["tax"] as const,
  documents: (year?: number) => [...taxKeys.all, "documents", year] as const,
};

export function useRoyaltySummary(year: number, period: string = "ytd") {
  return useQuery<RoyaltySummary>({
    queryKey: royaltyKeys.summary(year, period),
    queryFn: async () => {
      const { data } = await api.get(`${ROYALTIES}/summary`, {
        params: { year, period },
      });
      return data;
    },
  });
}

export function useRoyaltyRecords(params: {
  year?: number;
  platform?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<RoyaltyRecordList>({
    queryKey: royaltyKeys.records(params),
    queryFn: async () => {
      const { data } = await api.get(`${ROYALTIES}/records`, { params });
      return data;
    },
  });
}

export function usePlatformBreakdown(year: number) {
  return useQuery<PlatformBreakdown>({
    queryKey: royaltyKeys.platformBreakdown(year),
    queryFn: async () => {
      const { data } = await api.get(`${ROYALTIES}/platform-breakdown`, {
        params: { year },
      });
      return data;
    },
  });
}

export function useBookBreakdown(year: number) {
  return useQuery<BookBreakdown>({
    queryKey: royaltyKeys.bookBreakdown(year),
    queryFn: async () => {
      const { data } = await api.get(`${ROYALTIES}/book-breakdown`, {
        params: { year },
      });
      return data;
    },
  });
}

export function useImportRoyalty() {
  const qc = useQueryClient();
  return useMutation<RoyaltyImportResult, Error, { platform: string; file: File }>({
    mutationFn: async ({ platform, file }) => {
      const form = new FormData();
      form.append("platform", platform);
      form.append("file", file);
      const { data } = await api.post(`${ROYALTIES}/import`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: royaltyKeys.all });
    },
  });
}

export function useTaxDocuments(year?: number) {
  return useQuery<TaxDocumentList>({
    queryKey: taxKeys.documents(year),
    queryFn: async () => {
      const { data } = await api.get(`${TAX}/documents`, {
        params: year ? { year } : undefined,
      });
      return data;
    },
  });
}

export function useGenerateTaxDocument() {
  const qc = useQueryClient();
  return useMutation<
    TaxDocument,
    Error,
    { tax_year: number; document_type: string; platform?: string; format?: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${TAX}/documents/generate`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: taxKeys.all });
    },
  });
}

export async function downloadTaxDocument(id: string, filename: string) {
  const response = await api.get(`${TAX}/documents/${id}/download`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(response.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
