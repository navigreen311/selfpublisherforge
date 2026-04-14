"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  ManualEntryInput,
  MonthlyStatement,
  RoyaltyDashboard,
  RoyaltyEntry,
  RoyaltyImportResult,
} from "./types";

const API_PREFIX = "/api/v1/royalties";

export const royaltyKeys = {
  all: ["royalties"] as const,
  list: (params?: Record<string, unknown>) =>
    [...royaltyKeys.all, "list", params] as const,
  dashboard: (year?: number, penNameId?: string) =>
    [...royaltyKeys.all, "dashboard", year, penNameId] as const,
  monthly: (year: number, penNameId?: string) =>
    [...royaltyKeys.all, "monthly", year, penNameId] as const,
};

export function useRoyalties(params?: {
  period?: string;
  year?: number;
  distributor?: string;
  pen_name_id?: string;
}) {
  return useQuery<RoyaltyEntry[]>({
    queryKey: royaltyKeys.list(params),
    queryFn: async () => {
      const sp = new URLSearchParams();
      if (params?.period) sp.set("period", params.period);
      if (params?.year) sp.set("year", String(params.year));
      if (params?.distributor) sp.set("distributor", params.distributor);
      if (params?.pen_name_id) sp.set("pen_name_id", params.pen_name_id);
      const { data } = await api.get(`${API_PREFIX}?${sp}`);
      return data;
    },
  });
}

export function useRoyaltyDashboard(year?: number, penNameId?: string) {
  return useQuery<RoyaltyDashboard>({
    queryKey: royaltyKeys.dashboard(year, penNameId),
    queryFn: async () => {
      const sp = new URLSearchParams();
      if (year) sp.set("year", String(year));
      if (penNameId) sp.set("pen_name_id", penNameId);
      const { data } = await api.get(`${API_PREFIX}/by-distributor?${sp}`);
      return data;
    },
  });
}

export function useMonthlyStatement(year: number, penNameId?: string) {
  return useQuery<MonthlyStatement>({
    queryKey: royaltyKeys.monthly(year, penNameId),
    queryFn: async () => {
      const sp = new URLSearchParams({ year: String(year) });
      if (penNameId) sp.set("pen_name_id", penNameId);
      const { data } = await api.get(`${API_PREFIX}/monthly-statement?${sp}`);
      return data;
    },
  });
}

export function useImportRoyalties() {
  const qc = useQueryClient();
  return useMutation<RoyaltyImportResult, Error, { file: File; distributor: string }>({
    mutationFn: async ({ file, distributor }) => {
      const form = new FormData();
      form.append("file", file);
      form.append("distributor", distributor);
      const { data } = await api.post(`${API_PREFIX}/import`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: (data) => {
      toast.success(
        `Imported ${data.imported} ${data.distributor.toUpperCase()} entries ($${data.total_amount})`,
      );
      qc.invalidateQueries({ queryKey: royaltyKeys.all });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useManualRoyaltyEntry() {
  const qc = useQueryClient();
  return useMutation<RoyaltyEntry, Error, ManualEntryInput>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_PREFIX}/manual-entry`, payload);
      return data;
    },
    onSuccess: () => {
      toast.success("Royalty entry added");
      qc.invalidateQueries({ queryKey: royaltyKeys.all });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function downloadRoyaltyExport(format: "csv" | "pdf", year: number) {
  const sp = new URLSearchParams({ format, year: String(year) });
  return api
    .get(`${API_PREFIX}/export?${sp}`, { responseType: "blob" })
    .then((res) => {
      const blob = new Blob([res.data], {
        type: format === "csv" ? "text/csv" : "application/pdf",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `royalties_${year}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
}
