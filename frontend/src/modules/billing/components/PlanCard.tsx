"use client";

import { cn } from "@/lib/utils";
import type { PlanInfo, PlanTier } from "../hooks";

interface PlanCardProps {
  plan: PlanInfo;
  currentTier: PlanTier;
  onSelect: (tier: PlanTier) => void;
  isLoading?: boolean;
}

/**
 * A single pricing plan card displayed in the billing settings page.
 *
 * Highlights the recommended plan (plan.highlight === true) and shows
 * the current plan badge when applicable.
 */
export function PlanCard({
  plan,
  currentTier,
  onSelect,
  isLoading = false,
}: PlanCardProps) {
  const isCurrent = plan.tier === currentTier;
  const isHighlighted = plan.highlight;

  const priceDisplay =
    plan.price_monthly === 0
      ? "Free"
      : `$${(plan.price_monthly / 100).toFixed(0)}`;

  const projectsDisplay =
    plan.max_projects === null ? "Unlimited" : String(plan.max_projects);

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-2xl border p-6 shadow-sm transition-shadow hover:shadow-md",
        isHighlighted
          ? "border-blue-500 ring-2 ring-blue-500/20"
          : "border-gray-200",
        isCurrent && "bg-blue-50/50"
      )}
    >
      {/* Highlight badge */}
      {isHighlighted && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-semibold text-white">
          Most Popular
        </span>
      )}

      {/* Plan name & description */}
      <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
      <p className="mt-1 text-sm text-gray-500">{plan.description}</p>

      {/* Price */}
      <div className="mt-4 flex items-baseline gap-1">
        <span className="text-4xl font-bold text-gray-900">{priceDisplay}</span>
        {plan.price_monthly > 0 && (
          <span className="text-sm text-gray-500">/mo</span>
        )}
      </div>

      {/* Limits summary */}
      <div className="mt-4 space-y-1 text-sm text-gray-600">
        <p>
          <span className="font-medium">{projectsDisplay}</span> project
          {plan.max_projects !== 1 ? "s" : ""}
        </p>
        <p>
          <span className="font-medium">{plan.ai_generations_per_day}</span> AI
          generations/day
        </p>
      </div>

      {/* Feature list */}
      <ul className="mt-6 flex-1 space-y-2">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-2 text-sm">
            <svg
              className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span className="text-gray-700">{feature}</span>
          </li>
        ))}
      </ul>

      {/* Action button */}
      <button
        onClick={() => onSelect(plan.tier)}
        disabled={isCurrent || isLoading || plan.tier === "enterprise"}
        className={cn(
          "mt-6 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors",
          isCurrent
            ? "cursor-default bg-gray-100 text-gray-500"
            : isHighlighted
              ? "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              : "bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50"
        )}
      >
        {isCurrent
          ? "Current Plan"
          : plan.tier === "enterprise"
            ? "Contact Sales"
            : plan.price_monthly === 0
              ? "Downgrade to Free"
              : "Upgrade"}
      </button>
    </div>
  );
}
