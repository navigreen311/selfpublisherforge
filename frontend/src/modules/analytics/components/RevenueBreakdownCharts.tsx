"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface BookRevenue {
  book_title: string;
  revenue: number;
  percentage: number;
}

interface FormatRevenue {
  format: string;
  revenue: number;
  percentage: number;
}

interface RevenueBreakdownChartsProps {
  revenueByBook: BookRevenue[];
  revenueByFormat: FormatRevenue[];
}

const BOOK_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#db2777",
  "#ea580c",
  "#16a34a",
  "#0891b2",
  "#4f46e5",
  "#be123c",
];

const FORMAT_COLORS: Record<string, string> = {
  Kindle: "#f59e0b",
  Print: "#2563eb",
  "KU Pages": "#16a34a",
  Audio: "#9333ea",
};

function formatCurrency(value: number) {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  return `$${value.toFixed(0)}`;
}

const CustomBarTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  const label = item.book_title || item.format || "";
  return (
    <div className="rounded-lg border bg-background p-3 shadow-md text-sm">
      <p className="font-medium mb-1">{label}</p>
      <p className="text-muted-foreground">
        ${Number(item.revenue).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        {" "}({item.percentage.toFixed(1)}%)
      </p>
    </div>
  );
};

export function RevenueBreakdownCharts({
  revenueByBook,
  revenueByFormat,
}: RevenueBreakdownChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
      {/* Revenue by Book */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Revenue by Book</CardTitle>
        </CardHeader>
        <CardContent>
          {revenueByBook && revenueByBook.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={revenueByBook}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} className="stroke-muted" />
                  <XAxis
                    type="number"
                    tickFormatter={formatCurrency}
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    type="category"
                    dataKey="book_title"
                    width={120}
                    tick={{ fontSize: 11 }}
                    className="text-muted-foreground"
                    tickFormatter={(value: string) =>
                      value.length > 18 ? `${value.slice(0, 18)}...` : value
                    }
                  />
                  <Tooltip content={<CustomBarTooltip />} />
                  <Bar dataKey="revenue" radius={[0, 4, 4, 0]} maxBarSize={28}>
                    {revenueByBook.map((_, index) => (
                      <Cell
                        key={`book-${index}`}
                        fill={BOOK_COLORS[index % BOOK_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">
              No book revenue data available.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Revenue by Format */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Revenue by Format</CardTitle>
        </CardHeader>
        <CardContent>
          {revenueByFormat && revenueByFormat.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={revenueByFormat}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} className="stroke-muted" />
                  <XAxis
                    type="number"
                    tickFormatter={formatCurrency}
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    type="category"
                    dataKey="format"
                    width={90}
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <Tooltip content={<CustomBarTooltip />} />
                  <Bar dataKey="revenue" radius={[0, 4, 4, 0]} maxBarSize={32}>
                    {revenueByFormat.map((item, index) => (
                      <Cell
                        key={`format-${index}`}
                        fill={FORMAT_COLORS[item.format] || BOOK_COLORS[index % BOOK_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">
              No format revenue data available.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
