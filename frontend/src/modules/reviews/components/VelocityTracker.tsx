"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { VelocityTrend, type VelocityReport } from "../types";

interface VelocityTrackerProps {
  velocityReport: VelocityReport;
}

export function VelocityTracker({ velocityReport }: VelocityTrackerProps) {
  const chartData = velocityReport.data_points.map((point) => ({
    date: new Date(point.period_start).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    reviews: point.review_count,
    avgRating: point.avg_rating || 0,
  }));

  const trendColor = getTrendColor(velocityReport.trend);
  const trendIcon = getTrendIcon(velocityReport.trend);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Review Velocity</h3>
        <Badge className={trendColor}>
          {trendIcon} {velocityReport.trend.charAt(0).toUpperCase() + velocityReport.trend.slice(1)}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">
            {velocityReport.current_rate.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">Current Rate / {velocityReport.period}</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">
            {velocityReport.previous_rate.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">Previous Rate</p>
        </div>
        <div className="text-center">
          <p
            className={`text-2xl font-bold ${
              velocityReport.change_pct >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {velocityReport.change_pct >= 0 ? "+" : ""}
            {velocityReport.change_pct.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">Change</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorReviews" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
            </linearGradient>
          </defs>
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
          <Area
            type="monotone"
            dataKey="reviews"
            stroke="#3b82f6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorReviews)"
          />
        </AreaChart>
      </ResponsiveContainer>

      {velocityReport.anomalies.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm font-medium text-yellow-800 mb-1">Anomalies Detected</p>
          <ul className="text-xs text-yellow-700 space-y-1">
            {velocityReport.anomalies.slice(0, 3).map((anomaly, idx) => (
              <li key={idx}>• {JSON.stringify(anomaly)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function getTrendColor(trend: VelocityTrend): string {
  switch (trend) {
    case VelocityTrend.RISING:
      return "bg-green-100 text-green-800 border-green-300";
    case VelocityTrend.DECLINING:
      return "bg-red-100 text-red-800 border-red-300";
    case VelocityTrend.STABLE:
      return "bg-blue-100 text-blue-800 border-blue-300";
    default:
      return "bg-gray-100 text-gray-800 border-gray-300";
  }
}

function getTrendIcon(trend: VelocityTrend): string {
  switch (trend) {
    case VelocityTrend.RISING:
      return "↑";
    case VelocityTrend.DECLINING:
      return "↓";
    case VelocityTrend.STABLE:
      return "→";
    default:
      return "";
  }
}
