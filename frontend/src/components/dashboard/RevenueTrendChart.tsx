"use client";

import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp } from "lucide-react";
import {
  useDashboardAggregate,
  type RevenuePoint,
} from "@/modules/dashboard/hooks";

/**
 * RevenueTrendChart -- renders the revenue_trend series returned by
 * GET /api/v1/dashboard as a simple line chart. Phase 2.1 widget.
 */
export function RevenueTrendChart() {
  const { data, isLoading, isError, refetch } = useDashboardAggregate();

  const chartData = React.useMemo(() => {
    return (data?.revenue_trend ?? []).map((p: RevenuePoint) => ({
      date: p.date,
      amount: typeof p.amount === "string" ? parseFloat(p.amount) : p.amount,
    }));
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base sm:text-lg">Revenue Trend</CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          Daily net revenue over the last 30 days
        </CardDescription>
      </CardHeader>
      <CardContent className="h-64">
        {isLoading ? (
          <Skeleton className="h-full w-full" />
        ) : isError ? (
          <ErrorState
            message="Could not load revenue trend."
            onRetry={() => refetch()}
          />
        ) : chartData.length === 0 ? (
          <EmptyState
            icon={<TrendingUp />}
            title="No revenue data yet"
            description="Import royalty data to start tracking revenue trends."
          />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickFormatter={(v) =>
                  new Date(v).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })
                }
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, "Revenue"]}
                labelFormatter={(v) => new Date(v).toLocaleDateString()}
              />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export default RevenueTrendChart;
