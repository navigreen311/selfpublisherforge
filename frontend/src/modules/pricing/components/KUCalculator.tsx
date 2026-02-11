"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useKUCalculator } from "../hooks";
import type { KUCalculatorResponse } from "../types";

export function KUCalculator() {
  const [pageCount, setPageCount] = useState(300);
  const [kuReadsPerMonth, setKuReadsPerMonth] = useState(100);
  const [kuPageRate, setKuPageRate] = useState(0.0045);
  const [widePrice, setWidePrice] = useState(4.99);
  const [wideMonthlySales, setWideMonthlySales] = useState(50);
  const [wideRoyaltyRate, setWideRoyaltyRate] = useState(0.7);
  const [amazonPrice, setAmazonPrice] = useState(4.99);
  const [amazonMonthlySales, setAmazonMonthlySales] = useState(30);
  const [amazonRoyaltyRate, setAmazonRoyaltyRate] = useState(0.7);

  const { mutate: calculate, data, isPending } = useKUCalculator();

  const handleCalculate = () => {
    calculate({
      book_page_count: pageCount,
      estimated_ku_reads_per_month: kuReadsPerMonth,
      ku_page_rate: kuPageRate,
      wide_price: widePrice,
      wide_monthly_sales: wideMonthlySales,
      wide_royalty_rate: wideRoyaltyRate,
      amazon_price: amazonPrice,
      amazon_monthly_sales: amazonMonthlySales,
      amazon_royalty_rate: amazonRoyaltyRate,
    });
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">KU vs. Wide Calculator</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Compare potential revenue from Kindle Unlimited (KU exclusive) vs. wide distribution across
          multiple platforms.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Book Details */}
          <div className="space-y-4">
            <h3 className="font-medium text-sm">Book Details</h3>
            <div className="space-y-2">
              <Label htmlFor="page-count">KENPC Page Count</Label>
              <Input
                id="page-count"
                type="number"
                min={1}
                value={pageCount}
                onChange={(e) => setPageCount(parseInt(e.target.value) || 1)}
              />
              <p className="text-xs text-muted-foreground">
                Kindle Edition Normalized Page Count (from KDP dashboard)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ku-page-rate">KU Page Rate</Label>
              <Input
                id="ku-page-rate"
                type="number"
                min={0}
                step={0.0001}
                value={kuPageRate}
                onChange={(e) => setKuPageRate(parseFloat(e.target.value) || 0.0045)}
              />
              <p className="text-xs text-muted-foreground">
                Current KENP rate (typically $0.0040 - $0.0050)
              </p>
            </div>
          </div>

          {/* KU Exclusive */}
          <div className="space-y-4">
            <h3 className="font-medium text-sm">KU Exclusive (Amazon Only)</h3>
            <div className="space-y-2">
              <Label htmlFor="ku-reads">Estimated KU Reads/Month</Label>
              <Input
                id="ku-reads"
                type="number"
                min={0}
                value={kuReadsPerMonth}
                onChange={(e) => setKuReadsPerMonth(parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="amazon-price">Amazon Price</Label>
              <Input
                id="amazon-price"
                type="number"
                min={0}
                step={0.01}
                value={amazonPrice}
                onChange={(e) => setAmazonPrice(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="amazon-sales">Amazon Monthly Sales (Paid)</Label>
              <Input
                id="amazon-sales"
                type="number"
                min={0}
                value={amazonMonthlySales}
                onChange={(e) => setAmazonMonthlySales(parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="amazon-royalty">Amazon Royalty Rate</Label>
              <Input
                id="amazon-royalty"
                type="number"
                min={0}
                max={1}
                step={0.01}
                value={amazonRoyaltyRate}
                onChange={(e) => setAmazonRoyaltyRate(parseFloat(e.target.value) || 0.7)}
              />
              <p className="text-xs text-muted-foreground">0.35 for 35% or 0.70 for 70%</p>
            </div>
          </div>

          {/* Wide Distribution */}
          <div className="space-y-4 md:col-span-2">
            <h3 className="font-medium text-sm">Wide Distribution</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="wide-price">Wide Price</Label>
                <Input
                  id="wide-price"
                  type="number"
                  min={0}
                  step={0.01}
                  value={widePrice}
                  onChange={(e) => setWidePrice(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="wide-sales">Wide Monthly Sales</Label>
                <Input
                  id="wide-sales"
                  type="number"
                  min={0}
                  value={wideMonthlySales}
                  onChange={(e) => setWideMonthlySales(parseInt(e.target.value) || 0)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="wide-royalty">Wide Royalty Rate</Label>
                <Input
                  id="wide-royalty"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={wideRoyaltyRate}
                  onChange={(e) => setWideRoyaltyRate(parseFloat(e.target.value) || 0.7)}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Combined sales from Apple Books, Kobo, Google Play, Barnes & Noble, etc.
            </p>
          </div>
        </div>

        <Button onClick={handleCalculate} disabled={isPending} className="w-full mt-6">
          {isPending ? "Calculating..." : "Calculate Revenue"}
        </Button>
      </Card>

      {data && <KUCalculatorResults data={data} />}
    </div>
  );
}

function KUCalculatorResults({ data }: { data: KUCalculatorResponse }) {
  const monthlyDiff = data.difference_monthly;
  const annualDiff = data.difference_annual;
  const diffColor = monthlyDiff >= 0 ? "text-green-600" : "text-red-600";

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Revenue Comparison</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* KU Exclusive */}
        <div className="space-y-3 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
          <h4 className="font-medium">KU Exclusive (Amazon Only)</h4>
          <div className="space-y-2">
            <RevenueRow
              label="Monthly Revenue"
              value={`$${data.ku_exclusive.monthly_revenue.toFixed(2)}`}
            />
            <RevenueRow
              label="Monthly Royalties"
              value={`$${data.ku_exclusive.monthly_royalties.toFixed(2)}`}
              emphasized
            />
            <RevenueRow
              label="Annual Revenue"
              value={`$${data.ku_exclusive.annual_revenue.toFixed(2)}`}
            />
            <RevenueRow
              label="Annual Royalties"
              value={`$${data.ku_exclusive.annual_royalties.toFixed(2)}`}
              emphasized
            />
          </div>
        </div>

        {/* Wide Distribution */}
        <div className="space-y-3 p-4 bg-purple-50 dark:bg-purple-950 rounded-lg">
          <h4 className="font-medium">Wide Distribution</h4>
          <div className="space-y-2">
            <RevenueRow
              label="Monthly Revenue"
              value={`$${data.wide_distribution.monthly_revenue.toFixed(2)}`}
            />
            <RevenueRow
              label="Monthly Royalties"
              value={`$${data.wide_distribution.monthly_royalties.toFixed(2)}`}
              emphasized
            />
            <RevenueRow
              label="Annual Revenue"
              value={`$${data.wide_distribution.annual_revenue.toFixed(2)}`}
            />
            <RevenueRow
              label="Annual Royalties"
              value={`$${data.wide_distribution.annual_royalties.toFixed(2)}`}
              emphasized
            />
          </div>
        </div>
      </div>

      {/* Difference Summary */}
      <div className="p-4 bg-muted rounded-lg space-y-2">
        <h4 className="font-medium mb-3">Net Difference</h4>
        <RevenueRow
          label="Monthly Difference"
          value={`${monthlyDiff >= 0 ? "+" : ""}$${Math.abs(monthlyDiff).toFixed(2)}`}
          valueClassName={diffColor}
          emphasized
        />
        <RevenueRow
          label="Annual Difference"
          value={`${annualDiff >= 0 ? "+" : ""}$${Math.abs(annualDiff).toFixed(2)}`}
          valueClassName={diffColor}
          emphasized
        />
      </div>

      {/* Recommendation */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
        <h4 className="font-medium mb-2">Recommendation</h4>
        <p className="text-sm">{data.recommendation}</p>
      </div>

      {/* Additional Details */}
      {data.details && Object.keys(data.details).length > 0 && (
        <div className="mt-6">
          <h4 className="font-medium text-sm text-muted-foreground mb-2">Additional Details</h4>
          <div className="text-xs text-muted-foreground space-y-1">
            {Object.entries(data.details).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

function RevenueRow({
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
