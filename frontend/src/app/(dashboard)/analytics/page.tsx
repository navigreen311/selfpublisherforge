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
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </div>
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">Failed to load analytics data. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="flex space-x-2">
          <a
            href="/analytics/revenue"
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Revenue Details
          </a>
          <a
            href="/analytics/reports"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Reports
          </a>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {dashboard?.kpis.map((kpi, index) => (
          <KPICard key={index} kpi={kpi} />
        ))}
      </div>

      {/* Revenue Chart */}
      <RevenueChart data={dashboard?.revenue_chart || []} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Books */}
        <PortfolioTable
          books={
            (dashboard?.top_books || []).map((b) => ({
              title: String(b.title || ""),
              revenue: Number(b.revenue || 0),
              units: Number(b.units || 0),
            }))
          }
        />

        {/* Platform Breakdown */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Breakdown</h3>
          {dashboard?.platform_breakdown &&
          Object.keys(dashboard.platform_breakdown).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(dashboard.platform_breakdown).map(([platform, revenue]) => {
                const totalRevenue = Object.values(dashboard.platform_breakdown).reduce(
                  (sum, val) => sum + Number(val),
                  0
                );
                const percentage = totalRevenue > 0 ? (Number(revenue) / totalRevenue) * 100 : 0;
                return (
                  <div key={platform}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700 capitalize">
                        {platform.replace("_", " ")}
                      </span>
                      <span className="text-gray-600">
                        ${Number(revenue).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}{" "}
                        ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
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
            <p className="text-gray-500 text-center py-4">No platform data available</p>
          )}
        </div>
      </div>
    </div>
  );
}
