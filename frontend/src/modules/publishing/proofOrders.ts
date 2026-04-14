"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

export type ProofOrderStatus =
  | "ordered"
  | "processing"
  | "printed"
  | "shipped"
  | "delivered"
  | "reviewed"
  | "approved"
  | "rejected"
  | "cancelled";

export type ProofPlatform = "kdp" | "ingramspark";

export interface ShippingAddress {
  name: string;
  address: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
}

export interface ProofBilling {
  method?: string;
  reference?: string;
  amount?: number | null;
}

export interface ProofOrderCreatePayload {
  publishing_id?: string | null;
  book_id?: string | null;
  quantity: number;
  platform: ProofPlatform;
  shipping_address: ShippingAddress;
  billing?: ProofBilling;
  shipping_method?: string;
  interior_file_url?: string;
  cover_file_url?: string;
  notes?: string;
}

export interface ProofOrder {
  id: string;
  org_id: string;
  publishing_id: string | null;
  book_id: string | null;
  quantity: number;
  platform: string | null;
  interior_file_url: string | null;
  cover_file_url: string | null;
  shipping_name: string | null;
  shipping_address: string | null;
  shipping_method: string | null;
  billing: Record<string, unknown> | null;
  cost: string | number | null;
  tracking_number: string | null;
  estimated_delivery: string | null;
  status: ProofOrderStatus;
  checklist: Record<string, unknown> | null;
  issues: string | null;
  notes: string | null;
  approved: boolean;
  approved_at: string | null;
  ordered_at: string;
  updated_at: string;
}

export interface ProofOrderListResponse {
  items: ProofOrder[];
  limit: number;
  offset: number;
  total: number;
}

export interface ProofOrderStatusUpdate {
  status: ProofOrderStatus;
  tracking_number?: string;
  estimated_delivery?: string;
  notes?: string;
}

export const proofOrderKeys = {
  all: ["proof-orders"] as const,
  list: (params?: Record<string, unknown>) =>
    [...proofOrderKeys.all, "list", params ?? {}] as const,
  detail: (id: string) => [...proofOrderKeys.all, "detail", id] as const,
};

export function useProofOrders(params?: {
  status?: ProofOrderStatus;
  publishing_id?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<ProofOrderListResponse>({
    queryKey: proofOrderKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/proof-orders", { params });
      return data;
    },
  });
}

export function useProofOrder(id: string | null | undefined) {
  return useQuery<ProofOrder>({
    queryKey: proofOrderKeys.detail(id ?? ""),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/proof-orders/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateProofOrder() {
  const qc = useQueryClient();
  return useMutation<ProofOrder, Error, ProofOrderCreatePayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/proof-orders", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: proofOrderKeys.all });
      toast.success("Proof order placed");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateProofOrderStatus(id: string) {
  const qc = useQueryClient();
  return useMutation<ProofOrder, Error, ProofOrderStatusUpdate>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(
        `/api/v1/proof-orders/${id}/status`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: proofOrderKeys.all });
      toast.success("Proof order updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
