"use client";

import { useTranslations } from "@/hooks/use-translations";
import type { CompetitorBookBrief } from "@/modules/competitors/hooks";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Eye, Trash2, Star, TrendingUp, TrendingDown } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format a number as compact currency (e.g. $1,234). */
function formatCurrency(amount: number): string {
  return `$${Math.round(amount).toLocaleString()}`;
}

/** Format a date string to a readable short date. */
function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CompetitorCardProps {
  competitor: CompetitorBookBrief;
  onViewDetails: (id: string) => void;
  onRemove: (id: string) => void;
}

export function CompetitorCard({
  competitor,
  onViewDetails,
  onRemove,
}: CompetitorCardProps) {
  const t = useTranslations("competitors");

  const bsrImproving =
    competitor.bsr_change != null && competitor.bsr_change < 0;
  const bsrDeclining =
    competitor.bsr_change != null && competitor.bsr_change > 0;

  return (
    <Card className="flex flex-col overflow-hidden">
      <CardContent className="flex gap-4 p-4 flex-1">
        {/* Cover thumbnail */}
        {competitor.image_url ? (
          <img
            src={competitor.image_url}
            alt={competitor.title}
            className="h-28 w-20 flex-shrink-0 rounded object-cover"
          />
        ) : (
          <div className="flex h-28 w-20 flex-shrink-0 items-center justify-center rounded bg-muted text-xs text-muted-foreground">
            No Cover
          </div>
        )}

        {/* Details */}
        <div className="flex flex-1 flex-col gap-1.5 min-w-0">
          {/* Title + author */}
          <h3 className="text-sm font-semibold leading-snug line-clamp-2">
            {competitor.title}
          </h3>
          {competitor.author && (
            <p className="text-xs text-muted-foreground truncate">
              {t("card.by")} {competitor.author}
            </p>
          )}

          {/* BSR + trend */}
          {competitor.bsr != null && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="font-medium">
                {t("card.bsr")}: #{competitor.bsr.toLocaleString()}
              </span>
              {bsrImproving && (
                <span className="inline-flex items-center gap-0.5 text-green-600">
                  <TrendingUp className="h-3 w-3" />
                  {Math.abs(competitor.bsr_change!).toLocaleString()}
                </span>
              )}
              {bsrDeclining && (
                <span className="inline-flex items-center gap-0.5 text-red-600">
                  <TrendingDown className="h-3 w-3" />
                  {Math.abs(competitor.bsr_change!).toLocaleString()}
                </span>
              )}
            </div>
          )}

          {/* Reviews + rating */}
          {(competitor.review_count != null || competitor.rating != null) && (
            <div className="flex items-center gap-1.5 text-xs">
              {competitor.review_count != null && (
                <span>
                  {t("card.reviews")}: {competitor.review_count.toLocaleString()}
                </span>
              )}
              {competitor.rating != null && (
                <span className="inline-flex items-center gap-0.5 text-yellow-500">
                  <Star className="h-3 w-3 fill-current" />
                  {competitor.rating.toFixed(1)}
                </span>
              )}
            </div>
          )}

          {/* Price */}
          {competitor.price != null && (
            <p className="text-xs">
              {t("card.price")}: {formatCurrency(competitor.price)}
            </p>
          )}

          {/* Estimated monthly revenue */}
          {competitor.estimated_monthly_revenue != null && (
            <p className="text-xs">
              {t("card.estRevenue")}:{" "}
              {formatCurrency(competitor.estimated_monthly_revenue)}
              <span className="text-muted-foreground">
                {" "}
                {t("card.perMonth")}
              </span>
            </p>
          )}

          {/* Published date */}
          {competitor.publish_date && (
            <p className="text-xs text-muted-foreground">
              {t("card.published")}: {formatDate(competitor.publish_date)}
            </p>
          )}
        </div>
      </CardContent>

      {/* Action buttons */}
      <CardFooter className="flex items-center gap-2 border-t px-4 py-3">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => onViewDetails(competitor.id)}
        >
          <Eye className="mr-1.5 h-3.5 w-3.5" />
          {t("card.viewDetails")}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-destructive hover:text-destructive"
          onClick={() => onRemove(competitor.id)}
        >
          <Trash2 className="mr-1.5 h-3.5 w-3.5" />
          {t("card.remove")}
        </Button>
      </CardFooter>
    </Card>
  );
}
