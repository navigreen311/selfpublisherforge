import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Analytics",
  description: "Analyze your book sales, revenue trends, and platform performance with detailed analytics and reports.",
  noindex: true,
});

"use client";

import { useDashboard } from "@/modules/analytics/hooks";
import { KPICard } from "@/modules/analytics/components/KPICard";
import { RevenueChart } from "@/modules/analytics/components/RevenueChart";
import { PortfolioTable } from "@/modules/analytics/components/PortfolioTable";
import { Skeleton } from "@/components/ui/skeleton";

export default function AnalyticsDashboardPage() {
  const { data: dashboard, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0" aria-busy="true" aria-label="Loading analytics dashboard">
        <h1 className="text-xl sm:text-2xl font-bold text-foreground">Analytics Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4" role="status">
          <span className="sr-only">Loading key performance indicators...</span>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card rounded-lg border p-4 sm:p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </div>
          ))}
        </div>
        <Skeleton className="h-48 sm:h-64 w-full" aria-label="Loading revenue chart" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
        <h1 className="text-xl sm:text-2xl font-bold text-foreground">Analytics Dashboard</h1>
        <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
          <p className="text-sm sm:text-base text-red-800">Failed to load analytics data. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-xl sm:text-2xl font-bold text-foreground">Analytics Dashboard</h1>
        <nav aria-label="Analytics navigation" className="flex flex-col sm:flex-row gap-2">
          <a
            href="/analytics/revenue"
            aria-label="View detailed revenue analytics"
            className="w-full sm:w-auto px-4 py-2 text-xs sm:text-sm font-medium text-foreground bg-card border rounded-md hover:bg-muted text-center"
          >
            Revenue Details
          </a>
          <a
            href="/analytics/reports"
            aria-label="View and generate analytics reports"
            className="w-full sm:w-auto px-4 py-2 text-xs sm:text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 text-center"
          >
            Reports
          </a>
        </nav>
      </div>

      {/* KPI Cards */}
      <section role="region" aria-label="Key performance indicators">
        <p id="kpi-desc" className="sr-only">
          Summary cards showing key metrics including revenue, units sold, and percentage changes from the previous period.
        </p>
        <div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"
          aria-describedby="kpi-desc"
        >
          {dashboard?.kpis.map((kpi, index) => (
            <KPICard key={index} kpi={kpi} />
          ))}
        </div>
      </section>

      {/* Revenue Chart */}
      <section role="region" aria-label="Revenue chart">
        <p id="revenue-chart-desc" className="sr-only">
          Bar chart displaying revenue and units sold over time. Each bar represents a time period with its corresponding revenue amount and unit count.
        </p>
        <div aria-describedby="revenue-chart-desc" className="h-[200px] sm:h-[300px]">
          <RevenueChart data={dashboard?.revenue_chart || []} />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
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
            className="bg-card rounded-lg border p-4 sm:p-6 shadow-sm"
            aria-describedby="platform-breakdown-desc"
          >
            <h3 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Platform Breakdown</h3>
            {dashboard?.platform_breakdown &&
            Object.keys(dashboard.platform_breakdown).length > 0 ? (
              <div className="space-y-2 sm:space-y-3" role="list" aria-label="Platform revenue distribution">
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
                      <div className="flex justify-between text-xs sm:text-sm mb-1 gap-2">
                        <span className="font-medium text-foreground capitalize truncate">
                          {platformName}
                        </span>
                        <span className="text-muted-foreground whitespace-nowrap">
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
    </div>
  );
}
