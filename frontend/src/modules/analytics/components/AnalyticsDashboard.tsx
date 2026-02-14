"use client";

import { useState } from "react";
import {
  DollarSign,
  ShoppingCart,
  Coins,
  BookOpen,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useEnhancedDashboard } from "@/modules/analytics/hooks";
import { RevenueOverviewChart } from "./RevenueOverviewChart";
import { RevenueBreakdownCharts } from "./RevenueBreakdownCharts";
import { AnalyticsInsightsPanel } from "./AnalyticsInsightsPanel";

const PERIOD_OPTIONS = [
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
  { value: "ytd", label: "Year to Date" },
];

const STAT_ICONS = [DollarSign, ShoppingCart, Coins, BookOpen];

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <Skeleton className="h-4 w-20 mb-2" />
        <Skeleton className="h-8 w-28 mb-1" />
        <Skeleton className="h-3 w-16" />
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Period selector skeleton */}
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-6 w-48" />
      </div>
      {/* Stat cards skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
      {/* Tabs skeleton */}
      <Skeleton className="h-10 w-full max-w-lg" />
      {/* Chart skeleton */}
      <Skeleton className="h-[350px] w-full" />
      {/* Breakdown skeletons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-[300px]" />
        <Skeleton className="h-[300px]" />
      </div>
    </div>
  );
}

export function AnalyticsDashboard() {
  const [period, setPeriod] = useState("30d");
  const [compareEnabled, setCompareEnabled] = useState(false);

  const compare = compareEnabled ? "previous" : "none";
  const { data: dashboard, isLoading, error } = useEnhancedDashboard(period, compare);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="p-6">
          <p className="text-sm text-destructive text-center">
            Failed to load dashboard data. Please try again.
          </p>
        </CardContent>
      </Card>
    );
  }

  const stats = dashboard?.stats ?? [];
  const trendData = dashboard?.trend_data ?? [];
  const revenueByBook = dashboard?.revenue_by_book ?? [];
  const revenueByFormat = dashboard?.revenue_by_format ?? [];
  const insights = dashboard?.insights ?? [];

  // Build comparison data if it exists from the API
  // The comparison data would follow the same trend_data shape
  // For now we pass undefined when compare is disabled
  const comparisonTrendData = compareEnabled ? undefined : undefined;

  return (
    <div className="space-y-6">
      {/* Controls: Period selector + Compare toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            {PERIOD_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-2">
          <Switch
            id="compare-toggle"
            checked={compareEnabled}
            onCheckedChange={setCompareEnabled}
          />
          <label
            htmlFor="compare-toggle"
            className="text-sm text-muted-foreground cursor-pointer select-none"
          >
            Compare with previous period
          </label>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {stats.length > 0
          ? stats.map((stat, index) => {
              const Icon = STAT_ICONS[index % STAT_ICONS.length];
              const isPositive = stat.change_direction === "up";
              const isNegative = stat.change_direction === "down";
              const changeColor = isPositive
                ? "text-green-600"
                : isNegative
                  ? "text-red-600"
                  : "text-muted-foreground";
              const ChangeArrow = isPositive ? ArrowUp : isNegative ? ArrowDown : null;

              return (
                <Card key={index}>
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted-foreground">
                        {stat.label}
                      </span>
                      <div className="rounded-full bg-muted p-1.5">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                    <div className="text-2xl sm:text-3xl font-bold tracking-tight">
                      {stat.value}
                    </div>
                    {stat.change_percent !== null && stat.change_percent !== undefined && (
                      <div className={`flex items-center gap-1 mt-1 text-sm font-medium ${changeColor}`}>
                        {ChangeArrow && <ChangeArrow className="h-3.5 w-3.5" />}
                        <span>{Math.abs(stat.change_percent).toFixed(1)}%</span>
                        <span className="text-xs text-muted-foreground font-normal ml-1">
                          vs previous period
                        </span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          : [1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardContent className="p-4 sm:p-6 text-center text-sm text-muted-foreground">
                  No data available
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="books">Books</TabsTrigger>
          <TabsTrigger value="advertising">Advertising</TabsTrigger>
          <TabsTrigger value="kdp-reports">KDP Reports</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Revenue Trend Chart */}
          <RevenueOverviewChart
            data={trendData}
            comparisonData={comparisonTrendData}
          />

          {/* Breakdown Charts */}
          <RevenueBreakdownCharts
            revenueByBook={revenueByBook}
            revenueByFormat={revenueByFormat}
          />

          {/* AI Insights */}
          <AnalyticsInsightsPanel insights={insights} />
        </TabsContent>

        {/* Sales Tab - placeholder */}
        <TabsContent value="sales">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground text-center py-12">
                Detailed sales data coming soon. Use the Overview tab for current metrics.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Books Tab - placeholder */}
        <TabsContent value="books">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground text-center py-12">
                Per-book performance analytics coming soon. Use the Overview tab for book revenue breakdown.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advertising Tab - placeholder */}
        <TabsContent value="advertising">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground text-center py-12">
                Advertising analytics coming soon. Visit the Advertising module for campaign management.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* KDP Reports Tab - placeholder */}
        <TabsContent value="kdp-reports">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground text-center py-12">
                KDP report integration coming soon. Import your royalty data to populate this view.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
