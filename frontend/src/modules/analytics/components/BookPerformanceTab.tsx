"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/modules/projects/hooks";
import { useBookPerformance } from "../hooks";

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------

const FORMAT_COLORS: Record<string, string> = {
  kindle: "#F59E0B",
  paperback: "#3B82F6",
  "ku pages": "#8B5CF6",
  audiobook: "#10B981",
};

function formatBSR(value: number): string {
  return `#${value.toLocaleString()}`;
}

function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
}

function colorForFormat(format: string): string {
  return FORMAT_COLORS[format.toLowerCase()] ?? "#6B7280";
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatsCards({
  stats,
}: {
  stats: {
    bsr: number;
    bsr_change: number;
    monthly_revenue: number;
    avg_daily_sales: number;
    reviews: number;
    avg_rating: number;
    new_reviews_month: number;
  };
}) {
  const bsrChangeColor =
    stats.bsr_change < 0
      ? "text-green-600" // BSR going down is good
      : stats.bsr_change > 0
        ? "text-red-600"
        : "text-gray-500";
  const bsrChangeIcon =
    stats.bsr_change < 0 ? "\u2191" : stats.bsr_change > 0 ? "\u2193" : "\u2192";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* BSR */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            BSR
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">{formatBSR(stats.bsr)}</span>
            {stats.bsr_change !== 0 && (
              <span className={`text-sm font-medium ${bsrChangeColor}`}>
                {bsrChangeIcon} {Math.abs(stats.bsr_change).toLocaleString()}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Current rank</p>
        </CardContent>
      </Card>

      {/* Monthly Revenue */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Monthly Revenue
          </CardTitle>
        </CardHeader>
        <CardContent>
          <span className="text-2xl font-bold">
            {formatCurrency(stats.monthly_revenue)}
          </span>
          <p className="mt-1 text-xs text-muted-foreground">Last 30 days</p>
        </CardContent>
      </Card>

      {/* Avg Daily Sales */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Avg Daily Sales
          </CardTitle>
        </CardHeader>
        <CardContent>
          <span className="text-2xl font-bold">
            {stats.avg_daily_sales.toFixed(1)}
          </span>
          <p className="mt-1 text-xs text-muted-foreground">Units / day</p>
        </CardContent>
      </Card>

      {/* Reviews */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Reviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">
              {stats.reviews.toLocaleString()}
            </span>
            <span className="text-sm text-amber-500 font-medium">
              {stats.avg_rating.toFixed(1)} &#9733;
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            +{stats.new_reviews_month} this month
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function BSRHistoryChart({
  data,
}: {
  data: Array<{ recorded_at: string; bsr: number; category_rank?: number; category_name?: string }>;
}) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">BSR History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-12">
            No BSR history available
          </p>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    date: formatDate(d.recorded_at),
    bsr: d.bsr,
    rawDate: d.recorded_at,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">BSR History</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              reversed
              tickFormatter={(v: number) => formatBSR(v)}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              width={80}
            />
            <Tooltip
              formatter={(value: number) => [formatBSR(value), "BSR Rank"]}
              labelFormatter={(label: string) => label}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid var(--border)",
                boxShadow: "0 2px 8px rgba(0,0,0,.08)",
              }}
            />
            <Line
              type="monotone"
              dataKey="bsr"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground text-center mt-2">
          (lower = better rank)
        </p>
      </CardContent>
    </Card>
  );
}

function RevenueBreakdown({
  data,
}: {
  data: Array<{ format: string; revenue: number; percentage: number }>;
}) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Revenue Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-12">
            No revenue breakdown available
          </p>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    label: `${d.format} - ${formatCurrency(d.revenue)} (${d.percentage.toFixed(1)}%)`,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Revenue Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={data.length * 56 + 16}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} className="stroke-muted" />
            <XAxis
              type="number"
              tickFormatter={(v: number) => `$${v.toLocaleString()}`}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="format"
              tick={{ fontSize: 13, fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              width={100}
            />
            <Tooltip
              formatter={(value: number) => [formatCurrency(value), "Revenue"]}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid var(--border)",
                boxShadow: "0 2px 8px rgba(0,0,0,.08)",
              }}
            />
            <Bar dataKey="revenue" radius={[0, 4, 4, 0]} barSize={28}>
              {chartData.map((entry, idx) => (
                <Cell key={idx} fill={colorForFormat(entry.format)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Legend / detail list */}
        <div className="mt-4 space-y-2">
          {data.map((item) => (
            <div key={item.format} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 rounded-sm"
                  style={{ backgroundColor: colorForFormat(item.format) }}
                />
                <span className="font-medium capitalize">{item.format}</span>
              </div>
              <span className="text-muted-foreground">
                {formatCurrency(item.revenue)} ({item.percentage.toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-24 mb-3" />
              <Skeleton className="h-8 w-32" />
              <Skeleton className="h-3 w-20 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
      {/* Chart skeleton */}
      <Card>
        <CardContent className="pt-6">
          <Skeleton className="h-5 w-32 mb-4" />
          <Skeleton className="h-80 w-full" />
        </CardContent>
      </Card>
      {/* Breakdown skeleton */}
      <Card>
        <CardContent className="pt-6">
          <Skeleton className="h-5 w-44 mb-4" />
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function BookPerformanceTab() {
  const [selectedBookId, setSelectedBookId] = useState<string>("");
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { data: performance, isLoading: performanceLoading } =
    useBookPerformance(selectedBookId);

  return (
    <div className="space-y-6">
      {/* Book Selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-muted-foreground whitespace-nowrap">
          Select Book
        </label>
        <Select value={selectedBookId} onValueChange={setSelectedBookId}>
          <SelectTrigger className="w-full max-w-sm">
            <SelectValue placeholder={projectsLoading ? "Loading books..." : "Choose a book"} />
          </SelectTrigger>
          <SelectContent>
            {projects?.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Empty state — no book selected */}
      {!selectedBookId && (
        <Card>
          <CardContent className="py-16">
            <p className="text-center text-muted-foreground">
              Select a book above to view its performance data.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Loading state */}
      {selectedBookId && performanceLoading && <LoadingSkeleton />}

      {/* Populated state */}
      {selectedBookId && performance && !performanceLoading && (
        <>
          <StatsCards stats={performance.stats} />
          <BSRHistoryChart data={performance.bsr_history} />
          <RevenueBreakdown data={performance.revenue_breakdown} />
        </>
      )}
    </div>
  );
}
