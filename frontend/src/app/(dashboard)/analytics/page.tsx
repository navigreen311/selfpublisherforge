"use client";

import { useDashboard } from "@/modules/analytics/hooks";
import { KPICard } from "@/modules/analytics/components/KPICard";
import { RevenueChart } from "@/modules/analytics/components/RevenueChart";
import { PortfolioTable } from "@/modules/analytics/components/PortfolioTable";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart3, RefreshCw, AlertCircle, Upload } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function AnalyticsDashboardPage() {
  const { data: dashboard, isLoading, error, refetch } = useDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6" aria-busy="true" aria-label="Loading analytics dashboard">
        <h1 className="text-2xl font-bold text-foreground">Analytics Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" role="status">
          <span className="sr-only">Loading key performance indicators...</span>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card rounded-lg border p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </div>
          ))}
        </div>
        <Skeleton className="h-64 w-full" aria-label="Loading revenue chart" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Analytics Dashboard</h1>
        <Card className="border-destructive/50">
          <CardContent className="p-6">
            <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
              <div className="rounded-full bg-destructive/10 p-3">
                <AlertCircle className="h-8 w-8 text-destructive" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-semibold">Failed to load analytics data</h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  {error instanceof Error ? error.message : "An unexpected error occurred. Please try again."}
                </p>
              </div>
              <Button onClick={() => refetch()} variant="outline" className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check if we have any data at all
  const hasData = dashboard && (
    (dashboard.kpis && dashboard.kpis.length > 0) ||
    (dashboard.revenue_chart && dashboard.revenue_chart.length > 0) ||
    (dashboard.top_books && dashboard.top_books.length > 0)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">Track your revenue, sales, and book performance</p>
        </div>
        <nav aria-label="Analytics navigation" className="flex space-x-2">
          <Button variant="outline" size="sm" asChild>
            <Link href="/analytics/revenue" aria-label="View detailed revenue analytics">
              Revenue Details
            </Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/analytics/reports" aria-label="View and generate analytics reports">
              Reports
            </Link>
          </Button>
        </nav>
      </div>

      {/* Empty State - No Data */}
      {!hasData && (
        <EmptyState
          icon={BarChart3}
          title="No analytics data yet"
          description="Import your royalty reports to start tracking your publishing performance. Your revenue, sales, and book analytics will appear here."
          actionLabel="Import Royalty Data"
          onAction={() => window.location.href = "/analytics/reports"}
        />
      )}

      {/* KPI Cards */}
      {hasData && (
        <section role="region" aria-label="Key performance indicators">
          <p id="kpi-desc" className="sr-only">
            Summary cards showing key metrics including revenue, units sold, and percentage changes from the previous period.
          </p>
          <div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
            aria-describedby="kpi-desc"
          >
            {dashboard?.kpis && dashboard.kpis.length > 0 ? (
              dashboard.kpis.map((kpi, index) => (
                <KPICard key={index} kpi={kpi} />
              ))
            ) : (
              <Card className="col-span-full">
                <CardContent className="p-6 text-center text-sm text-muted-foreground">
                  No KPI data available
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      )}

      {/* Revenue Chart */}
      {hasData && (
        <section role="region" aria-label="Revenue chart">
          <p id="revenue-chart-desc" className="sr-only">
            Bar chart displaying revenue and units sold over time. Each bar represents a time period with its corresponding revenue amount and unit count.
          </p>
          <div aria-describedby="revenue-chart-desc">
            <RevenueChart data={dashboard?.revenue_chart || []} />
          </div>
        </section>
      )}

      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Books */}
        <section role="region" aria-label="Top performing books">
          <p id="top-books-desc" className="sr-only">
            Table listing your top performing books ranked by revenue, showing title, total revenue, units sold, and average revenue per unit.
          </p>
          <div aria-describedby="top-books-desc">
            <PortfolioTable
              books={
                (dashboard?.top_books || []).map((b) => ({
                  title: String(b.title || ""),
                  revenue: Number(b.revenue || 0),
                  units: Number(b.units || 0),
                }))
              }
            />
          </div>
        </section>

        {/* Platform Breakdown */}
        <section role="region" aria-label="Revenue by platform">
          <p id="platform-breakdown-desc" className="sr-only">
            Visual breakdown of revenue distribution across publishing platforms, showing each platform&apos;s revenue amount and percentage of total revenue.
          </p>
          <div
            className="bg-card rounded-lg border p-6 shadow-sm"
            aria-describedby="platform-breakdown-desc"
          >
            <h3 className="text-lg font-semibold text-foreground mb-4">Platform Breakdown</h3>
            {dashboard?.platform_breakdown &&
            Object.keys(dashboard.platform_breakdown).length > 0 ? (
              <div className="space-y-3" role="list" aria-label="Platform revenue distribution">
                {Object.entries(dashboard.platform_breakdown).map(([platform, revenue]) => {
                  const totalRevenue = Object.values(dashboard.platform_breakdown).reduce(
                    (sum, val) => sum + Number(val),
                    0
                  );
                  const percentage = totalRevenue > 0 ? (Number(revenue) / totalRevenue) * 100 : 0;
                  const formattedRevenue = Number(revenue).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  });
                  const platformName = platform.replace("_", " ");
                  return (
                    <div
                      key={platform}
                      role="listitem"
                      aria-label={`${platformName}: $${formattedRevenue}, ${percentage.toFixed(1)}% of total revenue`}
                    >
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-foreground capitalize">
                          {platformName}
                        </span>
                        <span className="text-muted-foreground">
                          ${formattedRevenue}{" "}
                          ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div
                        className="w-full bg-muted rounded-full h-2"
                        role="progressbar"
                        aria-valuenow={Math.round(percentage)}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`${platformName} revenue share: ${percentage.toFixed(1)}%`}
                      >
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-4">No platform data available</p>
            )}
          </div>
        </section>
        </div>
      )}
    </div>
  );
}
