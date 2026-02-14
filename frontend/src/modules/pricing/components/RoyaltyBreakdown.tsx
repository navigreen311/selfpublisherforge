"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { AlertTriangle, Info } from "lucide-react";
import { useRoyaltyAnalysis } from "../hooks";

interface RoyaltyRow {
  book: string;
  price?: number;
  format: string;
  rate?: string;
  units: number;
  revenue: number;
  royalty: number;
}

const MOCK_ROYALTY_DATA: RoyaltyRow[] = [
  { book: "Keto Guide", price: 9.99, format: "Kindle", rate: "70%", units: 98, revenue: 979, royalty: 685 },
  { book: "Keto Guide", price: 14.99, format: "Print", rate: "60%", units: 32, revenue: 480, royalty: 168 },
  { book: "Keto Guide", format: "KU", units: 0, revenue: 0, royalty: 216 },
  { book: "Startup Playbook", price: 12.99, format: "Kindle", rate: "70%", units: 45, revenue: 585, royalty: 409 },
  { book: "Marketing Authors", price: 4.99, format: "Kindle", rate: "70%", units: 64, revenue: 319, royalty: 224 },
];

const MOCK_TIPS = [
  {
    type: "warning" as const,
    text: "'Marketing for Authors' at $4.99 earns $3.49/sale (70%). If priced at $2.98, royalty drops to $1.04/sale (35%). Always price above $2.99 for Kindle unless running a promo.",
  },
  {
    type: "info" as const,
    text: "Print royalties are lower because of print costs. Current print cost for Keto Guide: $3.85 (250 pages, 6x9). Royalty = ($14.99 x 60%) - $3.85 = $5.14 per copy.",
  },
];

interface RoyaltyBreakdownProps {
  currentPrice?: number;
}

export function RoyaltyBreakdown({ currentPrice = 4.99 }: RoyaltyBreakdownProps) {
  const [period, setPeriod] = useState("30d");

  // Fetch royalty analysis from API
  const { data: analysisData } = useRoyaltyAnalysis(period);

  // Build table rows from API data or fall back to mock
  const royaltyRows = useMemo<RoyaltyRow[]>(() => {
    if (analysisData?.rows && analysisData.rows.length > 0) {
      return analysisData.rows.map((row) => ({
        book: row.book_title,
        price: row.price,
        format: row.format,
        rate: `${Math.round(row.royalty_rate * 100)}%`,
        units: row.units,
        revenue: row.revenue,
        royalty: row.royalty,
      }));
    }
    return MOCK_ROYALTY_DATA;
  }, [analysisData]);

  // Totals
  const totalRevenue = royaltyRows.reduce((sum, r) => sum + r.revenue, 0);
  const totalRoyalty = royaltyRows.reduce((sum, r) => sum + r.royalty, 0);
  const effectiveRate =
    analysisData?.effective_rate ??
    (totalRevenue > 0 ? Math.round((totalRoyalty / totalRevenue) * 100) : 0);

  // Optimization tips from API or mock
  const tips = useMemo(() => {
    if (analysisData?.optimization_tips && analysisData.optimization_tips.length > 0) {
      return analysisData.optimization_tips.map((tip, idx) => ({
        type: idx === 0 ? ("warning" as const) : ("info" as const),
        text: tip,
      }));
    }
    return MOCK_TIPS;
  }, [analysisData]);

  // --- Existing bar chart data ---
  const pricePoints = [
    0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 10.99, 11.99, 12.99,
  ];

  const getRoyaltyRate = (price: number): number => {
    if (price >= 2.99 && price <= 9.99) return 0.7;
    return 0.35;
  };

  const barData = pricePoints.map((price) => {
    const royaltyRate = getRoyaltyRate(price);
    const royaltyPerSale = price * royaltyRate;
    const estimatedSales = calculateEstimatedSales(price);
    const monthlyRoyalty = royaltyPerSale * estimatedSales * 30;

    return {
      price: `$${price.toFixed(2)}`,
      priceValue: price,
      royaltyRate: royaltyRate * 100,
      royaltyPerSale,
      estimatedMonthlySales: estimatedSales,
      monthlyRoyalty,
      isCurrent: Math.abs(price - currentPrice) < 0.01,
    };
  });

  return (
    <div className="space-y-6">
      {/* Header with Period Selector */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Royalty Analysis</h3>
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="90d">Last 90 Days</SelectItem>
              <SelectItem value="ytd">Year to Date</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Royalty Analysis Table */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Book</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead>Format</TableHead>
              <TableHead className="text-right">Royalty Rate</TableHead>
              <TableHead className="text-right">Units</TableHead>
              <TableHead className="text-right">Revenue</TableHead>
              <TableHead className="text-right">Royalty</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {royaltyRows.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-medium">{row.book}</TableCell>
                <TableCell className="text-right">
                  {row.price != null ? `$${row.price.toFixed(2)}` : "--"}
                </TableCell>
                <TableCell>{row.format}</TableCell>
                <TableCell className="text-right">{row.rate ?? "--"}</TableCell>
                <TableCell className="text-right">{row.units.toLocaleString()}</TableCell>
                <TableCell className="text-right">${row.revenue.toLocaleString()}</TableCell>
                <TableCell className="text-right font-medium">
                  ${row.royalty.toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell colSpan={5} className="font-semibold">
                Total
              </TableCell>
              <TableCell className="text-right font-semibold">
                ${totalRevenue.toLocaleString()}
              </TableCell>
              <TableCell className="text-right font-semibold">
                ${totalRoyalty.toLocaleString()}
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>

        <p className="mt-3 text-sm text-muted-foreground">
          Effective royalty rate: <span className="font-semibold">{effectiveRate}%</span>
        </p>
      </Card>

      {/* Royalty Optimization Tips */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Optimization Tips</h3>
        <div className="space-y-4">
          {tips.map((tip, idx) => (
            <div
              key={idx}
              className={`flex gap-3 p-4 rounded-lg ${
                tip.type === "warning"
                  ? "bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800"
                  : "bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800"
              }`}
            >
              {tip.type === "warning" ? (
                <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              ) : (
                <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              )}
              <p className="text-sm leading-relaxed">{tip.text}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Existing Royalty by Price Point Chart */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-6">Royalty Breakdown by Price Point</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="price" tick={{ fontSize: 12 }} />
            <YAxis
              tick={{ fontSize: 12 }}
              label={{ value: "Monthly Royalty ($)", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-background border rounded-lg shadow-lg p-3">
                    <p className="font-medium mb-1">{d.price}</p>
                    <p className="text-sm">
                      Royalty Rate: <span className="font-medium">{d.royaltyRate}%</span>
                    </p>
                    <p className="text-sm">
                      Per Sale: <span className="font-medium">${d.royaltyPerSale.toFixed(2)}</span>
                    </p>
                    <p className="text-sm">
                      Est. Sales: <span className="font-medium">{d.estimatedMonthlySales}/month</span>
                    </p>
                    <p className="text-sm font-medium mt-1">
                      Monthly: ${d.monthlyRoyalty.toFixed(2)}
                    </p>
                  </div>
                );
              }}
            />
            <Legend />
            <Bar dataKey="monthlyRoyalty" name="Estimated Monthly Royalty ($)" radius={[4, 4, 0, 0]}>
              {barData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isCurrent ? "#2563eb" : entry.royaltyRate === 70 ? "#16a34a" : "#94a3b8"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Royalty Tiers Info */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">70% Royalty Tier</h4>
              <span className="text-2xl font-bold text-green-600">70%</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Price range: <span className="font-medium">$2.99 - $9.99</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Maximum royalty rate for ebooks priced within this range
            </p>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">35% Royalty Tier</h4>
              <span className="text-2xl font-bold text-slate-600">35%</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Price range: <span className="font-medium">$0.99 - $2.98, $10.00+</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Lower royalty rate for books priced outside the 70% tier
            </p>
          </div>
        </div>

        {/* Sweet Spot Recommendation */}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
          <h4 className="font-medium mb-2">Sweet Spot Analysis</h4>
          <p className="text-sm">
            Based on typical price elasticity, the $2.99 - $4.99 range often maximizes total royalties by
            balancing higher royalty rates (70%) with stronger sales volume. The highlighted bar shows your
            current price point.
          </p>
        </div>
      </Card>
    </div>
  );
}

// Simple demand curve estimation (preserved from original)
function calculateEstimatedSales(price: number): number {
  const basePrice = 2.99;
  const baseSales = 100;
  const elasticity = -1.5;

  const priceChange = (price - basePrice) / basePrice;
  const salesChange = elasticity * priceChange;
  const newSales = baseSales * (1 + salesChange);

  return Math.max(Math.round(newSales), 5);
}
