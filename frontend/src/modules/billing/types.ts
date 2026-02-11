/**
 * Type definitions for the Billing module.
 */

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
