"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from "@/components/ui/table";
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

  // Monthly KU Earnings Estimator inputs
  const [estimatedMonthlyFullReads, setEstimatedMonthlyFullReads] = useState(100);
  const [averagePercentRead, setAveragePercentRead] = useState(75);

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

      {data && (
        <KUCalculatorResults
          data={data}
          pageCount={pageCount}
          kuPageRate={kuPageRate}
          amazonPrice={amazonPrice}
          amazonRoyaltyRate={amazonRoyaltyRate}
          amazonMonthlySales={amazonMonthlySales}
          kuReadsPerMonth={kuReadsPerMonth}
          widePrice={widePrice}
          wideRoyaltyRate={wideRoyaltyRate}
          wideMonthlySales={wideMonthlySales}
          estimatedMonthlyFullReads={estimatedMonthlyFullReads}
          setEstimatedMonthlyFullReads={setEstimatedMonthlyFullReads}
          averagePercentRead={averagePercentRead}
          setAveragePercentRead={setAveragePercentRead}
        />
      )}
    </div>
  );
}

interface KUCalculatorResultsProps {
  data: KUCalculatorResponse;
  pageCount: number;
  kuPageRate: number;
  amazonPrice: number;
  amazonRoyaltyRate: number;
  amazonMonthlySales: number;
  kuReadsPerMonth: number;
  widePrice: number;
  wideRoyaltyRate: number;
  wideMonthlySales: number;
  estimatedMonthlyFullReads: number;
  setEstimatedMonthlyFullReads: (v: number) => void;
  averagePercentRead: number;
  setAveragePercentRead: (v: number) => void;
}

function KUCalculatorResults({
  data,
  pageCount,
  kuPageRate,
  amazonPrice,
  amazonRoyaltyRate,
  amazonMonthlySales,
  kuReadsPerMonth,
  widePrice,
  wideRoyaltyRate,
  wideMonthlySales,
  estimatedMonthlyFullReads,
  setEstimatedMonthlyFullReads,
  averagePercentRead,
  setAveragePercentRead,
}: KUCalculatorResultsProps) {
  const monthlyDiff = data.difference_monthly;
  const annualDiff = data.difference_annual;

  // --- Derived calculations ---
  const perFullReadEarning = pageCount * kuPageRate;
  const paidRoyaltyPerSale = amazonPrice * amazonRoyaltyRate;
  const breakeven = paidRoyaltyPerSale > 0 ? paidRoyaltyPerSale / perFullReadEarning : 0;

  // Monthly KU Earnings Estimator
  const effectivePages = pageCount * (averagePercentRead / 100);
  const estimatedKUMonthlyEarnings = estimatedMonthlyFullReads * effectivePages * kuPageRate;
  const estimatedKUExclusiveMonthly =
    estimatedKUMonthlyEarnings + amazonMonthlySales * paidRoyaltyPerSale;
  const estimatedWideMonthly = wideMonthlySales * widePrice * wideRoyaltyRate;

  // Recommendation logic
  const kuExclusiveMonthly = data.ku_exclusive.monthly_royalties;
  const wideMonthly = data.wide_distribution.monthly_royalties;
  const marginPercent =
    wideMonthly > 0 ? Math.abs(kuExclusiveMonthly - wideMonthly) / wideMonthly : 0;
  const isClose = marginPercent < 0.15;
  const kuWins = kuExclusiveMonthly > wideMonthly;

  const monthlyAdvantage = Math.abs(kuExclusiveMonthly - wideMonthly);
  const annualAdvantage = monthlyAdvantage * 12;

  // Detailed breakdown rows
  const kuPageReadsRevenue = kuReadsPerMonth * pageCount * kuPageRate;
  const amazonPaidRevenue = amazonMonthlySales * paidRoyaltyPerSale;
  const kuExclusiveTotalMonthly = kuPageReadsRevenue + amazonPaidRevenue;
  const wideTotalMonthly = wideMonthlySales * widePrice * wideRoyaltyRate;

  return (
    <div className="space-y-6">
      {/* 1. Per-Read Earnings Box */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Per-Read Earnings</h3>
        <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
          <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
            If 100% of KENP read:
          </p>
          <p className="text-lg font-bold text-blue-800 dark:text-blue-200 mt-1">
            {pageCount.toLocaleString()} pages x ${kuPageRate.toFixed(4)} = $
            {perFullReadEarning.toFixed(2)} per full read
          </p>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
            Each time a KU subscriber reads your entire book, you earn $
            {perFullReadEarning.toFixed(2)} based on the current KENP rate.
          </p>
        </div>
      </Card>

      {/* 2. Comparison Card */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Purchase vs. KU Read Comparison</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
            <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Kindle Purchase (${amazonPrice.toFixed(2)})
            </h4>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              ${paidRoyaltyPerSale.toFixed(2)}
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              Royalty at {(amazonRoyaltyRate * 100).toFixed(0)}% rate
            </p>
          </div>
          <div className="p-4 bg-purple-50 dark:bg-purple-950 rounded-lg border border-purple-200 dark:border-purple-800">
            <h4 className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">
              Full KU Read
            </h4>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              ${perFullReadEarning.toFixed(2)}
            </p>
            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              {pageCount.toLocaleString()} pages at ${kuPageRate.toFixed(4)}/page
            </p>
          </div>
        </div>

        <div className="p-4 bg-amber-50 dark:bg-amber-950 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex items-start gap-3">
            <BreakevenIcon />
            <div>
              <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">
                Breakeven: Need{" "}
                <span className="text-amber-700 dark:text-amber-300 text-base">
                  {breakeven.toFixed(1)}
                </span>{" "}
                KU reads to equal 1 paid sale
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                If your KU read rate is above {breakeven.toFixed(1)} reads per sale equivalent, KU
                is earning you more per reader than paid purchases alone.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* 3. Monthly KU Earnings Estimator */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Monthly KU Earnings Estimator</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Adjust estimated reads and average completion rate to project monthly KU earnings.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-2">
            <Label htmlFor="est-monthly-reads">Estimated Monthly Full Reads</Label>
            <Input
              id="est-monthly-reads"
              type="number"
              min={0}
              value={estimatedMonthlyFullReads}
              onChange={(e) => setEstimatedMonthlyFullReads(parseInt(e.target.value) || 0)}
            />
          </div>

          <div className="space-y-3">
            <Label>Average % Read: {averagePercentRead}%</Label>
            <Slider
              value={[averagePercentRead]}
              onValueChange={(v) => setAveragePercentRead(v[0])}
              min={0}
              max={100}
              step={1}
            />
            <p className="text-xs text-muted-foreground">
              How much of the book readers typically finish
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">
              KU Exclusive Monthly
            </h4>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              ${estimatedKUExclusiveMonthly.toFixed(2)}
            </p>
            <div className="mt-2 space-y-1 text-xs text-blue-600 dark:text-blue-400">
              <p>KU page reads: ${estimatedKUMonthlyEarnings.toFixed(2)}</p>
              <p>
                Amazon paid sales ({amazonMonthlySales}): ${(amazonMonthlySales * paidRoyaltyPerSale).toFixed(2)}
              </p>
            </div>
          </div>
          <div className="p-4 bg-purple-50 dark:bg-purple-950 rounded-lg">
            <h4 className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-1">
              Wide Distribution Monthly
            </h4>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              ${estimatedWideMonthly.toFixed(2)}
            </p>
            <div className="mt-2 space-y-1 text-xs text-purple-600 dark:text-purple-400">
              <p>
                {wideMonthlySales} sales x ${widePrice.toFixed(2)} x{" "}
                {(wideRoyaltyRate * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* 4. AI/Smart Recommendation */}
      <SmartRecommendation
        kuWins={kuWins}
        isClose={isClose}
        monthlyAdvantage={monthlyAdvantage}
        annualAdvantage={annualAdvantage}
        kuExclusiveMonthly={kuExclusiveMonthly}
        wideMonthly={wideMonthly}
        pageCount={pageCount}
        amazonPrice={amazonPrice}
        widePrice={widePrice}
        recommendation={data.recommendation}
      />

      {/* 5. Detailed Breakdown Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Detailed Breakdown</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Revenue Source</TableHead>
              <TableHead className="text-right">Monthly</TableHead>
              <TableHead className="text-right">Annual</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {/* KU Exclusive section */}
            <TableRow className="bg-blue-50/50 dark:bg-blue-950/50">
              <TableCell colSpan={3} className="font-semibold text-blue-800 dark:text-blue-200">
                KU Exclusive (Amazon Only)
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell className="pl-8 text-muted-foreground">KU Page Reads Revenue</TableCell>
              <TableCell className="text-right">${kuPageReadsRevenue.toFixed(2)}</TableCell>
              <TableCell className="text-right">${(kuPageReadsRevenue * 12).toFixed(2)}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell className="pl-8 text-muted-foreground">
                Amazon Paid Sales Royalties
              </TableCell>
              <TableCell className="text-right">${amazonPaidRevenue.toFixed(2)}</TableCell>
              <TableCell className="text-right">${(amazonPaidRevenue * 12).toFixed(2)}</TableCell>
            </TableRow>
            <TableRow className="font-semibold">
              <TableCell className="pl-8">Total KU Exclusive</TableCell>
              <TableCell className="text-right text-blue-700 dark:text-blue-300">
                ${kuExclusiveTotalMonthly.toFixed(2)}
              </TableCell>
              <TableCell className="text-right text-blue-700 dark:text-blue-300">
                ${(kuExclusiveTotalMonthly * 12).toFixed(2)}
              </TableCell>
            </TableRow>

            {/* Wide Distribution section */}
            <TableRow className="bg-purple-50/50 dark:bg-purple-950/50">
              <TableCell colSpan={3} className="font-semibold text-purple-800 dark:text-purple-200">
                Wide Distribution
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell className="pl-8 text-muted-foreground">
                Multi-Platform Sales Royalties
              </TableCell>
              <TableCell className="text-right">${wideTotalMonthly.toFixed(2)}</TableCell>
              <TableCell className="text-right">${(wideTotalMonthly * 12).toFixed(2)}</TableCell>
            </TableRow>
            <TableRow className="font-semibold">
              <TableCell className="pl-8">Total Wide Distribution</TableCell>
              <TableCell className="text-right text-purple-700 dark:text-purple-300">
                ${wideTotalMonthly.toFixed(2)}
              </TableCell>
              <TableCell className="text-right text-purple-700 dark:text-purple-300">
                ${(wideTotalMonthly * 12).toFixed(2)}
              </TableCell>
            </TableRow>
          </TableBody>
          <TableFooter>
            <TableRow className="font-bold">
              <TableCell>Difference (KU - Wide)</TableCell>
              <TableCell
                className={`text-right ${
                  kuExclusiveTotalMonthly - wideTotalMonthly >= 0
                    ? "text-green-700 dark:text-green-400"
                    : "text-red-700 dark:text-red-400"
                }`}
              >
                {kuExclusiveTotalMonthly - wideTotalMonthly >= 0 ? "+" : "-"}$
                {Math.abs(kuExclusiveTotalMonthly - wideTotalMonthly).toFixed(2)}
              </TableCell>
              <TableCell
                className={`text-right ${
                  kuExclusiveTotalMonthly - wideTotalMonthly >= 0
                    ? "text-green-700 dark:text-green-400"
                    : "text-red-700 dark:text-red-400"
                }`}
              >
                {kuExclusiveTotalMonthly - wideTotalMonthly >= 0 ? "+" : "-"}$
                {Math.abs((kuExclusiveTotalMonthly - wideTotalMonthly) * 12).toFixed(2)}
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </Card>

      {/* Existing Revenue Comparison (KU vs Wide side-by-side from API) */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">API Revenue Comparison</h3>

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
            valueClassName={monthlyDiff >= 0 ? "text-green-600" : "text-red-600"}
            emphasized
          />
          <RevenueRow
            label="Annual Difference"
            value={`${annualDiff >= 0 ? "+" : ""}$${Math.abs(annualDiff).toFixed(2)}`}
            valueClassName={annualDiff >= 0 ? "text-green-600" : "text-red-600"}
            emphasized
          />
        </div>
      </Card>

      {/* Additional Details */}
      {data.details && Object.keys(data.details).length > 0 && (
        <Card className="p-6">
          <h4 className="font-medium text-sm text-muted-foreground mb-2">Additional Details</h4>
          <div className="text-xs text-muted-foreground space-y-1">
            {Object.entries(data.details).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// --- Smart Recommendation Component ---

function SmartRecommendation({
  kuWins,
  isClose,
  monthlyAdvantage,
  annualAdvantage,
  kuExclusiveMonthly,
  wideMonthly,
  pageCount,
  amazonPrice,
  widePrice,
  recommendation,
}: {
  kuWins: boolean;
  isClose: boolean;
  monthlyAdvantage: number;
  annualAdvantage: number;
  kuExclusiveMonthly: number;
  wideMonthly: number;
  pageCount: number;
  amazonPrice: number;
  widePrice: number;
  recommendation: string;
}) {
  const winnerLabel = kuWins ? "KU Exclusive" : "Wide Distribution";

  const getRecommendationLevel = (): {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    iconColor: string;
  } => {
    if (isClose) {
      return {
        label: "Consider other factors (margins are close)",
        color: "text-amber-900 dark:text-amber-100",
        bgColor: "bg-amber-50 dark:bg-amber-950",
        borderColor: "border-amber-200 dark:border-amber-800",
        iconColor: "text-amber-600 dark:text-amber-400",
      };
    }
    return {
      label: kuWins ? "Stay in KU" : "Go Wide",
      color: "text-green-900 dark:text-green-100",
      bgColor: "bg-green-50 dark:bg-green-950",
      borderColor: "border-green-200 dark:border-green-800",
      iconColor: "text-green-600 dark:text-green-400",
    };
  };

  const rec = getRecommendationLevel();

  const getExplanation = (): string => {
    if (isClose) {
      return "The difference between KU and Wide distribution is less than 15%. Consider factors like audience reach, exclusivity trade-offs, genre trends, and long-term catalog strategy before deciding.";
    }
    if (kuWins) {
      const reasons: string[] = [];
      if (pageCount > 250)
        reasons.push("your book has a high page count which maximizes KENP earnings");
      if (amazonPrice < 5)
        reasons.push("your lower price point means KU reads can outperform paid royalties");
      reasons.push("KU-exclusive titles often receive better Amazon algorithm visibility");
      return `KU Exclusive earns more because ${reasons.join(", ")}. Many popular genres (Romance, Thriller, LitRPG, Sci-Fi) perform especially well in KU.`;
    }
    const reasons: string[] = [];
    if (widePrice > 5)
      reasons.push("your higher price point generates stronger per-sale royalties");
    if (wideMonthly > kuExclusiveMonthly * 1.3)
      reasons.push("your wide sales volume significantly outpaces KU revenue");
    reasons.push("wide distribution builds a diversified reader base across platforms");
    return `Wide Distribution earns more because ${reasons.join(", ")}. Genres like non-fiction, literary fiction, and established series often do well across multiple retailers.`;
  };

  return (
    <Card className={`p-6 border-2 ${rec.borderColor} ${rec.bgColor}`}>
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${rec.iconColor}`}>
          <RecommendationIcon />
        </div>
        <div className="flex-1 space-y-3">
          <div>
            <h3 className={`text-lg font-semibold ${rec.color}`}>Smart Recommendation</h3>
            <p className={`text-sm font-medium mt-1 ${rec.color}`}>
              Based on your inputs,{" "}
              <span className="font-bold">{winnerLabel}</span> earns{" "}
              <span className="font-bold">${monthlyAdvantage.toFixed(2)}</span> more per month (
              <span className="font-bold">${annualAdvantage.toFixed(2)}</span> annually).
            </p>
          </div>

          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-semibold text-sm ${
            isClose
              ? "bg-amber-200/60 dark:bg-amber-800/40 text-amber-800 dark:text-amber-200"
              : "bg-green-200/60 dark:bg-green-800/40 text-green-800 dark:text-green-200"
          }`}>
            <CheckIcon />
            Recommendation: {rec.label}
          </div>

          <p className={`text-sm ${rec.color} opacity-80`}>{getExplanation()}</p>

          {recommendation && (
            <div className={`text-xs ${rec.color} opacity-60 mt-2 pt-2 border-t ${rec.borderColor}`}>
              <span className="font-medium">Server analysis:</span> {recommendation}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

// --- Helper Components ---

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

// --- SVG Icon Components ---

function BreakevenIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12h8" />
      <path d="M12 8v8" />
    </svg>
  );
}

function RecommendationIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-6 w-6 shrink-0"
    >
      <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z" />
      <path d="M9 21h6" />
      <path d="M10 21v1a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
