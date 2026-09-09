"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Funnel,
  FunnelChart,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/lib/api";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";

// ---------- Types (mirrors backend SeriesAnalyticsResponse) ----------

type FunnelStep = {
  book_id: string;
  title: string;
  series_order: number;
  unique_buyers: number;
  units_sold: number;
  revenue: number;
};

type ReadThroughRate = {
  from_order: number;
  to_order: number;
  from_title: string;
  to_title: string;
  rate: number;
  healthy: boolean;
};

type PerVolumeStat = {
  book_id: string;
  title: string;
  series_order: number;
  units_sold: number;
  revenue: number;
  bsr_avg: number | null;
  review_count: number | null;
  rating_avg: number | null;
  status: string | null;
};

type RevenuePerBook = {
  book_id: string;
  title: string;
  series_order: number;
  revenue: number;
};

type SeriesAnalyticsResponse = {
  series_id: string;
  series_name: string;
  period: string;
  funnel: FunnelStep[];
  read_through_rates: ReadThroughRate[];
  overall_read_through: number;
  avg_revenue_per_vol1_buyer: number;
  revenue_per_book: RevenuePerBook[];
  per_volume_stats: PerVolumeStat[];
  total_units: number;
  total_revenue: number;
};

// ---------- Page ----------

const PERIOD_OPTIONS = [
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
  { value: "1y", label: "Last Year" },
];

const FUNNEL_COLORS = ["#2563eb", "#4f46e5", "#7c3aed", "#9333ea", "#c026d3"];

export default function SeriesAnalyticsPage() {
  const params = useParams<{ id: string }>();
  const seriesId = params?.id;
  const [period, setPeriod] = useState<string>("90d");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<SeriesAnalyticsResponse>({
    queryKey: ["series-analytics", seriesId, period],
    enabled: Boolean(seriesId),
    queryFn: async () => {
      const res = await api.get(
        `/api/v1/series/${seriesId}/analytics`,
        { params: { period } },
      );
      return res.data as SeriesAnalyticsResponse;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4 p-6" aria-busy="true">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="h-64 bg-gray-100 rounded animate-pulse" />
        <div className="h-64 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <ErrorState
          message={
            error instanceof Error
              ? error.message
              : "Failed to load series analytics."
          }
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!data || data.funnel.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          icon={<span aria-hidden>📚</span>}
          title="No series data yet"
          description="Add books to this series and record sales to see read-through rates, a funnel, and revenue per volume."
        />
      </div>
    );
  }

  const funnelChartData = data.funnel.map((f, i) => ({
    name: `V${f.series_order}: ${f.title}`,
    value: f.unique_buyers,
    fill: FUNNEL_COLORS[i % FUNNEL_COLORS.length],
  }));

  const revenueChartData = data.revenue_per_book.map((r) => ({
    name: `V${r.series_order}`,
    title: r.title,
    revenue: r.revenue,
  }));

  const currency = (n: number) =>
    n.toLocaleString(undefined, {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    });
  const pct = (n: number) => `${Math.round(n * 100)}%`;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {data.series_name} — Series Analytics
          </h1>
          <p className="text-sm text-gray-500">
            Read-through rates, buy-through funnel, and revenue per volume.
          </p>
        </div>
        <label className="text-sm flex items-center gap-2">
          <span className="text-gray-600">Period</span>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 border rounded-lg"
            aria-label="Select period"
          >
            {PERIOD_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Read-through rate cards */}
      <section aria-labelledby="rt-heading" className="space-y-3">
        <h2 id="rt-heading" className="text-lg font-semibold">
          Read-Through Rates
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {data.read_through_rates.map((rt) => (
            <div
              key={`${rt.from_order}-${rt.to_order}`}
              className={`p-4 rounded-lg border ${
                rt.healthy
                  ? "bg-green-50 border-green-200"
                  : "bg-yellow-50 border-yellow-200"
              }`}
            >
              <div className="text-xs text-gray-600 mb-1">
                V{rt.from_order} → V{rt.to_order}
              </div>
              <div className="text-2xl font-bold">{pct(rt.rate)}</div>
              <div className="text-xs text-gray-500 mt-1">
                {rt.healthy ? "Healthy (≥ 50%)" : "Below 50%"}
              </div>
            </div>
          ))}
          <div className="p-4 rounded-lg border bg-blue-50 border-blue-200">
            <div className="text-xs text-gray-600 mb-1">Overall (V1 → last)</div>
            <div className="text-2xl font-bold">
              {pct(data.overall_read_through)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Avg revenue / V1 buyer:{" "}
              <strong>{currency(data.avg_revenue_per_vol1_buyer)}</strong>
            </div>
          </div>
        </div>
      </section>

      {/* Funnel */}
      <section aria-labelledby="funnel-heading" className="space-y-3">
        <h2 id="funnel-heading" className="text-lg font-semibold">
          Buy-Through Funnel
        </h2>
        <div className="h-80 bg-white border rounded-lg p-4">
          <ResponsiveContainer width="100%" height="100%">
            <FunnelChart>
              <Tooltip />
              <Funnel
                dataKey="value"
                data={funnelChartData}
                isAnimationActive
              >
                <LabelList
                  position="right"
                  fill="#374151"
                  stroke="none"
                  dataKey="name"
                />
                {funnelChartData.map((entry, i) => (
                  <Cell key={`cell-${i}`} fill={entry.fill} />
                ))}
              </Funnel>
            </FunnelChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Revenue bar chart */}
      <section aria-labelledby="rev-heading" className="space-y-3">
        <h2 id="rev-heading" className="text-lg font-semibold">
          Revenue per Book
        </h2>
        <div className="h-72 bg-white border rounded-lg p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={revenueChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(v) => `$${v}`} />
              <Tooltip
                formatter={(v: number) => currency(Number(v))}
                labelFormatter={(label, payload) => {
                  const title = payload?.[0]?.payload?.title;
                  return title ? `${label}: ${title}` : label;
                }}
              />
              <Bar dataKey="revenue" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Per-volume table */}
      <section aria-labelledby="vol-heading" className="space-y-3">
        <h2 id="vol-heading" className="text-lg font-semibold">
          Per-Volume Performance
        </h2>
        <div className="overflow-x-auto bg-white border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left p-3">Vol</th>
                <th className="text-left p-3">Title</th>
                <th className="text-right p-3">Units</th>
                <th className="text-right p-3">Revenue</th>
                <th className="text-right p-3">BSR (avg)</th>
                <th className="text-right p-3">Reviews</th>
                <th className="text-right p-3">Rating</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.per_volume_stats.map((v) => (
                <tr key={v.book_id} className="border-t">
                  <td className="p-3 font-medium">V{v.series_order}</td>
                  <td className="p-3">{v.title}</td>
                  <td className="p-3 text-right">
                    {v.units_sold.toLocaleString()}
                  </td>
                  <td className="p-3 text-right">{currency(v.revenue)}</td>
                  <td className="p-3 text-right">
                    {v.bsr_avg != null ? `#${v.bsr_avg.toLocaleString()}` : "—"}
                  </td>
                  <td className="p-3 text-right">
                    {v.review_count ?? "—"}
                  </td>
                  <td className="p-3 text-right">
                    {v.rating_avg != null ? v.rating_avg.toFixed(1) : "—"}
                  </td>
                  <td className="p-3 capitalize">{v.status ?? "—"}</td>
                </tr>
              ))}
              <tr className="border-t font-semibold bg-gray-50">
                <td className="p-3">Total</td>
                <td className="p-3">—</td>
                <td className="p-3 text-right">
                  {data.total_units.toLocaleString()}
                </td>
                <td className="p-3 text-right">
                  {currency(data.total_revenue)}
                </td>
                <td className="p-3 text-right">—</td>
                <td className="p-3 text-right">—</td>
                <td className="p-3 text-right">—</td>
                <td className="p-3">—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
