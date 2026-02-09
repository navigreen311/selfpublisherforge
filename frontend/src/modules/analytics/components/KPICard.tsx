"use client";

import { type KPICard as KPICardType } from "../hooks";

interface KPICardProps {
  kpi: KPICardType;
}

export function KPICard({ kpi }: KPICardProps) {
  const changeColor =
    kpi.change_direction === "up"
      ? "text-green-600"
      : kpi.change_direction === "down"
        ? "text-red-600"
        : "text-gray-500";

  const changeIcon =
    kpi.change_direction === "up"
      ? "\u2191"
      : kpi.change_direction === "down"
        ? "\u2193"
        : "\u2192";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-600">{kpi.label}</p>
        {kpi.change_percent !== null && (
          <span className={`inline-flex items-center text-sm font-medium ${changeColor}`}>
            {changeIcon} {Math.abs(kpi.change_percent)}%
          </span>
        )}
      </div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{kpi.value}</p>
      <p className="mt-1 text-xs text-gray-500">{kpi.period}</p>
    </div>
  );
}
