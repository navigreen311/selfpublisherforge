"use client";

import { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface DataPoint {
  date: string;
  revenue: number;
  units: number;
  royalties: number;
  kenp: number;
}

interface RevenueOverviewChartProps {
  data: DataPoint[];
  comparisonData?: DataPoint[];
}

type Metric = "revenue" | "units" | "royalties" | "kenp";

const METRICS: { key: Metric; label: string; color: string }[] = [
  { key: "revenue", label: "Revenue", color: "#2563eb" },
  { key: "units", label: "Units", color: "#16a34a" },
  { key: "royalties", label: "Royalties", color: "#9333ea" },
  { key: "kenp", label: "KENP", color: "#ea580c" },
];

function formatXAxisDate(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatYAxisValue(value: number, metric: Metric) {
  if (metric === "revenue" || metric === "royalties") {
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
    return `$${value.toFixed(0)}`;
  }
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toFixed(0);
}

function formatTooltipValue(value: number, metric: Metric) {
  if (metric === "revenue" || metric === "royalties") {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return value.toLocaleString();
}

export function RevenueOverviewChart({ data, comparisonData }: RevenueOverviewChartProps) {
  const [activeMetrics, setActiveMetrics] = useState<Set<Metric>>(() => new Set<Metric>(["revenue"]));

  const toggleMetric = (metric: Metric) => {
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(metric)) {
        // Don't allow deselecting the last metric
        if (next.size > 1) next.delete(metric);
      } else {
        next.add(metric);
      }
      return next;
    });
  };

  // Determine primary metric for Y-axis formatting
  const primaryMetric = METRICS.find((m) => activeMetrics.has(m.key))?.key ?? "revenue";

  // Merge data with comparison for chart
  const chartData = data.map((point, i) => {
    const merged: Record<string, unknown> = { ...point, name: point.date };
    if (comparisonData && comparisonData[i]) {
      METRICS.forEach((m) => {
        merged[`prev_${m.key}`] = comparisonData[i][m.key];
      });
    }
    return merged;
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-lg border bg-background p-3 shadow-md">
        <p className="text-sm font-medium mb-1.5">{formatXAxisDate(label)}</p>
        <div className="space-y-1">
          {payload.map((entry: any) => {
            const isPrev = String(entry.dataKey).startsWith("prev_");
            const metricKey = isPrev
              ? String(entry.dataKey).replace("prev_", "") as Metric
              : entry.dataKey as Metric;
            const metricInfo = METRICS.find((m) => m.key === metricKey);
            return (
              <div key={entry.dataKey} className="flex items-center justify-between gap-4 text-sm">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  {isPrev ? `Prev ${metricInfo?.label}` : metricInfo?.label}
                </span>
                <span className="font-medium">
                  {formatTooltipValue(entry.value, metricKey)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Revenue Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-12">
            No trend data available for the selected period.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle className="text-base">Revenue Trend</CardTitle>
          <div className="flex flex-wrap gap-1.5">
            {METRICS.map((metric) => (
              <Button
                key={metric.key}
                variant={activeMetrics.has(metric.key) ? "default" : "outline"}
                size="sm"
                className="h-7 px-2.5 text-xs"
                onClick={() => toggleMetric(metric.key)}
                style={
                  activeMetrics.has(metric.key)
                    ? { backgroundColor: metric.color, borderColor: metric.color }
                    : undefined
                }
              >
                {metric.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] sm:h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxisDate}
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis
                tickFormatter={(val) => formatYAxisValue(val, primaryMetric)}
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
                width={55}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value: string) => {
                  const isPrev = value.startsWith("prev_");
                  const key = isPrev ? value.replace("prev_", "") : value;
                  const metricInfo = METRICS.find((m) => m.key === key);
                  return isPrev ? `Previous ${metricInfo?.label ?? key}` : metricInfo?.label ?? key;
                }}
              />
              {METRICS.filter((m) => activeMetrics.has(m.key)).map((metric) => (
                <Line
                  key={metric.key}
                  type="monotone"
                  dataKey={metric.key}
                  stroke={metric.color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
              {comparisonData &&
                METRICS.filter((m) => activeMetrics.has(m.key)).map((metric) => (
                  <Line
                    key={`prev_${metric.key}`}
                    type="monotone"
                    dataKey={`prev_${metric.key}`}
                    stroke={metric.color}
                    strokeWidth={1.5}
                    strokeDasharray="5 5"
                    dot={false}
                    opacity={0.5}
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
