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
import type { BSRHistoryPoint, CompetitorDetail } from "../hooks";

interface CompetitorChartProps {
  competitor: CompetitorDetail;
}

export function CompetitorChart({ competitor }: CompetitorChartProps) {
  const chartData = competitor.bsr_history.map((point) => ({
    date: new Date(point.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    bsr: point.bsr,
    price: point.price,
  }));

  if (!chartData.length) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        No BSR history available yet.
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-card p-4">
      <div className="mb-4">
        <h4 className="font-semibold text-sm">{competitor.title}</h4>
        <p className="text-xs text-muted-foreground">
          ASIN: {competitor.asin} | By {competitor.author}
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
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="price"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            name="Price"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
