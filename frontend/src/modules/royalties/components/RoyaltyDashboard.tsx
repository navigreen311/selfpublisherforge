"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  useRoyaltyDashboard,
  useMonthlyStatement,
  downloadRoyaltyExport,
} from "../hooks";
import { DISTRIBUTOR_LABELS } from "../types";
import { RoyaltyImporterPanel } from "./RoyaltyImporterPanel";
import { ManualRoyaltyEntryForm } from "./ManualRoyaltyEntryForm";

const YEARS = [2024, 2025, 2026, 2027];

export function RoyaltyDashboard() {
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const { data: dashboard, isLoading } = useRoyaltyDashboard(year);
  const { data: statement } = useMonthlyStatement(year);

  if (isLoading) return <div>Loading...</div>;
  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <label className="text-sm">Year:</label>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded border px-2 py-1 text-sm"
        >
          {YEARS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="YTD Earnings" value={`$${dashboard.ytd_earnings}`} />
        <KpiCard label="This Month" value={`$${dashboard.this_month_earnings}`} />
        <KpiCard label="Pending Payout" value={`$${dashboard.pending_payout}`} />
        <KpiCard
          label="Next Payout"
          value={dashboard.next_payout_date ?? "—"}
        />
      </div>

      {/* By distributor */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Earnings by Distributor</h2>
        {dashboard.by_distributor.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-muted-foreground">
              No royalty data yet. Import a report or add a manual entry below.
            </CardContent>
          </Card>
        ) : (
          dashboard.by_distributor.map((d) => (
            <Card key={d.distributor}>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>
                    {DISTRIBUTOR_LABELS[d.distributor] ?? d.distributor}
                  </span>
                  <span className="text-base font-mono">
                    ${d.total} ({d.pct.toFixed(1)}%)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                {Object.entries(d.breakdown).map(([type, amt]) => (
                  <div key={type} className="flex justify-between">
                    <span className="capitalize">{type.replace("_", " ")}</span>
                    <span className="font-mono">${amt}</span>
                  </div>
                ))}
                {d.kenp_pages > 0 && (
                  <div className="text-xs text-muted-foreground">
                    KENP pages: {d.kenp_pages.toLocaleString()}
                  </div>
                )}
                {d.last_payment_date && (
                  <div className="text-xs text-muted-foreground">
                    Last payment: ${d.last_payment_amount} on{" "}
                    {d.last_payment_date}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </section>

      {/* Monthly statement */}
      {statement && (
        <section className="space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Monthly Statement</h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => downloadRoyaltyExport("csv", year)}
              >
                Export CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => downloadRoyaltyExport("pdf", year)}
              >
                Export PDF
              </Button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm border">
              <thead className="bg-muted">
                <tr>
                  <th className="px-3 py-2 text-left">Month</th>
                  <th className="px-3 py-2 text-right">KDP eBook</th>
                  <th className="px-3 py-2 text-right">KDP Print</th>
                  <th className="px-3 py-2 text-right">KU/KENP</th>
                  <th className="px-3 py-2 text-right">Ingram</th>
                  <th className="px-3 py-2 text-right">D2D</th>
                  <th className="px-3 py-2 text-right">Other</th>
                  <th className="px-3 py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {statement.rows.map((r) => (
                  <tr key={r.month} className="border-t">
                    <td className="px-3 py-2">{r.label}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.kdp_ebook}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.kdp_print}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.ku_kenp}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.ingram}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.d2d}</td>
                    <td className="px-3 py-2 text-right font-mono">${r.other}</td>
                    <td className="px-3 py-2 text-right font-mono font-semibold">
                      ${r.total}
                    </td>
                  </tr>
                ))}
                <tr className="border-t-2 font-semibold bg-muted/50">
                  <td className="px-3 py-2">{statement.ytd_totals.label}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.kdp_ebook}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.kdp_print}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.ku_kenp}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.ingram}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.d2d}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.other}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    ${statement.ytd_totals.total}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Import & Manual entry */}
      <div className="grid md:grid-cols-2 gap-6">
        <RoyaltyImporterPanel />
        <ManualRoyaltyEntryForm defaultYear={year} />
      </div>
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wide">
          {label}
        </div>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}
