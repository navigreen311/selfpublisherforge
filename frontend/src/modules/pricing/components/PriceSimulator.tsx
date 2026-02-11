"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useSimulatePrice } from "../hooks";
import type { PriceSimulationResponse } from "../types";

export function PriceSimulator() {
  const [currentPrice, setCurrentPrice] = useState(2.99);
  const [proposedPrice, setProposedPrice] = useState(4.99);
  const [currentSales, setCurrentSales] = useState(10);
  const [elasticity, setElasticity] = useState(-1.5);

  const { mutate: simulatePrice, data, isPending } = useSimulatePrice();

  const handleSimulate = () => {
    simulatePrice({
      current_price: currentPrice,
      proposed_price: proposedPrice,
      current_daily_sales: currentSales,
      elasticity,
    });
  };

  const getRoyaltyRate = (price: number): number => {
    if (price >= 2.99 && price <= 9.99) return 0.7;
    return 0.35;
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
              <span className="text-sm font-medium">${currentPrice.toFixed(2)}</span>
            </div>
            <Slider
              id="current-price"
              min={0.99}
              max={19.99}
              step={0.10}
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
              onChange={(e) => setCurrentPrice(parseFloat(e.target.value) || 0.99)}
              className="mt-2"
            />
            <div className="text-xs text-muted-foreground mt-1">
              Royalty Rate: {(getRoyaltyRate(currentPrice) * 100).toFixed(0)}% = $
              {calculateRoyalty(currentPrice, getRoyaltyRate(currentPrice)).toFixed(2)} per sale
            </div>
          </div>

          {/* Proposed Price */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="proposed-price">Proposed Price</Label>
              <span className="text-sm font-medium">${proposedPrice.toFixed(2)}</span>
            </div>
            <Slider
              id="proposed-price"
              min={0.99}
              max={19.99}
              step={0.10}
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
              onChange={(e) => setProposedPrice(parseFloat(e.target.value) || 0.99)}
              className="mt-2"
            />
            <div className="text-xs text-muted-foreground mt-1">
              Royalty Rate: {(getRoyaltyRate(proposedPrice) * 100).toFixed(0)}% = $
              {calculateRoyalty(proposedPrice, getRoyaltyRate(proposedPrice)).toFixed(2)} per sale
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
              onChange={(e) => setCurrentSales(parseInt(e.target.value) || 1)}
              className="mt-2"
            />
          </div>

          {/* Price Elasticity */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="elasticity">Price Elasticity</Label>
              <span className="text-sm font-medium">{elasticity.toFixed(2)}</span>
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
              How sensitive sales are to price changes (negative value). -1.5 means a 10% price increase
              typically results in 15% fewer sales.
            </p>
          </div>

          <Button onClick={handleSimulate} disabled={isPending} className="w-full">
            {isPending ? "Simulating..." : "Simulate Price Change"}
          </Button>
        </div>
      </Card>

      {data && <SimulationResults data={data} />}
    </div>
  );
}

function SimulationResults({ data }: { data: PriceSimulationResponse }) {
  const revenueChangeColor = data.revenue_change_pct >= 0 ? "text-green-600" : "text-red-600";
  const royaltyChangeColor = data.royalty_change_pct >= 0 ? "text-green-600" : "text-red-600";

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Simulation Results</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Current Metrics */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground">Current Metrics</h4>
          <div className="space-y-2">
            <MetricRow
              label="Price"
              value={`$${data.current_metrics.price.toFixed(2)}`}
            />
            <MetricRow
              label="Royalty Rate"
              value={`${(data.current_metrics.royalty_rate * 100).toFixed(0)}%`}
            />
            <MetricRow
              label="Daily Sales"
              value={`${data.current_metrics.estimated_daily_sales.toFixed(1)} units`}
            />
            <MetricRow
              label="Daily Revenue"
              value={`$${data.current_metrics.estimated_daily_revenue.toFixed(2)}`}
            />
            <MetricRow
              label="Daily Royalties"
              value={`$${data.current_metrics.estimated_daily_royalties.toFixed(2)}`}
            />
            <MetricRow
              label="Monthly Royalties"
              value={`$${data.current_metrics.estimated_monthly_royalties.toFixed(2)}`}
              emphasized
            />
          </div>
        </div>

        {/* Proposed Metrics */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground">Proposed Metrics</h4>
          <div className="space-y-2">
            <MetricRow
              label="Price"
              value={`$${data.proposed_metrics.price.toFixed(2)}`}
            />
            <MetricRow
              label="Royalty Rate"
              value={`${(data.proposed_metrics.royalty_rate * 100).toFixed(0)}%`}
            />
            <MetricRow
              label="Daily Sales"
              value={`${data.proposed_metrics.estimated_daily_sales.toFixed(1)} units`}
            />
            <MetricRow
              label="Daily Revenue"
              value={`$${data.proposed_metrics.estimated_daily_revenue.toFixed(2)}`}
            />
            <MetricRow
              label="Daily Royalties"
              value={`$${data.proposed_metrics.estimated_daily_royalties.toFixed(2)}`}
            />
            <MetricRow
              label="Monthly Royalties"
              value={`$${data.proposed_metrics.estimated_monthly_royalties.toFixed(2)}`}
              emphasized
            />
          </div>
        </div>
      </div>

      {/* Change Summary */}
      <div className="mt-6 pt-6 border-t space-y-2">
        <h4 className="font-medium text-sm text-muted-foreground mb-3">Impact Summary</h4>
        <MetricRow
          label="Price Change"
          value={`${data.price_change_pct >= 0 ? "+" : ""}${data.price_change_pct.toFixed(1)}%`}
        />
        <MetricRow
          label="Revenue Change"
          value={`${data.revenue_change_pct >= 0 ? "+" : ""}${data.revenue_change_pct.toFixed(1)}%`}
          valueClassName={revenueChangeColor}
        />
        <MetricRow
          label="Royalty Change"
          value={`${data.royalty_change_pct >= 0 ? "+" : ""}${data.royalty_change_pct.toFixed(1)}%`}
          valueClassName={royaltyChangeColor}
          emphasized
        />
        <MetricRow
          label="Breakeven Sales"
          value={`${data.breakeven_sales.toFixed(1)} units/day`}
        />
      </div>

      {/* Recommended Price Points */}
      {data.recommended_price_points && data.recommended_price_points.length > 0 && (
        <div className="mt-6 pt-6 border-t">
          <h4 className="font-medium text-sm text-muted-foreground mb-3">
            Recommended Price Points
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.recommended_price_points.map((point, idx) => (
              <Card key={idx} className="p-4 bg-muted/50">
                <div className="text-lg font-bold">${point.price.toFixed(2)}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {(point.royalty_rate * 100).toFixed(0)}% royalty
                </div>
                <div className="text-sm mt-2">
                  ${point.estimated_monthly_royalties.toFixed(0)}/mo
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

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
      <span className={emphasized ? "font-medium" : "text-sm text-muted-foreground"}>
        {label}
      </span>
      <span className={emphasized ? "font-bold" : `text-sm ${valueClassName || ""}`}>
        {value}
      </span>
    </div>
  );
}
