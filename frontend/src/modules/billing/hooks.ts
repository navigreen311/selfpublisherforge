/**
 * React Query hooks for the Billing API.
 *
 * Provides data-fetching hooks for plans, subscriptions, usage stats,
 * invoices, and mutation hooks for checkout / portal session creation.
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PlanTier,
  PlanInfo,
  SubscriptionResponse,
  UsageStats,
  InvoiceItem,
  InvoiceListResponse,
  CheckoutRequest,
  CheckoutResponse,
  PortalRequest,
  PortalResponse,
} from "./types";

export type * from "./types";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const billingKeys = {
  all: ["billing"] as const,
  plans: () => [...billingKeys.all, "plans"] as const,
  subscription: () => [...billingKeys.all, "subscription"] as const,
  usage: () => [...billingKeys.all, "usage"] as const,
  invoices: () => [...billingKeys.all, "invoices"] as const,
};

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

/** Fetch all available billing plans. */
export function usePlans() {
  return useQuery({
    queryKey: billingKeys.plans(),
    queryFn: async (): Promise<PlanInfo[]> => {
      const { data } = await api.get<PlanInfo[]>("/api/v1/billing/plans");
      return data;
    },
  });
}

/** Fetch the current subscription for the authenticated org. */
export function useSubscription() {
  return useQuery({
    queryKey: billingKeys.subscription(),
    queryFn: async (): Promise<SubscriptionResponse> => {
      const { data } = await api.get<SubscriptionResponse>(
        "/api/v1/billing/subscription"
      );
      return data;
    },
  });
}

/** Fetch current usage stats for the authenticated org. */
export function useUsage() {
  return useQuery({
    queryKey: billingKeys.usage(),
    queryFn: async (): Promise<UsageStats> => {
      const { data } = await api.get<UsageStats>("/api/v1/billing/usage");
      return data;
    },
    refetchInterval: 60_000, // refresh usage every minute
  });
}

/** Fetch invoices for the authenticated org. */
export function useInvoices(limit = 10) {
  return useQuery({
    queryKey: [...billingKeys.invoices(), limit],
    queryFn: async (): Promise<InvoiceListResponse> => {
      const { data } = await api.get<InvoiceListResponse>(
        "/api/v1/billing/invoices",
        { params: { limit } }
      );
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

/** Create a Stripe Checkout session and redirect the user. */
export function useCreateCheckout() {
  return useMutation({
    mutationFn: async (body: CheckoutRequest): Promise<CheckoutResponse> => {
      const { data } = await api.post<CheckoutResponse>(
        "/api/v1/billing/subscribe",
        body
      );
      return data;
    },
    onSuccess: (data) => {
      // External redirect to Stripe - must use window.location
      window.location.href = data.checkout_url;
    },
  });
}

/** Create a Stripe billing portal session and redirect the user. */
export function useCreatePortal() {
  return useMutation({
    mutationFn: async (
      body?: PortalRequest
    ): Promise<PortalResponse> => {
      const { data } = await api.post<PortalResponse>(
        "/api/v1/billing/portal",
        body ?? {}
      );
      return data;
    },
    onSuccess: (data) => {
      // External redirect to Stripe - must use window.location
      window.location.href = data.portal_url;
    },
  });
}
