"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import type { AdPerformance } from "../hooks";

interface PerformanceChartProps {
  data: AdPerformance[];
  metrics?: ("spend" | "sales" | "acos" | "impressions" | "clicks" | "roas")[];
}

const METRIC_CONFIG: Record<
  string,
  { color: string; label: string; format: (v: number) => string }
> = {
  spend: { color: "#ef4444", label: "Spend ($)", format: (v) => `$${v.toFixed(2)}` },
  sales: { color: "#22c55e", label: "Sales ($)", format: (v) => `$${v.toFixed(2)}` },
  acos: { color: "#f97316", label: "ACOS (%)", format: (v) => `${v.toFixed(1)}%` },
  impressions: { color: "#3b82f6", label: "Impressions", format: (v) => v.toLocaleString() },
  clicks: { color: "#8b5cf6", label: "Clicks", format: (v) => v.toLocaleString() },
  roas: { color: "#06b6d4", label: "ROAS", format: (v) => `${v.toFixed(2)}x` },
};

export function PerformanceChart({
  data,
  metrics = ["spend", "sales", "acos"],
}: PerformanceChartProps) {
  const chartData = data
    .slice()
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((record) => ({
      ...record,
      date: format(new Date(record.date), "MMM dd"),
    }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-lg bg-muted/10">
        <p className="text-muted-foreground">No performance data available</p>
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey="date" fontSize={12} />
          <YAxis fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
          />
          <Legend />
          {metrics.map((metric) => {
            const config = METRIC_CONFIG[metric];
            return (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                name={config.label}
                stroke={config.color}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
