"use client";

import { cn } from "@/lib/utils";

interface UsageMeterProps {
  label: string;
  used: number;
  limit: number | null; // null = unlimited
  unit?: string;
}

/**
 * A visual usage meter that shows current consumption vs. the plan limit.
 *
 * When the limit is null (unlimited), it displays "Unlimited" with a full bar.
 */
export function UsageMeter({
  label,
  used,
  limit,
  unit = "",
}: UsageMeterProps) {
  const isUnlimited = limit === null;
  const percentage = isUnlimited
    ? 100
    : limit > 0
      ? Math.min((used / limit) * 100, 100)
      : 0;

  const isWarning = !isUnlimited && percentage >= 80;
  const isDanger = !isUnlimited && percentage >= 95;

  const barColor = isDanger
    ? "bg-red-500"
    : isWarning
      ? "bg-amber-500"
      : "bg-blue-500";

  const usedDisplay = `${used.toLocaleString()}${unit ? ` ${unit}` : ""}`;
  const limitDisplay = isUnlimited
    ? "Unlimited"
    : `${limit.toLocaleString()}${unit ? ` ${unit}` : ""}`;

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">{label}</span>
        <span
          className={cn(
            "tabular-nums",
            isDanger
              ? "font-semibold text-red-600"
              : isWarning
                ? "font-semibold text-amber-600"
                : "text-gray-500"
          )}
        >
          {usedDisplay} / {limitDisplay}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className={cn("h-full rounded-full transition-all duration-300", barColor)}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Warning text */}
      {isDanger && (
        <p className="text-xs text-red-600">
          You are at or near your limit. Consider upgrading your plan.
        </p>
      )}
      {isWarning && !isDanger && (
        <p className="text-xs text-amber-600">
          You are approaching your limit.
        </p>
      )}
    </div>
  );
}
