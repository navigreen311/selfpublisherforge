"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import type { CompetitorBookBrief } from "@/modules/competitors/hooks";
import { CompetitorCard } from "./CompetitorCard";
import { Button } from "@/components/ui/button";
import {
  LayoutGrid,
  List,
  ArrowUpDown,
  Filter,
  Star,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type SortOption = "bsr" | "reviews" | "price" | "revenue" | "date_added";

interface CompetitorGridProps {
  competitors: CompetitorBookBrief[];
  onViewDetails: (id: string) => void;
  onRemove: (id: string) => void;
  view: "grid" | "table";
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: number): string {
  return `$${Math.round(amount).toLocaleString()}`;
}

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

function sortCompetitors(
  list: CompetitorBookBrief[],
  sortBy: SortOption,
): CompetitorBookBrief[] {
  const sorted = [...list];
  sorted.sort((a, b) => {
    switch (sortBy) {
      case "bsr":
        return (a.bsr ?? Infinity) - (b.bsr ?? Infinity);
      case "reviews":
        return (b.review_count ?? 0) - (a.review_count ?? 0);
      case "price":
        return (a.price ?? 0) - (b.price ?? 0);
      case "revenue":
        return (
          (b.estimated_monthly_revenue ?? 0) -
          (a.estimated_monthly_revenue ?? 0)
        );
      case "date_added":
        return (
          new Date(b.publish_date ?? 0).getTime() -
          new Date(a.publish_date ?? 0).getTime()
        );
      default:
        return 0;
    }
  });
  return sorted;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** A single row in the table view. */
function TableRow({
  competitor,
  onViewDetails,
  onRemove,
  t,
}: {
  competitor: CompetitorBookBrief;
  onViewDetails: (id: string) => void;
  onRemove: (id: string) => void;
  t: ReturnType<typeof useTranslations>;
}) {
  const bsrImproving =
    competitor.bsr_change != null && competitor.bsr_change < 0;
  const bsrDeclining =
    competitor.bsr_change != null && competitor.bsr_change > 0;

  return (
    <tr className="border-b last:border-b-0 hover:bg-muted/50 transition-colors">
      {/* Cover + title */}
      <td className="px-3 py-2">
        <div className="flex items-center gap-3">
          {competitor.image_url ? (
            <img
              src={competitor.image_url}
              alt={competitor.title}
              className="h-12 w-8 rounded object-cover flex-shrink-0"
            />
          ) : (
            <div className="flex h-12 w-8 items-center justify-center rounded bg-muted text-[10px] text-muted-foreground flex-shrink-0">
              --
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium leading-snug line-clamp-1">
              {competitor.title}
            </p>
            {competitor.author && (
              <p className="text-xs text-muted-foreground truncate">
                {competitor.author}
              </p>
            )}
          </div>
        </div>
      </td>

      {/* BSR */}
      <td className="px-3 py-2 text-sm whitespace-nowrap">
        {competitor.bsr != null ? (
          <div className="flex items-center gap-1">
            <span>#{competitor.bsr.toLocaleString()}</span>
            {bsrImproving && (
              <span className="inline-flex items-center gap-0.5 text-green-600 text-xs">
                <TrendingUp className="h-3 w-3" />
                {Math.abs(competitor.bsr_change!).toLocaleString()}
              </span>
            )}
            {bsrDeclining && (
              <span className="inline-flex items-center gap-0.5 text-red-600 text-xs">
                <TrendingDown className="h-3 w-3" />
                {Math.abs(competitor.bsr_change!).toLocaleString()}
              </span>
            )}
          </div>
        ) : (
          "--"
        )}
      </td>

      {/* Reviews + rating */}
      <td className="px-3 py-2 text-sm whitespace-nowrap">
        {competitor.review_count != null
          ? competitor.review_count.toLocaleString()
          : "--"}
        {competitor.rating != null && (
          <span className="ml-1.5 inline-flex items-center gap-0.5 text-yellow-500 text-xs">
            <Star className="h-3 w-3 fill-current" />
            {competitor.rating.toFixed(1)}
          </span>
        )}
      </td>

      {/* Price */}
      <td className="px-3 py-2 text-sm whitespace-nowrap">
        {competitor.price != null ? formatCurrency(competitor.price) : "--"}
      </td>

      {/* Revenue */}
      <td className="px-3 py-2 text-sm whitespace-nowrap">
        {competitor.estimated_monthly_revenue != null
          ? formatCurrency(competitor.estimated_monthly_revenue)
          : "--"}
      </td>

      {/* Published */}
      <td className="px-3 py-2 text-sm text-muted-foreground whitespace-nowrap">
        {competitor.publish_date ? formatDate(competitor.publish_date) : "--"}
      </td>

      {/* Actions */}
      <td className="px-3 py-2 text-right whitespace-nowrap">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetails(competitor.id)}
        >
          {t("card.viewDetails")}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-destructive hover:text-destructive"
          onClick={() => onRemove(competitor.id)}
        >
          {t("card.remove")}
        </Button>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CompetitorGrid({
  competitors,
  onViewDetails,
  onRemove,
  view: initialView,
}: CompetitorGridProps) {
  const t = useTranslations("competitors");
  const [currentView, setCurrentView] = useState<"grid" | "table">(
    initialView,
  );
  const [sortBy, setSortBy] = useState<SortOption>("bsr");
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  const sorted = sortCompetitors(competitors, sortBy);

  const sortOptions: { key: SortOption; label: string }[] = [
    { key: "bsr", label: t("tracked.sortBsr") },
    { key: "reviews", label: t("tracked.sortReviews") },
    { key: "price", label: t("tracked.sortPrice") },
    { key: "revenue", label: t("tracked.sortRevenue") },
    { key: "date_added", label: t("tracked.sortDateAdded") },
  ];

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        {/* Title */}
        <h2 className="text-lg font-semibold">
          {t("tracked.title")}{" "}
          <span className="text-muted-foreground font-normal">
            ({t("tracked.count", { count: competitors.length })})
          </span>
        </h2>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center rounded-md border">
            <Button
              variant={currentView === "grid" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-r-none"
              onClick={() => setCurrentView("grid")}
              aria-label={t("tracked.viewGrid")}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={currentView === "table" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-l-none"
              onClick={() => setCurrentView("table")}
              aria-label={t("tracked.viewTable")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>

          {/* Sort dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowSortMenu((prev) => !prev);
                setShowFilterMenu(false);
              }}
            >
              <ArrowUpDown className="mr-1.5 h-4 w-4" />
              {t("tracked.sort")}
            </Button>
            {showSortMenu && (
              <div className="absolute right-0 z-10 mt-1 w-44 rounded-md border bg-popover p-1 shadow-md">
                {sortOptions.map((opt) => (
                  <button
                    key={opt.key}
                    className={`w-full rounded px-3 py-1.5 text-left text-sm transition-colors hover:bg-accent ${
                      sortBy === opt.key
                        ? "bg-accent font-medium"
                        : ""
                    }`}
                    onClick={() => {
                      setSortBy(opt.key);
                      setShowSortMenu(false);
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Filter button */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowFilterMenu((prev) => !prev);
                setShowSortMenu(false);
              }}
            >
              <Filter className="mr-1.5 h-4 w-4" />
              {t("tracked.filter")}
            </Button>
            {showFilterMenu && (
              <div className="absolute right-0 z-10 mt-1 w-52 rounded-md border bg-popover p-3 shadow-md">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  {t("tracked.filterByProject")}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("tracked.filterByCategory")}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Empty state */}
      {competitors.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <p className="text-sm text-muted-foreground">
            {t("tracked.noCompetitors")}
          </p>
        </div>
      )}

      {/* Grid view */}
      {competitors.length > 0 && currentView === "grid" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sorted.map((c) => (
            <CompetitorCard
              key={c.id}
              competitor={c}
              onViewDetails={onViewDetails}
              onRemove={onRemove}
            />
          ))}
        </div>
      )}

      {/* Table view */}
      {competitors.length > 0 && currentView === "table" && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-left">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("tracked.title")}
                </th>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("card.bsr")}
                </th>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("card.reviews")}
                </th>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("card.price")}
                </th>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("card.estRevenue")}
                </th>
                <th className="px-3 py-2 text-xs font-medium text-muted-foreground">
                  {t("card.published")}
                </th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((c) => (
                <TableRow
                  key={c.id}
                  competitor={c}
                  onViewDetails={onViewDetails}
                  onRemove={onRemove}
                  t={t}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
