/**
 * React Query hooks for the Billing API.
 *
 * Provides data-fetching hooks for plans, subscriptions, usage stats,
 * invoices, and mutation hooks for checkout / portal session creation.
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types (mirroring backend schemas)
// ---------------------------------------------------------------------------

export type PlanTier = "free" | "starter" | "pro" | "business" | "enterprise";

export interface PlanInfo {
  tier: PlanTier;
  name: string;
  price_monthly: number; // cents
  description: string;
  max_projects: number | null;
  ai_generations_per_day: number;
  features: string[];
  highlight: boolean;
}

export interface SubscriptionResponse {
  org_id: string;
  plan_tier: PlanTier;
  subscription_status: string;
  stripe_subscription_id: string | null;
  stripe_customer_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface UsageStats {
  org_id: string;
  plan_tier: PlanTier;
  projects_used: number;
  projects_limit: number | null;
  ai_generations_used_today: number;
  ai_generations_daily_limit: number;
  current_period_start: string | null;
  current_period_end: string | null;
}

export interface InvoiceItem {
  id: string;
  number: string | null;
  status: string;
  amount_due: number;
  amount_paid: number;
  currency: string;
  created: string;
  period_start: string;
  period_end: string;
  hosted_invoice_url: string | null;
  invoice_pdf: string | null;
}

export interface InvoiceListResponse {
  invoices: InvoiceItem[];
  has_more: boolean;
}

export interface CheckoutRequest {
  plan_tier: PlanTier;
  success_url?: string;
  cancel_url?: string;
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface PortalRequest {
  return_url?: string;
}

export interface PortalResponse {
  portal_url: string;
}

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
      // Redirect to Stripe Checkout
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
      window.location.href = data.portal_url;
    },
  });
}
