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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Revenue</h1>
        <a
          href="/analytics"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Back to Dashboard
        </a>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="platform-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Platform
            </label>
            <select
              id="platform-filter"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PLATFORM_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="aggregation-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Aggregation
            </label>
            <select
              id="aggregation-filter"
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {AGGREGATION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Revenue Summary */}
      {revenueLoading ? (
        <div className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
          <div className="h-48 bg-gray-200 rounded" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <p className="text-sm text-gray-600">Total Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                $
                {Number(revenue?.total_revenue || 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <p className="text-sm text-gray-600">Total Units</p>
              <p className="text-2xl font-bold text-gray-900">
                {(revenue?.total_units || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <p className="text-sm text-gray-600">Portfolio Books</p>
              <p className="text-2xl font-bold text-gray-900">
                {portfolio?.total_books || 0}
              </p>
            </div>
          </div>

          <RevenueChart data={revenue?.data_points || []} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PortfolioTable
              books={(revenue?.by_book || []).map((b) => ({
                title: String(b.title || ""),
                revenue: Number(b.revenue || 0),
                units: Number(b.units || 0),
              }))}
              title="Revenue by Book"
            />
            <RoyaltyImporter />
          </div>
        </>
      )}
    </div>
  );
}
