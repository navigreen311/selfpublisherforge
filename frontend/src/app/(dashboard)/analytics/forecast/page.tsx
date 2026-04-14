"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { TrendingDown, TrendingUp, Sparkles, BarChart3 } from "lucide-react";

type Horizon = 30 | 90 | 180;

interface ForecastPoint {
  date: string;
  actual?: number | null;
  projected?: number | null;
  conf_low?: number | null;
  conf_high?: number | null;
}

interface ForecastSummary {
  horizon_days: number;
  expected_revenue: number;
  best_case: number;
  worst_case: number;
  trend_pct: number;
  confidence: number;
  past_actual_total: number;
}

interface ForecastResponse {
  horizon_days: number;
  summary: ForecastSummary;
  chart_data: ForecastPoint[];
  seasonality_insights: string[];
  currency: string;
}

function useForecast(horizon: Horizon) {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", "revenue", horizon],
    queryFn: async () => {
      const { data } = await api.get(
        `/api/v1/forecast/revenue?horizon_days=${horizon}`,
      );
      return data;
    },
  });
}

function money(v: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(v);
}

export default function ForecastPage() {
  const [horizon, setHorizon] = React.useState<Horizon>(90);
  const { data, isLoading, isError, refetch } = useForecast(horizon);

  const chartData = React.useMemo(() => {
    if (!data) return [];
    return data.chart_data.map((p) => ({
      date: p.date,
      actual: p.actual ?? null,
      projected: p.projected ?? null,
      band:
        p.conf_low != null && p.conf_high != null
          ? [p.conf_low, p.conf_high]
          : null,
    }));
  }, [data]);

  const hasData = (data?.chart_data ?? []).some(
    (p) => (p.actual ?? 0) > 0 || (p.projected ?? 0) > 0,
  );

  return (
    <div className="p-4 sm:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Revenue Forecast
          </h1>
          <p className="text-sm text-gray-500">
            AI-powered projection based on historical royalties with seasonal
            adjustment.
          </p>
        </div>
        <div className="flex gap-2" role="tablist" aria-label="Forecast horizon">
          {[30, 90, 180].map((h) => (
            <Button
              key={h}
              variant={horizon === h ? "default" : "outline"}
              size="sm"
              onClick={() => setHorizon(h as Horizon)}
              aria-pressed={horizon === h}
            >
              {h} days
            </Button>
          ))}
        </div>
      </div>

      {isError ? (
        <ErrorState
          message="Could not load forecast."
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : !hasData ? (
        <EmptyState
          icon={<BarChart3 />}
          title="No sales history yet"
          description="Import royalty data or connect a sales source to see an AI-powered forecast."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              label="Expected revenue"
              value={money(data!.summary.expected_revenue, data!.currency)}
              sub={`Next ${horizon} days`}
            />
            <SummaryCard
              label="Best case"
              value={money(data!.summary.best_case, data!.currency)}
              sub="Upper confidence band"
              accent="text-green-600"
            />
            <SummaryCard
              label="Worst case"
              value={money(data!.summary.worst_case, data!.currency)}
              sub="Lower confidence band"
              accent="text-red-600"
            />
            <SummaryCard
              label="Trend"
              value={`${data!.summary.trend_pct > 0 ? "+" : ""}${data!.summary.trend_pct.toFixed(1)}%`}
              sub={`Confidence ${(data!.summary.confidence * 100).toFixed(0)}%`}
              accent={
                data!.summary.trend_pct >= 0 ? "text-green-600" : "text-red-600"
              }
              icon={
                data!.summary.trend_pct >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )
              }
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base sm:text-lg">
                Historical + Forecast
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Solid = actual, dashed = projected, shaded band = confidence.
              </CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value: unknown) => {
                      if (Array.isArray(value)) {
                        return [
                          `${money(Number(value[0]))} – ${money(Number(value[1]))}`,
                          "Confidence band",
                        ];
                      }
                      if (typeof value === "number") return money(value);
                      return String(value);
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="band"
                    stroke="none"
                    fill="#60a5fa"
                    fillOpacity={0.2}
                    name="Confidence band"
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    name="Actual"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="projected"
                    stroke="#7c3aed"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Projected"
                    connectNulls
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {data!.seasonality_insights.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-500" />
                  Seasonality insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-700">
                  {data!.seasonality_insights.map((insight, i) => (
                    <li key={i} className="flex gap-2">
                      <span aria-hidden>•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <p className="text-xs text-gray-400">
            Past {Math.max(90, horizon * 2)}-day actual:{" "}
            {money(data!.summary.past_actual_total, data!.currency)}
          </p>
        </>
      )}
    </div>
  );
}

interface SummaryCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
  icon?: React.ReactNode;
}

function SummaryCard({ label, value, sub, accent, icon }: SummaryCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-gray-500 flex items-center gap-1">
          {icon}
          {label}
        </div>
        <div className={`mt-1 text-2xl font-semibold ${accent ?? ""}`}>
          {value}
        </div>
        {sub && <div className="mt-1 text-xs text-gray-400">{sub}</div>}
      </CardContent>
    </Card>
  );
}
