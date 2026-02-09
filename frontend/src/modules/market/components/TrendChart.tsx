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
import { cn } from "@/lib/utils";
import type { MarketTrend } from "../hooks";

interface TrendChartProps {
  trend: MarketTrend;
}

export function TrendChart({ trend }: TrendChartProps) {
  const chartData = trend.data_points.map((p) => ({
    date: new Date(p.date).toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
    }),
    value: p.value,
  }));

  const directionColor = {
    up: { stroke: "#22c55e", fill: "#22c55e" },
    down: { stroke: "#ef4444", fill: "#ef4444" },
    stable: { stroke: "#6366f1", fill: "#6366f1" },
  };

  const colors = directionColor[trend.direction];

  return (
    <div className="border rounded-lg bg-card p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-sm">{trend.label}</h4>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-xs font-medium px-2 py-0.5 rounded-full",
              trend.direction === "up"
                ? "bg-green-100 text-green-700"
                : trend.direction === "down"
                ? "bg-red-100 text-red-700"
                : "bg-gray-100 text-gray-700"
            )}
          >
            {trend.change_pct > 0 ? "+" : ""}
            {trend.change_pct.toFixed(1)}%
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
        <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
          No trend data available
        </div>
      )}
    </div>
  );
}
