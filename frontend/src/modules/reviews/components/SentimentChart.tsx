"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { VelocityDataPoint } from "../types";

interface SentimentChartProps {
  data: VelocityDataPoint[];
  title?: string;
}

export function SentimentChart({ data, title = "Sentiment Trend Over Time" }: SentimentChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <p className="text-gray-500 text-center py-8">No sentiment data available</p>
      </div>
    );
  }

  const chartData = data.map((point) => ({
    date: new Date(point.period_start).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    positive: point.positive_count,
    neutral: point.neutral_count,
    negative: point.negative_count,
    total: point.review_count,
  }));

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "12px" }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="positive"
            stroke="#22c55e"
            strokeWidth={2}
            name="Positive"
            dot={{ fill: "#22c55e", r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="neutral"
            stroke="#facc15"
            strokeWidth={2}
            name="Neutral"
            dot={{ fill: "#facc15", r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="negative"
            stroke="#ef4444"
            strokeWidth={2}
            name="Negative"
            dot={{ fill: "#ef4444", r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-4 flex justify-between text-sm text-gray-500">
        <span>
          Total Reviews: {chartData.reduce((sum, d) => sum + d.total, 0).toLocaleString()}
        </span>
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Positive: {chartData.reduce((sum, d) => sum + d.positive, 0)}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
            Neutral: {chartData.reduce((sum, d) => sum + d.neutral, 0)}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-red-500 rounded-full"></span>
            Negative: {chartData.reduce((sum, d) => sum + d.negative, 0)}
          </span>
        </div>
      </div>
    </div>
  );
}
