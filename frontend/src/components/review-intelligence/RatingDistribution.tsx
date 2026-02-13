"use client";

import { Star } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { useTranslations } from "@/hooks/use-translations";

interface RatingDistributionProps {
  distribution: Record<number, number>;
  total: number;
  bookFilter?: string;
}

const BAR_COLORS: Record<number, string> = {
  5: "bg-green-500",
  4: "bg-green-400",
  3: "bg-yellow-400",
  2: "bg-orange-400",
  1: "bg-red-500",
};

const STAR_RATINGS = [5, 4, 3, 2, 1] as const;

export function RatingDistribution({
  distribution,
  total,
}: RatingDistributionProps) {
  const t = useTranslations("reviews");

  // Find the max count for proportional bar width
  const maxCount = Math.max(
    ...STAR_RATINGS.map((star) => distribution[star] ?? 0),
    1
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">
          {t("charts.ratingDistribution")}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {STAR_RATINGS.map((star) => {
            const count = distribution[star] ?? 0;
            const percentage = total > 0 ? (count / total) * 100 : 0;
            const barWidth = maxCount > 0 ? (count / maxCount) * 100 : 0;

            return (
              <div key={star} className="flex items-center gap-3">
                {/* Star label */}
                <div className="flex w-[72px] shrink-0 items-center gap-1">
                  <span className="text-sm font-medium">{star}</span>
                  <div className="flex">
                    {Array.from({ length: star }).map((_, i) => (
                      <Star
                        key={i}
                        className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400"
                      />
                    ))}
                  </div>
                </div>

                {/* Bar */}
                <div className="relative h-5 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className={`absolute inset-y-0 left-0 rounded-full transition-all ${BAR_COLORS[star]}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>

                {/* Count and percentage */}
                <div className="flex w-[80px] shrink-0 items-center justify-end gap-1.5 text-sm">
                  <span className="font-medium tabular-nums">{count}</span>
                  <span className="text-muted-foreground tabular-nums">
                    ({percentage.toFixed(0)}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Total reviews */}
        <div className="mt-4 border-t pt-3">
          <p className="text-sm text-muted-foreground">
            {t("charts.totalReviews")}: <span className="font-medium text-foreground">{total.toLocaleString()}</span>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
