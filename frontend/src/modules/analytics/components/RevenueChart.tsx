"use client";

import { type RevenueDataPoint } from "../hooks";

interface RevenueChartProps {
  data: RevenueDataPoint[];
  title?: string;
}

export function RevenueChart({ data, title = "Revenue Over Time" }: RevenueChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="mt-4 text-gray-500 text-center py-8">No revenue data available</p>
      </div>
    );
  }

  const maxRevenue = Math.max(...data.map((d) => d.revenue), 1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="flex items-end space-x-2 h-48">
        {data.map((point, index) => {
          const height = (point.revenue / maxRevenue) * 100;
          const formattedDate = new Date(point.period).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });
          return (
            <div
              key={index}
              className="flex-1 flex flex-col items-center group"
              title={`${formattedDate}: $${point.revenue.toLocaleString()} (${point.units} units)`}
            >
              <div className="w-full relative">
                <div
                  className="bg-blue-500 rounded-t hover:bg-blue-600 transition-colors w-full"
                  style={{ height: `${Math.max(height, 2)}%`, minHeight: "4px" }}
                />
              </div>
              {data.length <= 12 && (
                <span className="text-xs text-gray-500 mt-1 transform -rotate-45 origin-top-left whitespace-nowrap">
                  {formattedDate}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex justify-between text-sm text-gray-500">
        <span>
          Total: $
          {data
            .reduce((sum, d) => sum + d.revenue, 0)
            .toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
        <span>
          Units:{" "}
          {data.reduce((sum, d) => sum + d.units, 0).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
