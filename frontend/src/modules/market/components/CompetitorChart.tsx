"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Users } from "lucide-react";
import type { CompetitorDetail } from "../hooks";

interface CompetitorChartProps {
  competitor: CompetitorDetail | null | undefined;
}

export function CompetitorChart({ competitor }: CompetitorChartProps) {
  // Handle null/undefined competitor prop
  if (!competitor) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="rounded-full bg-muted p-3 mb-3">
          <Users className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground">
          No competitor data available
        </p>
      </div>
    );
  }

  const bsrHistory = competitor.bsr_history ?? [];

  const chartData = bsrHistory.map((point) => ({
    date: new Date(point.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    bsr: point.bsr ?? 0,
    price: point.price ?? null,
  }));

  // Handle empty data array
  if (chartData.length === 0) {
    return (
      <div className="border rounded-lg bg-card p-4">
        <div className="mb-4">
          <h4 className="font-semibold text-sm">
            {competitor.title ?? "Unknown Title"}
          </h4>
          <p className="text-xs text-muted-foreground">
            ASIN: {competitor.asin ?? "N/A"} | By{" "}
            {competitor.author ?? "Unknown"}
          </p>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="rounded-full bg-muted p-3 mb-3">
            <Users className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">
            No competitor data available
          </p>
        </div>
      </div>
    );
  }

  // Check if any data points have price info for the price axis
  const hasPriceData = chartData.some((d) => d.price != null);

  return (
    <div
      className="border rounded-lg bg-card p-4"
      role="img"
      aria-label={`BSR and price history chart for ${competitor.title ?? "competitor"}`}
    >
      <div className="mb-4">
        <h4 className="font-semibold text-sm">
          {competitor.title ?? "Unknown Title"}
        </h4>
        <p className="text-xs text-muted-foreground">
          ASIN: {competitor.asin ?? "N/A"} | By{" "}
          {competitor.author ?? "Unknown"}
        </p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="bsr"
            reversed
            tick={{ fontSize: 11 }}
            label={{
              value: "BSR (lower is better)",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 11 },
            }}
          />
          {hasPriceData && (
            <YAxis
              yAxisId="price"
              orientation="right"
              tick={{ fontSize: 11 }}
              label={{
                value: "Price ($)",
                angle: 90,
                position: "insideRight",
                style: { fontSize: 11 },
              }}
            />
          )}
          <Tooltip />
          <Legend />
          <Line
            yAxisId="bsr"
            type="monotone"
            dataKey="bsr"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            name="BSR"
          />
          {hasPriceData && (
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="price"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="Price"
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
