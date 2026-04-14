"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DollarSign, Download, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import {
  useBookBreakdown,
  usePlatformBreakdown,
  useRoyaltyRecords,
  useRoyaltySummary,
} from "../hooks";
import { ImportRoyaltyModal } from "./ImportRoyaltyModal";

const CHART_COLORS = [
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#f59e0b",
  "#8b5cf6",
  "#0891b2",
];

function formatCurrency(value: number | string | null | undefined) {
  const num = Number(value ?? 0);
  return `$${num.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function KpiCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${accent ?? "text-gray-900"}`}>{value}</p>
    </div>
  );
}

export function RoyaltyDashboard() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [importOpen, setImportOpen] = useState(false);

  const summary = useRoyaltySummary(year, "ytd");
  const platform = usePlatformBreakdown(year);
  const books = useBookBreakdown(year);
  const records = useRoyaltyRecords({ year, limit: 50 });

  const hasData =
    (platform.data?.entries?.length ?? 0) > 0 ||
    (books.data?.entries?.length ?? 0) > 0 ||
    (records.data?.items?.length ?? 0) > 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Royalty Tracking</h2>
          <p className="text-sm text-muted-foreground">
            Distributor-level royalties, payouts, and monthly statements.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            aria-label="Tax year"
          >
            {[0, 1, 2, 3].map((offset) => {
              const y = currentYear - offset;
              return (
                <option key={y} value={y}>
                  {y}
                </option>
              );
            })}
          </select>
          <Button onClick={() => setImportOpen(true)} className="gap-1.5">
            <Upload className="h-4 w-4" />
            Import Royalties
          </Button>
        </div>
      </div>

      {summary.isError ? (
        <ErrorState
          message={summary.error?.message ?? "Failed to load royalty summary"}
          onRetry={() => summary.refetch()}
        />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <KpiCard
            label="YTD Earnings"
            value={summary.isLoading ? "—" : formatCurrency(summary.data?.ytd_earnings)}
            accent="text-blue-600"
          />
          <KpiCard
            label="This Month"
            value={summary.isLoading ? "—" : formatCurrency(summary.data?.month_earnings)}
            accent="text-green-600"
          />
          <KpiCard
            label="Pending Payout"
            value={summary.isLoading ? "—" : formatCurrency(summary.data?.pending_payout)}
            accent="text-amber-600"
          />
          <KpiCard
            label="Next Payout"
            value={
              summary.isLoading
                ? "—"
                : summary.data?.next_payout_date
                ? new Date(summary.data.next_payout_date).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })
                : "—"
            }
          />
        </div>
      )}

      {!hasData && !summary.isLoading && !platform.isLoading ? (
        <EmptyState
          icon={<DollarSign className="h-10 w-10" aria-hidden />}
          title="No royalty data yet"
          description="Import your royalty reports from KDP, IngramSpark, or Draft2Digital to see earnings, platform breakdowns, and tax-ready reports."
          actionLabel="Import Royalties"
          onAction={() => setImportOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold">Earnings by Platform</h3>
            {platform.isError ? (
              <ErrorState
                message={platform.error?.message ?? "Failed to load platform breakdown"}
                onRetry={() => platform.refetch()}
              />
            ) : (platform.data?.entries?.length ?? 0) === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No platform data.</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={platform.data!.entries.map((e) => ({
                      name: e.platform,
                      value: Number(e.amount),
                    }))}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={90}
                    label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                  >
                    {platform.data!.entries.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold">Top Books</h3>
            {books.isError ? (
              <ErrorState
                message={books.error?.message ?? "Failed to load book breakdown"}
                onRetry={() => books.refetch()}
              />
            ) : (books.data?.entries?.length ?? 0) === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No book data.</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={books.data!.entries.slice(0, 8).map((e) => ({
                    title: e.title.length > 20 ? `${e.title.slice(0, 20)}…` : e.title,
                    net: Number(e.net_revenue),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="title" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Bar dataKey="net" fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Royalty Records</h3>
          <Button variant="outline" size="sm" className="gap-1.5" disabled>
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </div>
        {records.isError ? (
          <ErrorState
            message={records.error?.message ?? "Failed to load records"}
            onRetry={() => records.refetch()}
          />
        ) : records.isLoading ? (
          <p className="py-6 text-center text-sm text-muted-foreground">Loading…</p>
        ) : (records.data?.items?.length ?? 0) === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No records.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
                <tr>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">Platform</th>
                  <th className="px-3 py-2">Format</th>
                  <th className="px-3 py-2 text-right">Units</th>
                  <th className="px-3 py-2 text-right">Net Revenue</th>
                  <th className="px-3 py-2">Period</th>
                </tr>
              </thead>
              <tbody>
                {records.data!.items.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-3 py-2">{r.title ?? "—"}</td>
                    <td className="px-3 py-2">{r.platform}</td>
                    <td className="px-3 py-2">{r.format_type ?? "—"}</td>
                    <td className="px-3 py-2 text-right">
                      {r.units_sold.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {formatCurrency(r.net_revenue)}
                    </td>
                    <td className="px-3 py-2">
                      {r.period_start
                        ? new Date(r.period_start).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ImportRoyaltyModal open={importOpen} onOpenChange={setImportOpen} />
    </div>
  );
}
