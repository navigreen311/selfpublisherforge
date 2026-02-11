"use client";

import { useState } from "react";
import { useRevenue, usePortfolioMetrics } from "@/modules/analytics/hooks";
import { RevenueChart } from "@/modules/analytics/components/RevenueChart";
import { PortfolioTable } from "@/modules/analytics/components/PortfolioTable";
import { RoyaltyImporter } from "@/modules/analytics/components/RoyaltyImporter";

const AGGREGATION_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "yearly", label: "Yearly" },
];

const PLATFORM_OPTIONS = [
  { value: "", label: "All Platforms" },
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "draft2digital", label: "Draft2Digital" },
];

export default function RevenuePage() {
  const [aggregation, setAggregation] = useState("monthly");
  const [platform, setPlatform] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const { data: revenue, isLoading: revenueLoading } = useRevenue({
    aggregation,
    platform: platform || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  });

  const { data: portfolio, isLoading: portfolioLoading } = usePortfolioMetrics();

  const totalRevenueFormatted = Number(revenue?.total_revenue || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const totalUnitsFormatted = (revenue?.total_units || 0).toLocaleString();
  const totalBooks = portfolio?.total_books || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Revenue</h1>
        <a
          href="/analytics"
          aria-label="Back to Analytics Dashboard"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Back to Dashboard
        </a>
      </div>

      {/* Filters */}
      <div
        className="bg-card rounded-lg border p-4 shadow-sm"
        role="region"
        aria-label="Revenue filters"
      >
        <fieldset>
          <legend className="sr-only">Filter revenue data by date, platform, and aggregation</legend>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-foreground mb-1">
                Start Date
              </label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                aria-label="Filter by start date"
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-foreground mb-1">
                End Date
              </label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                aria-label="Filter by end date"
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="platform-filter" className="block text-sm font-medium text-foreground mb-1">
                Platform
              </label>
              <select
                id="platform-filter"
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                aria-label="Filter by publishing platform"
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {PLATFORM_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="aggregation-filter" className="block text-sm font-medium text-foreground mb-1">
                Aggregation
              </label>
              <select
                id="aggregation-filter"
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value)}
                aria-label="Select data aggregation period"
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {AGGREGATION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </fieldset>
      </div>

      {/* Revenue Summary */}
      <div aria-live="polite" aria-atomic="true">
        {revenueLoading ? (
          <div className="bg-card rounded-lg border p-6 animate-pulse" role="status">
            <span className="sr-only">Loading revenue data, please wait...</span>
            <div className="h-48 bg-muted rounded" />
          </div>
        ) : (
          <>
            <div
              className="grid grid-cols-1 md:grid-cols-3 gap-4"
              role="region"
              aria-label="Revenue summary statistics"
            >
              <p id="revenue-summary-desc" className="sr-only">
                Summary cards showing total revenue of ${totalRevenueFormatted}, total units sold of {totalUnitsFormatted}, and {totalBooks} portfolio books.
              </p>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label="Total Revenue"
              >
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`Total Revenue: $${totalRevenueFormatted}`}>
                  ${totalRevenueFormatted}
                </p>
              </div>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label="Total Units Sold"
              >
                <p className="text-sm text-muted-foreground">Total Units</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`Total Units: ${totalUnitsFormatted}`}>
                  {totalUnitsFormatted}
                </p>
              </div>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label="Portfolio Books Count"
              >
                <p className="text-sm text-muted-foreground">Portfolio Books</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`Portfolio Books: ${totalBooks}`}>
                  {totalBooks}
                </p>
              </div>
            </div>

            <div className="mt-6" role="region" aria-label="Revenue chart visualization">
              <p className="sr-only">
                Revenue chart displaying {aggregation} data
                {platform ? ` filtered by ${PLATFORM_OPTIONS.find(p => p.value === platform)?.label || platform}` : " across all platforms"}
                {startDate ? ` from ${startDate}` : ""}
                {endDate ? ` to ${endDate}` : ""}.
                {revenue?.data_points?.length
                  ? ` Showing ${revenue.data_points.length} data points.`
                  : " No data points available."}
              </p>
              <RevenueChart data={revenue?.data_points || []} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <div role="region" aria-label="Revenue by Book">
                <PortfolioTable
                  books={(revenue?.by_book || []).map((b) => ({
                    title: String(b.title || ""),
                    revenue: Number(b.revenue || 0),
                    units: Number(b.units || 0),
                  }))}
                  title="Revenue by Book"
                />
              </div>
              <div role="region" aria-label="Royalty Importer">
                <RoyaltyImporter />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
