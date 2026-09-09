"use client";

import { useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";

import { usePenNameAnalytics, usePenNames } from "../hooks";
import { PenNameSelect } from "./PenNameSelect";

/**
 * Stub analytics tab rendered per-pen-name. Real metrics wire in once the
 * analytics module exposes pen-name filters; this component owns the UI
 * contract and data-fetch wiring so those numbers can slot in later.
 */
export function PenNameAnalyticsTab() {
  const [penId, setPenId] = useState<string | null>(null);
  const [period] = useState<string>("30d");
  const { data: pens } = usePenNames();
  const { data, isLoading } = usePenNameAnalytics(penId, period);

  // Default to the default pen name when available.
  if (!penId && pens && pens.length > 0) {
    const def = pens.find((p) => p.is_default) ?? pens[0];
    if (def) setPenId(def.id);
  }

  return (
    <section className="space-y-4">
      <div className="flex items-end gap-3">
        <div className="max-w-sm flex-1 space-y-1">
          <label
            htmlFor="pen-analytics-select"
            className="text-sm font-medium"
          >
            Author
          </label>
          <PenNameSelect
            id="pen-analytics-select"
            value={penId}
            onChange={setPenId}
            placeholder="Filter by pen name"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      )}

      {!isLoading && data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Revenue" value={`$${data.revenue.toFixed(2)}`} />
          <StatCard label="Sales" value={String(data.sales)} />
          <StatCard label="Books" value={String(data.books_count)} />
          <StatCard
            label="Avg rating"
            value={data.avg_rating ? data.avg_rating.toFixed(1) : "--"}
          />
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Per-pen-name revenue, sales and BSR data roll up here once the
        analytics module lands pen filters. Book counts are already live.
      </p>
    </section>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
