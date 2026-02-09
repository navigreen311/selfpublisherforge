"use client";

import { cn } from "@/lib/utils";
import type { BudgetStatus } from "../types";

interface BudgetMeterProps {
  budget: BudgetStatus;
  agentName?: string;
}

function ProgressBar({
  label,
  value,
  max,
  percentage,
  unit,
}: {
  label: string;
  value: number;
  max: number;
  percentage: number;
  unit: string;
}) {
  const getColor = (pct: number) => {
    if (pct >= 90) return "bg-red-500";
    if (pct >= 70) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="font-medium text-muted-foreground">{label}</span>
        <span className="text-muted-foreground">
          {unit === "$"
            ? `$${value.toFixed(2)} / $${max.toFixed(2)}`
            : `${value.toLocaleString()} / ${max.toLocaleString()}`}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={cn("h-2 rounded-full transition-all", getColor(percentage))}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="text-right text-xs text-muted-foreground mt-0.5">
        {percentage.toFixed(1)}%
      </div>
    </div>
  );
}

export function BudgetMeter({ budget, agentName }: BudgetMeterProps) {
  return (
    <div className="rounded-lg border p-4 space-y-4">
      {agentName && (
        <h4 className="text-sm font-semibold">{agentName}</h4>
      )}

      <ProgressBar
        label="Daily Tokens"
        value={budget.tokens_used_today}
        max={budget.daily_token_limit}
        percentage={budget.daily_token_pct}
        unit="tokens"
      />

      <ProgressBar
        label="Daily USD"
        value={budget.usd_used_today}
        max={budget.daily_usd_limit}
        percentage={budget.daily_usd_pct}
        unit="$"
      />

      <ProgressBar
        label="Monthly USD"
        value={budget.usd_used_this_month}
        max={budget.monthly_usd_limit}
        percentage={budget.monthly_usd_pct}
        unit="$"
      />

      <div className="grid grid-cols-2 gap-2 pt-2 border-t text-xs text-muted-foreground">
        <div>
          <span className="font-medium">Total tokens:</span>{" "}
          {budget.total_tokens_used.toLocaleString()}
        </div>
        <div>
          <span className="font-medium">Total spent:</span> $
          {budget.total_usd_used.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
