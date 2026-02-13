"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { useTranslations } from "@/hooks/use-translations";
import type { ChartsData, CompetitorSummary } from "@/modules/market/hooks";

interface MarketChartsProps {
  chartsData?: ChartsData;
  books?: CompetitorSummary[];
}

// ---------------------------------------------------------------------------
// Helpers to compute chart data from books when chartsData is not provided
// ---------------------------------------------------------------------------

function computeBsrDistribution(
  books: CompetitorSummary[]
): { range: string; count: number }[] {
  const buckets = [
    { range: "< 1K", max: 1000 },
    { range: "1K-10K", max: 10000 },
    { range: "10K-50K", max: 50000 },
    { range: "50K-100K", max: 100000 },
    { range: "> 100K", max: Infinity },
  ];

  const counts = buckets.map((b) => ({ range: b.range, count: 0 }));

  for (const book of books) {
    const bsr = book.bsr;
    if (bsr == null) continue;
    if (bsr < 1000) counts[0].count++;
    else if (bsr < 10000) counts[1].count++;
    else if (bsr < 50000) counts[2].count++;
    else if (bsr < 100000) counts[3].count++;
    else counts[4].count++;
  }

  return counts;
}

function computePriceDistribution(
  books: CompetitorSummary[]
): { range: string; count: number }[] {
  const buckets = [
    { range: "< $5", max: 5 },
    { range: "$5-$10", max: 10 },
    { range: "$10-$15", max: 15 },
    { range: "$15-$20", max: 20 },
    { range: "> $20", max: Infinity },
  ];

  const counts = buckets.map((b) => ({ range: b.range, count: 0 }));

  for (const book of books) {
    const price = book.price;
    if (price == null) continue;
    if (price < 5) counts[0].count++;
    else if (price < 10) counts[1].count++;
    else if (price < 15) counts[2].count++;
    else if (price < 20) counts[3].count++;
    else counts[4].count++;
  }

  return counts;
}

function computeReviewDistribution(
  books: CompetitorSummary[]
): { range: string; count: number }[] {
  const buckets = [
    { range: "0-100", max: 100 },
    { range: "100-500", max: 500 },
    { range: "500-1K", max: 1000 },
    { range: "1K-5K", max: 5000 },
    { range: "> 5K", max: Infinity },
  ];

  const counts = buckets.map((b) => ({ range: b.range, count: 0 }));

  for (const book of books) {
    const reviews = book.reviews_count;
    if (reviews < 100) counts[0].count++;
    else if (reviews < 500) counts[1].count++;
    else if (reviews < 1000) counts[2].count++;
    else if (reviews < 5000) counts[3].count++;
    else counts[4].count++;
  }

  return counts;
}

function computeChartsData(books: CompetitorSummary[]): ChartsData {
  return {
    bsr_distribution: computeBsrDistribution(books),
    price_distribution: computePriceDistribution(books),
    review_distribution: computeReviewDistribution(books),
  };
}

// ---------------------------------------------------------------------------
// Footer summary helpers
// ---------------------------------------------------------------------------

function getBsrFooter(data: { range: string; count: number }[]): string {
  // Find the range with the most books
  let maxCount = 0;
  let maxRange = "";
  for (const d of data) {
    if (d.count > maxCount) {
      maxCount = d.count;
      maxRange = d.range;
    }
  }
  return maxRange;
}

function getPriceSweetSpot(data: { range: string; count: number }[]): string {
  let maxCount = 0;
  let maxRange = "";
  for (const d of data) {
    if (d.count > maxCount) {
      maxCount = d.count;
      maxRange = d.range;
    }
  }
  return maxRange;
}

function getAvgReviews(data: { range: string; count: number }[]): string {
  // Estimate an average review count from distribution buckets
  const midpoints = [50, 300, 750, 3000, 7500];
  let total = 0;
  let count = 0;
  for (let i = 0; i < data.length; i++) {
    total += midpoints[i] * data[i].count;
    count += data[i].count;
  }
  if (count === 0) return "0";
  const avg = Math.round(total / count);
  return avg.toLocaleString();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function MarketCharts({ chartsData, books }: MarketChartsProps) {
  const t = useTranslations("market");

  const data: ChartsData | null =
    chartsData ?? (books && books.length > 0 ? computeChartsData(books) : null);

  if (!data) {
    return null;
  }

  const bsrFooterValue = getBsrFooter(data.bsr_distribution);
  const priceSweetSpot = getPriceSweetSpot(data.price_distribution);
  const avgReviews = getAvgReviews(data.review_distribution);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* BSR Distribution */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {t("charts.bsrDistribution")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.bsr_distribution}>
              <XAxis
                dataKey="range"
                tick={{ fontSize: 11 }}
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            {t("charts.bsrDesc", { value: bsrFooterValue })}
          </p>
        </CardFooter>
      </Card>

      {/* Price Distribution */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {t("charts.priceDistribution")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.price_distribution}>
              <XAxis
                dataKey="range"
                tick={{ fontSize: 11 }}
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            {t("charts.priceDesc", { range: priceSweetSpot })}
          </p>
        </CardFooter>
      </Card>

      {/* Review Barrier */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {t("charts.reviewBarrier")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.review_distribution}>
              <XAxis
                dataKey="range"
                tick={{ fontSize: 11 }}
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            {t("charts.reviewDesc", { count: avgReviews })}
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
