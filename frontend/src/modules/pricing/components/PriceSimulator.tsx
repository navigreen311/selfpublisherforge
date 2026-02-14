"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceDot,
} from "recharts";
import { useSimulatePrice, useEnhancedSimulation } from "../hooks";
import type { PriceSimulationResponse, RevenueCurvePoint } from "../types";

// --------------- Revenue Curve Helpers ---------------

const PRICE_POINTS = [
  0.99, 1.49, 1.99, 2.49, 2.99, 3.49, 3.99, 4.49, 4.99, 5.99, 6.99, 7.99,
  8.99, 9.99,
];

function getRoyaltyRate(price: number): number {
  return price >= 2.99 && price <= 9.99 ? 0.7 : 0.35;
}

function buildRevenueCurve(
  currentPrice: number,
  currentDailySales: number,
  elasticity: number
): RevenueCurvePoint[] {
  return PRICE_POINTS.map((price) => {
    const royaltyRate = getRoyaltyRate(price);
    const estimatedSales =
      currentDailySales *
      (1 + elasticity * ((price - currentPrice) / currentPrice));
    const safeSales = Math.max(0, estimatedSales);
    const dailyRevenue = price * safeSales;
    const dailyRoyalty = price * royaltyRate * safeSales;
    return {
      price,
      daily_revenue: parseFloat(dailyRevenue.toFixed(2)),
      daily_royalty: parseFloat(dailyRoyalty.toFixed(2)),
      monthly_royalty: parseFloat((dailyRoyalty * 30).toFixed(2)),
    };
  });
}

function findOptimalPoint(curve: RevenueCurvePoint[]): RevenueCurvePoint {
  return curve.reduce((best, pt) =>
    pt.daily_royalty > best.daily_royalty ? pt : best
  );
}

function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function formatDollar(value: number): string {
  return `$${value.toFixed(2)}`;
}

function formatDollarWhole(value: number): string {
  return `$${Math.round(value).toLocaleString()}`;
}

// --------------- Simulation Results Shape ---------------

interface SimulationResults {
  data: PriceSimulationResponse;
  currentPrice: number;
  proposedPrice: number;
  currentSales: number;
  elasticity: number;
  revenueCurve: RevenueCurvePoint[];
  optimalPoint: RevenueCurvePoint;
}

// --------------- Main Component ---------------

export function PriceSimulator() {
  const [currentPrice, setCurrentPrice] = useState(2.99);
  const [proposedPrice, setProposedPrice] = useState(4.99);
  const [currentSales, setCurrentSales] = useState(10);
  const [elasticity, setElasticity] = useState(-1.5);
  const [simulationResults, setSimulationResults] =
    useState<SimulationResults | null>(null);

  const { mutate: simulatePrice, isPending } = useSimulatePrice();
  const { mutate: enhancedSimulate } = useEnhancedSimulation();

  const handleSimulate = () => {
    const request = {
      current_price: currentPrice,
      proposed_price: proposedPrice,
      current_daily_sales: currentSales,
      elasticity,
    };

    // Try enhanced simulation first, fall back to basic
    enhancedSimulate(request, {
      onSuccess: (enhanced) => {
        const curve =
          enhanced.revenue_curve && enhanced.revenue_curve.length > 0
            ? enhanced.revenue_curve
            : buildRevenueCurve(currentPrice, currentSales, elasticity);
        const optimal = findOptimalPoint(curve);
        setSimulationResults({
          data: enhanced,
          currentPrice,
          proposedPrice,
          currentSales,
          elasticity,
          revenueCurve: curve,
          optimalPoint: optimal,
        });
      },
      onError: () => {
        // Fall back to basic simulation
        simulatePrice(request, {
          onSuccess: (data) => {
            const curve = buildRevenueCurve(
              currentPrice,
              currentSales,
              elasticity
            );
            const optimal = findOptimalPoint(curve);
            setSimulationResults({
              data,
              currentPrice,
              proposedPrice,
              currentSales,
              elasticity,
              revenueCurve: curve,
              optimalPoint: optimal,
            });
          },
        });
      },
    });
  };

  const handleReset = () => {
    setSimulationResults(null);
  };

  const handleApplyPrice = (price: number) => {
    setCurrentPrice(price);
    setProposedPrice(price);
    setSimulationResults(null);
  };

  const calculateRoyalty = (price: number, rate: number): number => {
    return price * rate;
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Price Simulator</h2>

        <div className="space-y-6">
          {/* Current Price */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="current-price">Current Price</Label>
              <span className="text-sm font-medium">
                ${currentPrice.toFixed(2)}
              </span>
            </div>
            <Slider
              id="current-price"
              min={0.99}
              max={19.99}
              step={0.1}
              value={[currentPrice]}
              onValueChange={(value) => setCurrentPrice(value[0])}
              className="w-full"
            />
            <Input
              type="number"
              min={0.99}
              max={19.99}
              step={0.01}
              value={currentPrice}
              onChange={(e) =>
                setCurrentPrice(parseFloat(e.target.value) || 0.99)
              }
              className="mt-2"
            />
            <div className="text-xs text-muted-foreground mt-1">
              Royalty Rate: {(getRoyaltyRate(currentPrice) * 100).toFixed(0)}% =
              $
              {calculateRoyalty(
                currentPrice,
                getRoyaltyRate(currentPrice)
              ).toFixed(2)}{" "}
              per sale
            </div>
          </div>

          {/* Proposed Price */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="proposed-price">Proposed Price</Label>
              <span className="text-sm font-medium">
                ${proposedPrice.toFixed(2)}
              </span>
            </div>
            <Slider
              id="proposed-price"
              min={0.99}
              max={19.99}
              step={0.1}
              value={[proposedPrice]}
              onValueChange={(value) => setProposedPrice(value[0])}
              className="w-full"
            />
            <Input
              type="number"
              min={0.99}
              max={19.99}
              step={0.01}
              value={proposedPrice}
              onChange={(e) =>
                setProposedPrice(parseFloat(e.target.value) || 0.99)
              }
              className="mt-2"
            />
            <div className="text-xs text-muted-foreground mt-1">
              Royalty Rate:{" "}
              {(getRoyaltyRate(proposedPrice) * 100).toFixed(0)}% = $
              {calculateRoyalty(
                proposedPrice,
                getRoyaltyRate(proposedPrice)
              ).toFixed(2)}{" "}
              per sale
            </div>
          </div>

          {/* Current Daily Sales */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="current-sales">Current Daily Sales</Label>
              <span className="text-sm font-medium">{currentSales} units</span>
            </div>
            <Slider
              id="current-sales"
              min={1}
              max={500}
              step={1}
              value={[currentSales]}
              onValueChange={(value) => setCurrentSales(value[0])}
              className="w-full"
            />
            <Input
              type="number"
              min={1}
              max={10000}
              step={1}
              value={currentSales}
              onChange={(e) =>
                setCurrentSales(parseInt(e.target.value) || 1)
              }
              className="mt-2"
            />
          </div>

          {/* Price Elasticity */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="elasticity">Price Elasticity</Label>
              <span className="text-sm font-medium">
                {elasticity.toFixed(2)}
              </span>
            </div>
            <Slider
              id="elasticity"
              min={-3}
              max={-0.5}
              step={0.1}
              value={[elasticity]}
              onValueChange={(value) => setElasticity(value[0])}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              How sensitive sales are to price changes (negative value). -1.5
              means a 10% price increase typically results in 15% fewer sales.
            </p>
          </div>

          <Button
            onClick={handleSimulate}
            disabled={isPending}
            className="w-full"
          >
            {isPending ? "Simulating..." : "Simulate Price Change"}
          </Button>
        </div>
      </Card>

      {simulationResults && (
        <EnhancedSimulationResults
          results={simulationResults}
          onReset={handleReset}
          onApplyPrice={handleApplyPrice}
        />
      )}
    </div>
  );
}

// --------------- Enhanced Results Section ---------------

function EnhancedSimulationResults({
  results,
  onReset,
  onApplyPrice,
}: {
  results: SimulationResults;
  onReset: () => void;
  onApplyPrice: (price: number) => void;
}) {
  const { data, currentPrice, proposedPrice, elasticity, revenueCurve, optimalPoint } =
    results;

  const current = data.current_metrics;
  const proposed = data.proposed_metrics;

  // Determine how the current price relates to the optimal
  const priceRelation = useMemo(() => {
    const diff = Math.abs(currentPrice - optimalPoint.price);
    if (diff <= 0.5) return "close to optimal";
    if (currentPrice < optimalPoint.price) return "below optimal";
    return "above optimal";
  }, [currentPrice, optimalPoint.price]);

  return (
    <div className="space-y-6">
      {/* Scenario Header */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold">
          Scenario: {formatDollar(currentPrice)} &rarr;{" "}
          {formatDollar(proposedPrice)}{" "}
          <span className="text-muted-foreground font-normal text-base">
            (Price Elasticity: {elasticity.toFixed(2)})
          </span>
        </h3>
      </Card>

      {/* Comparison Table */}
      <ComparisonTable current={current} proposed={proposed} />

      {/* Revenue Curve Chart */}
      <RevenueCurveChart
        curve={revenueCurve}
        currentPrice={currentPrice}
        proposedPrice={proposedPrice}
        optimalPrice={optimalPoint.price}
      />

      {/* AI Recommendation */}
      <AIRecommendationBox
        elasticity={elasticity}
        optimalPoint={optimalPoint}
        currentPrice={currentPrice}
        priceRelation={priceRelation}
        onApplyPrice={onApplyPrice}
        onReset={onReset}
      />
    </div>
  );
}

// --------------- Comparison Table ---------------

interface PriceMetrics {
  price: number;
  royalty_rate: number;
  estimated_daily_sales: number;
  estimated_daily_revenue: number;
  estimated_daily_royalties: number;
  estimated_monthly_royalties: number;
  estimated_monthly_revenue?: number;
}

function ComparisonTable({
  current,
  proposed,
}: {
  current: PriceMetrics;
  proposed: PriceMetrics;
}) {
  const currentMonthlyRev = current.estimated_daily_revenue * 30;
  const proposedMonthlyRev = proposed.estimated_daily_revenue * 30;

  const rows = [
    {
      label: "Daily Sales",
      currentVal: `${current.estimated_daily_sales.toFixed(1)} units`,
      proposedVal: `${proposed.estimated_daily_sales.toFixed(1)} units`,
      changePct:
        current.estimated_daily_sales !== 0
          ? ((proposed.estimated_daily_sales - current.estimated_daily_sales) /
              current.estimated_daily_sales) *
            100
          : 0,
      changeDisplay: "pct" as const,
    },
    {
      label: "Daily Revenue",
      currentVal: formatDollar(current.estimated_daily_revenue),
      proposedVal: formatDollar(proposed.estimated_daily_revenue),
      changePct:
        current.estimated_daily_revenue !== 0
          ? ((proposed.estimated_daily_revenue -
              current.estimated_daily_revenue) /
              current.estimated_daily_revenue) *
            100
          : 0,
      changeDisplay: "pct" as const,
    },
    {
      label: "Daily Royalty",
      currentVal: `${formatDollar(current.estimated_daily_royalties)} (${(current.royalty_rate * 100).toFixed(0)}%)`,
      proposedVal: `${formatDollar(proposed.estimated_daily_royalties)} (${(proposed.royalty_rate * 100).toFixed(0)}%)`,
      changePct:
        current.estimated_daily_royalties !== 0
          ? ((proposed.estimated_daily_royalties -
              current.estimated_daily_royalties) /
              current.estimated_daily_royalties) *
            100
          : 0,
      changeDisplay: "pct" as const,
    },
    {
      label: "Monthly Rev",
      currentVal: formatDollarWhole(currentMonthlyRev),
      proposedVal: formatDollarWhole(proposedMonthlyRev),
      changeDollar: proposedMonthlyRev - currentMonthlyRev,
      changeDisplay: "dollar" as const,
    },
    {
      label: "Monthly Royalty",
      currentVal: formatDollarWhole(current.estimated_monthly_royalties),
      proposedVal: formatDollarWhole(proposed.estimated_monthly_royalties),
      changeDollar:
        proposed.estimated_monthly_royalties -
        current.estimated_monthly_royalties,
      changeDisplay: "dollar" as const,
    },
  ];

  return (
    <Card className="p-6">
      <h4 className="font-semibold text-sm text-muted-foreground mb-4">
        Side-by-Side Comparison
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                Metric
              </th>
              <th className="text-right py-2 px-4 font-medium text-muted-foreground">
                Current ({formatDollar(current.price)})
              </th>
              <th className="text-right py-2 px-4 font-medium text-muted-foreground">
                Proposed ({formatDollar(proposed.price)})
              </th>
              <th className="text-right py-2 pl-4 font-medium text-muted-foreground">
                Change
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isPositive =
                row.changeDisplay === "pct"
                  ? (row.changePct ?? 0) >= 0
                  : (row.changeDollar ?? 0) >= 0;
              const colorClass = isPositive
                ? "text-green-600"
                : "text-red-600";
              const changeText =
                row.changeDisplay === "pct"
                  ? formatPct(row.changePct ?? 0)
                  : `${(row.changeDollar ?? 0) >= 0 ? "+" : ""}$${Math.round(row.changeDollar ?? 0).toLocaleString()}`;
              return (
                <tr key={row.label} className="border-b last:border-0">
                  <td className="py-2 pr-4 font-medium">{row.label}</td>
                  <td className="py-2 px-4 text-right">{row.currentVal}</td>
                  <td className="py-2 px-4 text-right">{row.proposedVal}</td>
                  <td className={`py-2 pl-4 text-right font-semibold ${colorClass}`}>
                    {changeText}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// --------------- Revenue Curve Chart ---------------

function RevenueCurveChart({
  curve,
  currentPrice,
  proposedPrice,
  optimalPrice,
}: {
  curve: RevenueCurvePoint[];
  currentPrice: number;
  proposedPrice: number;
  optimalPrice: number;
}) {
  // Find points for annotation dots
  const currentPoint = curve.reduce((closest, pt) =>
    Math.abs(pt.price - currentPrice) < Math.abs(closest.price - currentPrice)
      ? pt
      : closest
  );
  const proposedPoint = curve.reduce((closest, pt) =>
    Math.abs(pt.price - proposedPrice) <
    Math.abs(closest.price - proposedPrice)
      ? pt
      : closest
  );
  const optimalPointData = curve.reduce((closest, pt) =>
    Math.abs(pt.price - optimalPrice) < Math.abs(closest.price - optimalPrice)
      ? pt
      : closest
  );

  return (
    <Card className="p-6">
      <h4 className="font-semibold mb-1">Revenue Curve</h4>
      <p className="text-xs text-muted-foreground mb-4">
        Estimated daily royalty at each price point based on your elasticity
      </p>

      <ResponsiveContainer width="100%" height={320}>
        <AreaChart
          data={curve}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <defs>
            <linearGradient id="royaltyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="price"
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => `$${v}`}
            label={{
              value: "Price",
              position: "insideBottom",
              offset: -10,
              fontSize: 12,
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => `$${v}`}
            label={{
              value: "Daily Royalty ($)",
              angle: -90,
              position: "insideLeft",
              offset: 0,
              fontSize: 12,
            }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const pt = payload[0].payload as RevenueCurvePoint;
              const rate = getRoyaltyRate(pt.price);
              return (
                <div className="bg-background border rounded-lg shadow-lg p-3 text-sm">
                  <p className="font-semibold">{formatDollar(pt.price)}</p>
                  <p>
                    Royalty Rate:{" "}
                    <span className="font-medium">
                      {(rate * 100).toFixed(0)}%
                    </span>
                  </p>
                  <p>
                    Daily Royalty:{" "}
                    <span className="font-medium">
                      {formatDollar(pt.daily_royalty)}
                    </span>
                  </p>
                  <p>
                    Monthly Royalty:{" "}
                    <span className="font-medium">
                      {formatDollarWhole(pt.monthly_royalty)}
                    </span>
                  </p>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="daily_royalty"
            stroke="#6366f1"
            fill="url(#royaltyGradient)"
            strokeWidth={2.5}
          />

          {/* Current price reference line */}
          <ReferenceLine
            x={currentPoint.price}
            stroke="#2563eb"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `Current $${currentPoint.price}`,
              position: "top",
              fill: "#2563eb",
              fontSize: 11,
            }}
          />

          {/* Proposed price reference line */}
          <ReferenceLine
            x={proposedPoint.price}
            stroke="#f97316"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `Proposed $${proposedPoint.price}`,
              position: "top",
              fill: "#f97316",
              fontSize: 11,
            }}
          />

          {/* Optimal (sweet spot) dot */}
          <ReferenceDot
            x={optimalPointData.price}
            y={optimalPointData.daily_royalty}
            r={6}
            fill="#22c55e"
            stroke="#fff"
            strokeWidth={2}
            label={{
              value: `Sweet Spot $${optimalPointData.price}`,
              position: "top",
              fill: "#22c55e",
              fontSize: 11,
              fontWeight: 600,
            }}
          />

          {/* Current price dot */}
          <ReferenceDot
            x={currentPoint.price}
            y={currentPoint.daily_royalty}
            r={5}
            fill="#2563eb"
            stroke="#fff"
            strokeWidth={2}
          />

          {/* Proposed price dot */}
          <ReferenceDot
            x={proposedPoint.price}
            y={proposedPoint.daily_royalty}
            r={5}
            fill="#f97316"
            stroke="#fff"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mt-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[#2563eb]" />
          <span>Current Price</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[#f97316]" />
          <span>Proposed Price</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
          <span>Sweet Spot (Optimal)</span>
        </div>
      </div>
    </Card>
  );
}

// --------------- AI Recommendation Box ---------------

function AIRecommendationBox({
  elasticity,
  optimalPoint,
  currentPrice,
  priceRelation,
  onApplyPrice,
  onReset,
}: {
  elasticity: number;
  optimalPoint: RevenueCurvePoint;
  currentPrice: number;
  priceRelation: string;
  onApplyPrice: (price: number) => void;
  onReset: () => void;
}) {
  return (
    <Card className="p-6 border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/30">
      <div className="flex items-start gap-3">
        <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-2 mt-0.5 shrink-0">
          <svg
            className="h-5 w-5 text-blue-600 dark:text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z"
            />
          </svg>
        </div>
        <div className="flex-1 space-y-3">
          <h4 className="font-semibold text-blue-900 dark:text-blue-100">
            AI Recommendation
          </h4>
          <p className="text-sm text-blue-800 dark:text-blue-200">
            At your elasticity of{" "}
            <span className="font-semibold">{elasticity.toFixed(2)}</span>, the
            revenue-maximizing price is{" "}
            <span className="font-semibold">
              {formatDollar(optimalPoint.price)}
            </span>{" "}
            (est.{" "}
            <span className="font-semibold">
              {formatDollar(optimalPoint.daily_royalty)}/day
            </span>{" "}
            royalty). Your current {formatDollar(currentPrice)} is{" "}
            <span className="font-semibold">{priceRelation}</span>.
          </p>
          <p className="text-xs text-blue-700 dark:text-blue-300 border-t border-blue-200 dark:border-blue-800 pt-2">
            Price must be $2.99 - $9.99 for the 70% KDP royalty rate. Below
            $2.99 drops to the 35% rate.
          </p>
          <div className="flex flex-wrap gap-3 pt-1">
            <Button
              onClick={() => onApplyPrice(optimalPoint.price)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
            >
              Apply {formatDollar(optimalPoint.price)} Price
            </Button>
            <Button onClick={onReset} variant="outline" size="sm">
              Try Another Scenario
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

// --------------- Metric Row (kept for compatibility) ---------------

function MetricRow({
  label,
  value,
  emphasized = false,
  valueClassName = "",
}: {
  label: string;
  value: string;
  emphasized?: boolean;
  valueClassName?: string;
}) {
  return (
    <div className="flex justify-between items-center">
      <span
        className={
          emphasized ? "font-medium" : "text-sm text-muted-foreground"
        }
      >
        {label}
      </span>
      <span
        className={emphasized ? "font-bold" : `text-sm ${valueClassName || ""}`}
      >
        {value}
      </span>
    </div>
  );
}
