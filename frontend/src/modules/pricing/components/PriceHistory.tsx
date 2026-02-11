"use client";

import { Card } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface PriceHistoryEntry {
  date: string;
  price: number;
  royaltyRate: number;
  sales?: number;
}

interface PriceHistoryProps {
  bookId?: string;
  data?: PriceHistoryEntry[];
}

// Mock data for demonstration
const MOCK_DATA: PriceHistoryEntry[] = [
  { date: "2024-01", price: 2.99, royaltyRate: 0.7, sales: 45 },
  { date: "2024-02", price: 2.99, royaltyRate: 0.7, sales: 52 },
  { date: "2024-03", price: 4.99, royaltyRate: 0.7, sales: 38 },
  { date: "2024-04", price: 4.99, royaltyRate: 0.7, sales: 41 },
  { date: "2024-05", price: 3.99, royaltyRate: 0.7, sales: 48 },
  { date: "2024-06", price: 3.99, royaltyRate: 0.7, sales: 50 },
  { date: "2024-07", price: 0.99, royaltyRate: 0.35, sales: 120 },
  { date: "2024-08", price: 4.99, royaltyRate: 0.7, sales: 35 },
  { date: "2024-09", price: 4.99, royaltyRate: 0.7, sales: 40 },
  { date: "2024-10", price: 4.99, royaltyRate: 0.7, sales: 42 },
];

export function PriceHistory({ data = MOCK_DATA }: PriceHistoryProps) {
  if (!data || data.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Price Change History</h3>
        <p className="text-muted-foreground text-center py-8">No price history available</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Price Change History</h3>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-600 rounded" />
            <span>Price</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-600 rounded" />
            <span>Sales</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
            }}
          />
          <YAxis
            yAxisId="price"
            orientation="left"
            tick={{ fontSize: 12 }}
            label={{ value: "Price ($)", angle: -90, position: "insideLeft" }}
          />
          <YAxis
            yAxisId="sales"
            orientation="right"
            tick={{ fontSize: 12 }}
            label={{ value: "Sales", angle: 90, position: "insideRight" }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const data = payload[0].payload as PriceHistoryEntry;
              return (
                <div className="bg-background border rounded-lg shadow-lg p-3">
                  <p className="font-medium">{data.date}</p>
                  <p className="text-sm">
                    Price: <span className="font-medium">${data.price.toFixed(2)}</span>
                  </p>
                  <p className="text-sm">
                    Royalty: <span className="font-medium">{(data.royaltyRate * 100).toFixed(0)}%</span>
                  </p>
                  {data.sales !== undefined && (
                    <p className="text-sm">
                      Sales: <span className="font-medium">{data.sales} units</span>
                    </p>
                  )}
                </div>
              );
            }}
          />
          <Legend />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="price"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ fill: "#2563eb", r: 4 }}
            name="Price ($)"
          />
          {data.some((d) => d.sales !== undefined) && (
            <Line
              yAxisId="sales"
              type="monotone"
              dataKey="sales"
              stroke="#16a34a"
              strokeWidth={2}
              dot={{ fill: "#16a34a", r: 4 }}
              name="Sales (units)"
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Price Change Summary */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold">${Math.min(...data.map((d) => d.price)).toFixed(2)}</div>
          <div className="text-xs text-muted-foreground">Lowest Price</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">${Math.max(...data.map((d) => d.price)).toFixed(2)}</div>
          <div className="text-xs text-muted-foreground">Highest Price</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">${data[data.length - 1].price.toFixed(2)}</div>
          <div className="text-xs text-muted-foreground">Current Price</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">
            {data.filter((d, i) => i > 0 && d.price !== data[i - 1].price).length}
          </div>
          <div className="text-xs text-muted-foreground">Price Changes</div>
        </div>
      </div>
    </Card>
  );
}
