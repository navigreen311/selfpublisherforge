"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MarketTrend } from "../hooks";

interface TrendChartProps {
  trend: MarketTrend | null | undefined;
  loading?: boolean;
}

export function TrendChart({ trend, loading = false }: TrendChartProps) {
  // Handle loading state
  if (loading) {
    return (
      <div className="border rounded-lg bg-card p-4">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-3" />
          <p className="text-sm text-muted-foreground">
            Loading trend data...
          </p>
        </div>
      </div>
    );
  }

  // Handle null/undefined trend prop
  if (!trend) {
    return (
      <div className="border rounded-lg bg-card p-4">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="rounded-full bg-muted p-3 mb-3">
            <TrendingUp className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">
            No trend data available yet. Check back after market snapshots are
            collected.
          </p>
        </div>
      </div>
    );
  }

  const dataPoints = trend.data_points ?? [];

  const chartData = dataPoints.map((p) => ({
    date: new Date(p.date).toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
    }),
    value: p.value ?? 0,
  }));

  const directionColor = {
    up: { stroke: "#22c55e", fill: "#22c55e" },
    down: { stroke: "#ef4444", fill: "#ef4444" },
    stable: { stroke: "#6366f1", fill: "#6366f1" },
  };

  const direction = trend.direction ?? "stable";
  const colors = directionColor[direction];
  const changePct = trend.change_pct ?? 0;

  return (
    <div
      className="border rounded-lg bg-card p-4"
      role="img"
      aria-label={`Market trend chart for ${trend.label ?? "unknown trend"}: ${changePct > 0 ? "+" : ""}${changePct.toFixed(1)}% ${direction}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-sm">{trend.label ?? "Trend"}</h4>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-xs font-medium px-2 py-0.5 rounded-full",
              direction === "up"
                ? "bg-green-100 text-green-700"
                : direction === "down"
                ? "bg-red-100 text-red-700"
                : "bg-gray-100 text-gray-700"
            )}
          >
            {changePct > 0 ? "+" : ""}
            {changePct.toFixed(1)}%
          </span>
        </div>
      </div>
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="value"
              stroke={colors.stroke}
              fill={colors.fill}
              fillOpacity={0.1}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="rounded-full bg-muted p-3 mb-3">
            <TrendingUp className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">
            No trend data available yet. Check back after market snapshots are
            collected.
          </p>
        </div>
      )}
    </div>
  );
}
