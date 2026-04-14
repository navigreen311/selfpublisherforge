"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  Checklist,
  IssuesLevel,
  ProofCostEstimate,
  ProofOrder,
  ProofOrderCreateInput,
  ShippingMethod,
} from "./types";

const API_PREFIX = "/api/v1/publishing";

export const proofKeys = {
  all: ["proof-orders"] as const,
  status: (publishingId: string) =>
    [...proofKeys.all, "status", publishingId] as const,
  estimate: (pageCount: number, interiorType: string, method: string) =>
    [...proofKeys.all, "estimate", pageCount, interiorType, method] as const,
};

export function useProofStatus(publishingId: string) {
  return useQuery<ProofOrder | null>({
    queryKey: proofKeys.status(publishingId),
    queryFn: async () => {
      try {
        const { data } = await api.get(
          `${API_PREFIX}/${publishingId}/proof-status`,
        );
        return data;
      } catch (err: any) {
        if (err?.response?.status === 404) return null;
        throw err;
      }
    },
  });
}

export function useProofCostEstimate(
  pageCount: number,
  interiorType: string,
  shippingMethod: ShippingMethod,
  enabled = true,
) {
  return useQuery<ProofCostEstimate>({
    queryKey: proofKeys.estimate(pageCount, interiorType, shippingMethod),
    enabled: enabled && pageCount > 0,
    queryFn: async () => {
      const sp = new URLSearchParams({
        page_count: String(pageCount),
        interior_type: interiorType,
        shipping_method: shippingMethod,
      });
      const { data } = await api.post(
        `${API_PREFIX}/estimate-proof-cost?${sp}`,
      );
      return data;
    },
  });
}

export function useOrderProof(publishingId: string) {
  const qc = useQueryClient();
  return useMutation<ProofOrder, Error, ProofOrderCreateInput>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_PREFIX}/${publishingId}/order-proof`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Proof copy ordered");
      qc.invalidateQueries({ queryKey: proofKeys.status(publishingId) });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useSkipProof(publishingId: string) {
  const qc = useQueryClient();
  return useMutation<ProofOrder, Error, { reason?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_PREFIX}/${publishingId}/skip-proof`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Proof skipped");
      qc.invalidateQueries({ queryKey: proofKeys.status(publishingId) });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

export function useProofReview(publishingId: string) {
  const qc = useQueryClient();
  return useMutation<
    ProofOrder,
    Error,
    { checklist: Checklist; issues: IssuesLevel; notes?: string; approved: boolean }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.patch(
        `${API_PREFIX}/${publishingId}/proof-review`,
        payload,
      );
      return data;
    },
    onSuccess: (data) => {
      toast.success(
        data.approved ? "Proof approved — ready to publish" : "Checklist saved",
      );
      qc.invalidateQueries({ queryKey: proofKeys.status(publishingId) });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}

// Convenience combined hook used by tests / page
export function useProofOrder(publishingId: string) {
  return {
    status: useProofStatus(publishingId),
    order: useOrderProof(publishingId),
    skip: useSkipProof(publishingId),
    review: useProofReview(publishingId),
  };
}
