"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { PlanCard } from "@/modules/billing/components/PlanCard";
import { UsageMeter } from "@/modules/billing/components/UsageMeter";
import { InvoiceList } from "@/modules/billing/components/InvoiceList";
import {
  usePlans,
  useSubscription,
  useUsage,
  useInvoices,
  useCreateCheckout,
  useCreatePortal,
  type PlanTier,
} from "@/modules/billing/hooks";

/**
 * Billing settings page.
 *
 * Displays:
 * - Current plan & subscription status
 * - Usage meters (projects, AI generations)
 * - Plan comparison cards with upgrade / downgrade actions
 * - Invoice history
 * - Billing portal link for managing payment methods
 */
export default function BillingSettingsPage() {
  const searchParams = useSearchParams();
  const [notified, setNotified] = useState(false);

  // Queries
  const { data: plans, isLoading: plansLoading } = usePlans();
  const { data: subscription, isLoading: subLoading } = useSubscription();
  const { data: usage, isLoading: usageLoading } = useUsage();
  const { data: invoiceData, isLoading: invoicesLoading } = useInvoices();

  // Mutations
  const checkout = useCreateCheckout();
  const portal = useCreatePortal();

  // Show success / cancel toasts from Stripe redirect
  useEffect(() => {
    if (notified) return;
    if (searchParams.get("success") === "true") {
      toast.success("Subscription updated successfully!");
      setNotified(true);
    } else if (searchParams.get("canceled") === "true") {
      toast.info("Checkout was canceled.");
      setNotified(true);
    }
  }, [searchParams, notified]);

  const currentTier: PlanTier = subscription?.plan_tier ?? "free";
  const isActive =
    subscription?.subscription_status === "active" ||
    subscription?.subscription_status === "trialing";

  const handleSelectPlan = (tier: PlanTier) => {
    if (tier === "enterprise") {
      window.open("mailto:sales@selfpublisherforge.com", "_blank");
      return;
    }
    if (tier === currentTier) return;

    checkout.mutate({
      plan_tier: tier,
      success_url: `${window.location.origin}/settings/billing?success=true`,
      cancel_url: `${window.location.origin}/settings/billing?canceled=true`,
    });
  };

  const handleManageBilling = () => {
    portal.mutate({
      return_url: `${window.location.origin}/settings/billing`,
    });
  };

  // Loading state
  if (plansLoading || subLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-gray-200" />
          <div className="h-4 w-96 rounded bg-gray-100" />
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-96 rounded-2xl bg-gray-100" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Billing & Subscription
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your plan, monitor usage, and view invoices.
        </p>
      </div>

      {/* Current plan summary */}
      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Current Plan:{" "}
              <span className="capitalize text-blue-600">{currentTier}</span>
            </h2>
            <p className="mt-0.5 text-sm text-gray-500">
              Status:{" "}
              <span className="font-medium capitalize">
                {subscription?.subscription_status ?? "none"}
              </span>
              {subscription?.cancel_at_period_end && (
                <span className="ml-2 text-amber-600">
                  (Cancels at period end)
                </span>
              )}
            </p>
            {subscription?.current_period_end && (
              <p className="mt-0.5 text-xs text-gray-400">
                Current period ends{" "}
                {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            )}
          </div>

          {isActive && (
            <button
              onClick={handleManageBilling}
              disabled={portal.isPending}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
            >
              {portal.isPending ? "Loading..." : "Manage Billing"}
            </button>
          )}
        </div>
      </section>

      {/* Usage meters */}
      {usage && (
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Current Usage
          </h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <UsageMeter
              label="Projects"
              used={usage.projects_used}
              limit={usage.projects_limit}
            />
            <UsageMeter
              label="AI Generations (today)"
              used={usage.ai_generations_used_today}
              limit={usage.ai_generations_daily_limit}
            />
          </div>
        </section>
      )}

      {/* Plan cards */}
      {plans && plans.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Available Plans
          </h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3 lg:grid-cols-5">
            {plans.map((plan) => (
              <PlanCard
                key={plan.tier}
                plan={plan}
                currentTier={currentTier}
                onSelect={handleSelectPlan}
                isLoading={checkout.isPending}
              />
            ))}
          </div>
        </section>
      )}

      {/* Invoice history */}
      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Invoice History
        </h2>
        <InvoiceList
          invoices={invoiceData?.invoices ?? []}
          isLoading={invoicesLoading}
        />
      </section>
    </div>
  );
}
