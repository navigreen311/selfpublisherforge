"use client";

import { useState } from "react";
import { useRevenue, usePortfolioMetrics } from "@/modules/analytics/hooks";
import { RevenueChart } from "@/modules/analytics/components/RevenueChart";
import { PortfolioTable } from "@/modules/analytics/components/PortfolioTable";
import { RoyaltyImporter } from "@/modules/analytics/components/RoyaltyImporter";
import { useTranslations } from "@/hooks/use-translations";

export default function RevenuePage() {
  const t = useTranslations("analytics");
  const [aggregation, setAggregation] = useState("monthly");
  const [platform, setPlatform] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const AGGREGATION_OPTIONS = [
    { value: "daily", label: t("revenue.daily") },
    { value: "weekly", label: t("revenue.weekly") },
    { value: "monthly", label: t("revenue.monthly") },
    { value: "quarterly", label: t("revenue.quarterly") },
    { value: "yearly", label: t("revenue.yearly") },
  ];

  const PLATFORM_OPTIONS = [
    { value: "", label: t("revenue.allPlatforms") },
    { value: "kdp", label: t("revenue.amazonKdp") },
    { value: "ingram_spark", label: t("revenue.ingramSpark") },
    { value: "draft2digital", label: t("revenue.draft2digital") },
  ];

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
        <h1 className="text-2xl font-bold text-foreground">{t("revenue.title")}</h1>
        <a
          href="/analytics"
          aria-label={t("revenue.backToDashboard")}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {t("revenue.backToDashboard")}
        </a>
      </div>

      {/* Filters */}
      <div
        className="bg-card rounded-lg border p-4 shadow-sm"
        role="region"
        aria-label={t("revenue.filters")}
      >
        <fieldset>
          <legend className="sr-only">{t("revenue.filtersLegend")}</legend>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-foreground mb-1">
                {t("revenue.startDate")}
              </label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                aria-label={t("revenue.startDate")}
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-foreground mb-1">
                {t("revenue.endDate")}
              </label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                aria-label={t("revenue.endDate")}
                className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="platform-filter" className="block text-sm font-medium text-foreground mb-1">
                {t("revenue.platform")}
              </label>
              <select
                id="platform-filter"
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                aria-label={t("revenue.platform")}
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
                {t("revenue.aggregation")}
              </label>
              <select
                id="aggregation-filter"
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value)}
                aria-label={t("revenue.aggregation")}
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
            <span className="sr-only">{t("revenue.loadingRevenue")}</span>
            <div className="h-48 bg-muted rounded" />
          </div>
        ) : (
          <>
            <div
              className="grid grid-cols-1 md:grid-cols-3 gap-4"
              role="region"
              aria-label={t("revenue.totalRevenue")}
            >
              <p id="revenue-summary-desc" className="sr-only">
                {t("revenue.summaryDescription", {
                  totalRevenue: totalRevenueFormatted,
                  totalUnits: totalUnitsFormatted,
                  totalBooks: totalBooks.toString(),
                })}
              </p>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label={t("revenue.totalRevenue")}
              >
                <p className="text-sm text-muted-foreground">{t("revenue.totalRevenue")}</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`${t("revenue.totalRevenue")}: $${totalRevenueFormatted}`}>
                  ${totalRevenueFormatted}
                </p>
              </div>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label={t("revenue.totalUnits")}
              >
                <p className="text-sm text-muted-foreground">{t("revenue.totalUnits")}</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`${t("revenue.totalUnits")}: ${totalUnitsFormatted}`}>
                  {totalUnitsFormatted}
                </p>
              </div>
              <div
                className="bg-card rounded-lg border p-6 shadow-sm"
                role="group"
                aria-label={t("revenue.portfolioBooks")}
              >
                <p className="text-sm text-muted-foreground">{t("revenue.portfolioBooks")}</p>
                <p className="text-2xl font-bold text-foreground" aria-label={`${t("revenue.portfolioBooks")}: ${totalBooks}`}>
                  {totalBooks}
                </p>
              </div>
            </div>

            <div className="mt-6" role="region" aria-label={t("revenueChart.title")}>
              <p className="sr-only">
                {t("revenue.chartDescription", {
                  aggregation,
                  platform: platform ? t("revenue.chartFilterPlatform", { platform: PLATFORM_OPTIONS.find(p => p.value === platform)?.label || platform }) : "",
                  startDate: startDate ? t("revenue.chartFilterStart", { date: startDate }) : "",
                  endDate: endDate ? t("revenue.chartFilterEnd", { date: endDate }) : "",
                  dataPoints: revenue?.data_points?.length
                    ? t("revenue.chartDataPoints", { count: revenue.data_points.length.toString() })
                    : t("revenue.chartNoData"),
                })}
              </p>
              <RevenueChart data={revenue?.data_points || []} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <div role="region" aria-label={t("revenue.revenueByBook")}>
                <PortfolioTable
                  books={(revenue?.by_book || []).map((b) => ({
                    title: String(b.title || ""),
                    revenue: Number(b.revenue || 0),
                    units: Number(b.units || 0),
                  }))}
                  title={t("revenue.revenueByBook")}
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
