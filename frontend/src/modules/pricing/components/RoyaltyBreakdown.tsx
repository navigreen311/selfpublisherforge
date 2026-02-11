"use client";

import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";

interface RoyaltyBreakdownProps {
  currentPrice?: number;
}

export function RoyaltyBreakdown({ currentPrice = 4.99 }: RoyaltyBreakdownProps) {
  // Generate price points and their royalties
  const pricePoints = [
    0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 10.99, 11.99, 12.99,
  ];

  const getRoyaltyRate = (price: number): number => {
    if (price >= 2.99 && price <= 9.99) return 0.7;
    return 0.35;
  };

  const data = pricePoints.map((price) => {
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
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-6">Royalty Breakdown by Price Point</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="price" tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            label={{ value: "Monthly Royalty ($)", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const data = payload[0].payload;
              return (
                <div className="bg-background border rounded-lg shadow-lg p-3">
                  <p className="font-medium mb-1">{data.price}</p>
                  <p className="text-sm">
                    Royalty Rate: <span className="font-medium">{data.royaltyRate}%</span>
                  </p>
                  <p className="text-sm">
                    Per Sale: <span className="font-medium">${data.royaltyPerSale.toFixed(2)}</span>
                  </p>
                  <p className="text-sm">
                    Est. Sales: <span className="font-medium">{data.estimatedMonthlySales}/month</span>
                  </p>
                  <p className="text-sm font-medium mt-1">
                    Monthly: ${data.monthlyRoyalty.toFixed(2)}
                  </p>
                </div>
              );
            }}
          />
          <Legend />
          <Bar dataKey="monthlyRoyalty" name="Estimated Monthly Royalty ($)" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
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
        <h4 className="font-medium mb-2">💡 Sweet Spot Analysis</h4>
        <p className="text-sm">
          Based on typical price elasticity, the $2.99 - $4.99 range often maximizes total royalties by
          balancing higher royalty rates (70%) with stronger sales volume. The highlighted bar shows your
          current price point.
        </p>
      </div>
    </Card>
  );
}

// Simple demand curve estimation
function calculateEstimatedSales(price: number): number {
  // Base sales at $2.99
  const basePrice = 2.99;
  const baseSales = 100;
  const elasticity = -1.5;

  // Calculate percentage change from base price
  const priceChange = (price - basePrice) / basePrice;

  // Apply elasticity to calculate new sales
  const salesChange = elasticity * priceChange;
  const newSales = baseSales * (1 + salesChange);

  return Math.max(Math.round(newSales), 5);
}
