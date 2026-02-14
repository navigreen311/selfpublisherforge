"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type MetricKey = "spend" | "sales" | "acos" | "impressions" | "clicks";

interface TrendDataPoint {
  date: string;
  spend: number;
  sales: number;
  impressions: number;
  clicks: number;
  orders: number;
}

interface PerformanceTrendChartProps {
  data: TrendDataPoint[];
  period: string;
  onPeriodChange: (p: string) => void;
}

const METRIC_CONFIG: Record<
  MetricKey,
  { color: string; label: string; formatter: (v: number) => string }
> = {
  spend: {
    color: "#3b82f6",
    label: "Spend",
    formatter: (v) => `$${v.toFixed(2)}`,
  },
  sales: {
    color: "#22c55e",
    label: "Sales",
    formatter: (v) => `$${v.toFixed(2)}`,
  },
  acos: {
    color: "#f97316",
    label: "ACOS",
    formatter: (v) => `${v.toFixed(1)}%`,
  },
  impressions: {
    color: "#8b5cf6",
    label: "Impressions",
    formatter: (v) => v.toLocaleString(),
  },
  clicks: {
    color: "#6b7280",
    label: "Clicks",
    formatter: (v) => v.toLocaleString(),
  },
};

const PERIODS = ["7d", "30d", "60d", "90d"];

export function PerformanceTrendChart({
  data,
  period,
  onPeriodChange,
}: PerformanceTrendChartProps) {
  const [selectedMetrics, setSelectedMetrics] = useState<MetricKey[]>([
    "spend",
    "sales",
    "acos",
  ]);

  const toggleMetric = (metric: MetricKey) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric]
    );
  };

  const chartData = data
    .slice()
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((record) => {
      const spend = record.spend;
      const sales = record.sales;
      const acos = sales > 0 ? (spend / sales) * 100 : 0;
      return {
        ...record,
        acos,
        dateLabel: format(new Date(record.date), "MMM dd"),
      };
    });

  const hasMoneyMetric = selectedMetrics.some((m) => m === "spend" || m === "sales");
  const hasPercentMetric = selectedMetrics.includes("acos");
  const hasCountMetric = selectedMetrics.some((m) => m === "impressions" || m === "clicks");

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="text-lg">Performance Trends</CardTitle>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <Button
                key={p}
                variant={period === p ? "default" : "outline"}
                size="sm"
                onClick={() => onPeriodChange(p)}
              >
                {p}
              </Button>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((metric) => {
            const config = METRIC_CONFIG[metric];
            const isSelected = selectedMetrics.includes(metric);
            return (
              <Button
                key={metric}
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => toggleMetric(metric)}
                className="text-xs"
                style={
                  isSelected
                    ? { backgroundColor: config.color, borderColor: config.color }
                    : { color: config.color, borderColor: config.color }
                }
              >
                {config.label}
              </Button>
            );
          })}
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-64 border rounded-lg bg-muted/10">
            <p className="text-muted-foreground">
              No performance data available for this period
            </p>
          </div>
        ) : (
          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="dateLabel" fontSize={12} />
                <YAxis
                  yAxisId="left"
                  fontSize={12}
                  tickFormatter={(v: number) => {
                    if (hasMoneyMetric) return `$${v}`;
                    if (hasPercentMetric) return `${v}%`;
                    return v.toLocaleString();
                  }}
                />
                {(hasCountMetric && (hasMoneyMetric || hasPercentMetric)) && (
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    fontSize={12}
                    tickFormatter={(v: number) => v.toLocaleString()}
                  />
                )}
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number, name: string) => {
                    const metricKey = Object.entries(METRIC_CONFIG).find(
                      ([, c]) => c.label === name
                    )?.[0] as MetricKey | undefined;
                    if (metricKey) {
                      return [METRIC_CONFIG[metricKey].formatter(value), name];
                    }
                    return [value, name];
                  }}
                />
                {selectedMetrics.map((metric) => {
                  const config = METRIC_CONFIG[metric];
                  const useRightAxis =
                    (metric === "impressions" || metric === "clicks") &&
                    (hasMoneyMetric || hasPercentMetric);
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
                      yAxisId={useRightAxis ? "right" : "left"}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
