"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  FilingStatus,
  TaxDashboard,
  TaxExpense,
  TaxExpenseInput,
} from "./types";

const API_PREFIX = "/api/v1/tax";

export const taxKeys = {
  all: ["tax"] as const,
  dashboard: (year: number, rate?: string, status?: string) =>
    [...taxKeys.all, "dashboard", year, rate, status] as const,
  expenses: (year: number) => [...taxKeys.all, "expenses", year] as const,
};

export function useTaxDashboard(
  year: number,
  taxRate?: string,
  filingStatus?: FilingStatus,
) {
  return useQuery<TaxDashboard>({
    queryKey: taxKeys.dashboard(year, taxRate, filingStatus),
    queryFn: async () => {
      const sp = new URLSearchParams({ year: String(year) });
      if (taxRate) sp.set("tax_rate", taxRate);
      if (filingStatus) sp.set("filing_status", filingStatus);
      const { data } = await api.get(`${API_PREFIX}?${sp}`);
      return data;
    },
  });
}

export function useTaxExpenses(year: number) {
  return useQuery<TaxExpense[]>({
    queryKey: taxKeys.expenses(year),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/expenses?year=${year}`);
      return data;
    },
  });
}

export function useCreateExpense() {
  const qc = useQueryClient();
  return useMutation<TaxExpense, Error, TaxExpenseInput>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`${API_PREFIX}/expenses`, payload);
      return data;
    },
    onSuccess: () => {
      toast.success("Expense added");
      qc.invalidateQueries({ queryKey: taxKeys.all });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useUpdateExpense() {
  const qc = useQueryClient();
  return useMutation<TaxExpense, Error, { id: string; patch: Partial<TaxExpenseInput> }>({
    mutationFn: async ({ id, patch }) => {
      const { data } = await api.patch(`${API_PREFIX}/expenses/${id}`, patch);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: taxKeys.all }),
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useDeleteExpense() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/expenses/${id}`);
    },
    onSuccess: () => {
      toast.success("Expense deleted");
      qc.invalidateQueries({ queryKey: taxKeys.all });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useMarkQuarterlyPaid() {
  const qc = useQueryClient();
  return useMutation<
    unknown,
    Error,
    { year: number; quarter: number; paid: boolean; paid_date?: string; actual_amount?: string }
  >({
    mutationFn: async ({ year, quarter, paid, paid_date, actual_amount }) => {
      const { data } = await api.patch(
        `${API_PREFIX}/quarterly-payment/${quarter}?year=${year}`,
        { paid, paid_date, actual_amount },
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: taxKeys.all }),
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function downloadTaxExport(
  format: "csv" | "pdf",
  year: number,
  taxRate?: string,
  filingStatus?: FilingStatus,
) {
  const sp = new URLSearchParams({ format, year: String(year) });
  if (taxRate) sp.set("tax_rate", taxRate);
  if (filingStatus) sp.set("filing_status", filingStatus);
  return api
    .get(`${API_PREFIX}/export?${sp}`, { responseType: "blob" })
    .then((res) => {
      const blob = new Blob([res.data], {
        type: format === "csv" ? "text/csv" : "application/pdf",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tax_${year}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
}
