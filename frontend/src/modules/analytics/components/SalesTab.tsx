"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useSalesData } from "../hooks";
import type { DailySalesRow } from "../types";

// --- Marketplace color palette ---

const MARKETPLACE_COLORS: Record<string, string> = {
  US: "bg-blue-500",
  UK: "bg-emerald-500",
  CA: "bg-amber-500",
  AU: "bg-violet-500",
  DE: "bg-rose-500",
  Others: "bg-slate-400",
};

function marketplaceColor(code: string): string {
  return MARKETPLACE_COLORS[code] ?? MARKETPLACE_COLORS.Others;
}

// --- Formatting helpers ---

function fmtCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function fmtInt(value: number): string {
  return value.toLocaleString();
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// --- Props ---

interface SalesTabProps {
  period?: string;
}

// --- Component ---

export function SalesTab({ period = "30d" }: SalesTabProps) {
  const { data, isLoading } = useSalesData({ period });

  // Sort daily rows by date descending (most recent first)
  const sortedDaily = useMemo(() => {
    if (!data?.daily_data) return [];
    return [...data.daily_data].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    );
  }, [data?.daily_data]);

  // Compute column totals for the footer
  const totals = useMemo(() => {
    if (sortedDaily.length === 0) {
      return { kindle: 0, print: 0, audio: 0, kenp: 0, revenue: 0, royalties: 0 };
    }
    return sortedDaily.reduce(
      (acc, row) => ({
        kindle: acc.kindle + row.kindle,
        print: acc.print + row.print,
        audio: acc.audio + row.audio,
        kenp: acc.kenp + row.kenp,
        revenue: acc.revenue + row.revenue,
        royalties: acc.royalties + row.royalties,
      }),
      { kindle: 0, print: 0, audio: 0, kenp: 0, revenue: 0, royalties: 0 },
    );
  }, [sortedDaily]);

  // Compute marketplace percentages (use provided percentage or derive from total revenue)
  const marketplaces = useMemo(() => {
    if (!data?.by_marketplace || data.by_marketplace.length === 0) return [];
    const totalRev = data.by_marketplace.reduce((s, m) => s + m.revenue, 0);
    return data.by_marketplace.map((m) => ({
      ...m,
      percentage: m.percentage ?? (totalRev > 0 ? (m.revenue / totalRev) * 100 : 0),
    }));
  }, [data?.by_marketplace]);

  // --- Loading state ---
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Daily Sales</CardTitle>
          </CardHeader>
          <CardContent>
            <TableSkeleton rows={7} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Sales by Marketplace</CardTitle>
          </CardHeader>
          <CardContent>
            <TableSkeleton rows={4} />
          </CardContent>
        </Card>
      </div>
    );
  }

  // --- Empty state ---
  if (!data || sortedDaily.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Daily Sales</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-center py-8">
              No sales data available for this period.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // --- Render ---
  return (
    <div className="space-y-6">
      {/* ---------- Daily Sales Table ---------- */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Sales</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Kindle</TableHead>
                  <TableHead className="text-right">Print</TableHead>
                  <TableHead className="text-right">Audio</TableHead>
                  <TableHead className="text-right">KU Pages</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                  <TableHead className="text-right">Royalties</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedDaily.map((row: DailySalesRow) => (
                  <TableRow key={row.date}>
                    <TableCell className="font-medium whitespace-nowrap">
                      {fmtDate(row.date)}
                    </TableCell>
                    <TableCell className="text-right">{fmtInt(row.kindle)}</TableCell>
                    <TableCell className="text-right">{fmtInt(row.print)}</TableCell>
                    <TableCell className="text-right">{fmtInt(row.audio)}</TableCell>
                    <TableCell className="text-right">{fmtInt(row.kenp)}</TableCell>
                    <TableCell className="text-right">{fmtCurrency(row.revenue)}</TableCell>
                    <TableCell className="text-right">{fmtCurrency(row.royalties)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell className="font-semibold">Month Total</TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtInt(totals.kindle)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtInt(totals.print)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtInt(totals.audio)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtInt(totals.kenp)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtCurrency(totals.revenue)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {fmtCurrency(totals.royalties)}
                  </TableCell>
                </TableRow>
              </TableFooter>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* ---------- Sales by Marketplace ---------- */}
      {marketplaces.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sales by Marketplace</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {marketplaces.map((mp) => (
                <div key={mp.marketplace} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{mp.marketplace}</span>
                    <span className="text-muted-foreground">
                      {fmtCurrency(mp.revenue)}{" "}
                      <span className="ml-1">({mp.percentage.toFixed(1)}%)</span>
                    </span>
                  </div>
                  <div className="relative h-3 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                      className={`h-full rounded-full transition-all ${marketplaceColor(mp.marketplace)}`}
                      style={{ width: `${Math.min(mp.percentage, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
