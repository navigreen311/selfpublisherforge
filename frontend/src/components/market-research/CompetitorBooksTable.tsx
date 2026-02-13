"use client";

import { Fragment, useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import type { CompetitorSummary } from "@/modules/market/hooks";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CompetitorBooksTableProps {
  books: CompetitorSummary[];
  onTrack?: (asin: string) => void;
  onAnalyze?: (asin: string) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE = 20;

type SortField =
  | "bsr"
  | "reviews_count"
  | "rating"
  | "price"
  | "estimated_revenue"
  | "title";

type SortDirection = "asc" | "desc";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function bsrTrendArrow(trend?: "up" | "down" | "stable") {
  switch (trend) {
    case "up":
      return <span className="text-green-600 ml-1" aria-label="trending up">{"\u2191"}</span>;
    case "down":
      return <span className="text-red-600 ml-1" aria-label="trending down">{"\u2193"}</span>;
    case "stable":
      return <span className="text-gray-500 ml-1" aria-label="stable">{"\u2192"}</span>;
    default:
      return null;
  }
}

function formatRevenue(value?: number | null): string {
  if (value == null) return "--";
  return `$${value.toLocaleString()}`;
}

function formatBsr(value: number | null): string {
  if (value == null) return "--";
  return value.toLocaleString();
}

function formatPrice(value: number | null): string {
  if (value == null) return "--";
  return `$${value.toFixed(2)}`;
}

function formatRating(value: number | null): string {
  if (value == null) return "--";
  return value.toFixed(1);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SortableHeader({
  label,
  field,
  currentField,
  currentDirection,
  onSort,
  className,
}: {
  label: string;
  field: SortField;
  currentField: SortField;
  currentDirection: SortDirection;
  onSort: (field: SortField) => void;
  className?: string;
}) {
  const isActive = currentField === field;
  return (
    <th
      className={cn(
        "px-4 py-3 font-medium cursor-pointer select-none hover:bg-muted/70 transition-colors",
        className,
      )}
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {isActive && (
          <span className="text-xs">
            {currentDirection === "asc" ? "\u25B2" : "\u25BC"}
          </span>
        )}
      </span>
    </th>
  );
}

function ExpandedRow({ book, t }: { book: CompetitorSummary; t: (key: string) => string }) {
  return (
    <tr className="bg-muted/20">
      <td colSpan={8} className="px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {book.description && (
            <div className="md:col-span-2">
              <span className="font-medium text-muted-foreground">Description:</span>
              <p className="mt-1 text-foreground line-clamp-4">{book.description}</p>
            </div>
          )}
          {book.categories && book.categories.length > 0 && (
            <div>
              <span className="font-medium text-muted-foreground">Categories:</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {book.categories.map((cat) => (
                  <span
                    key={cat}
                    className="bg-muted px-2 py-0.5 rounded text-xs text-foreground"
                  >
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          )}
          {book.keywords && book.keywords.length > 0 && (
            <div>
              <span className="font-medium text-muted-foreground">Keywords:</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {book.keywords.map((kw) => (
                  <span
                    key={kw}
                    className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
          {book.page_count != null && (
            <div>
              <span className="font-medium text-muted-foreground">Pages:</span>{" "}
              <span>{book.page_count}</span>
            </div>
          )}
          {book.publish_date && (
            <div>
              <span className="font-medium text-muted-foreground">Published:</span>{" "}
              <span>{book.publish_date}</span>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CompetitorBooksTable({
  books,
  onTrack,
  onAnalyze,
}: CompetitorBooksTableProps) {
  const t = useTranslations("market");

  // ---- State ----
  const [sortField, setSortField] = useState<SortField>("bsr");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [currentPage, setCurrentPage] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [selectedAsins, setSelectedAsins] = useState<Set<string>>(new Set());

  // ---- Sorting ----
  const handleSort = useCallback(
    (field: SortField) => {
      if (field === sortField) {
        setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setSortField(field);
        setSortDirection("asc");
      }
      setCurrentPage(0);
    },
    [sortField],
  );

  const sortedBooks = useMemo(() => {
    const sorted = [...books].sort((a, b) => {
      let aVal: number | string | null = null;
      let bVal: number | string | null = null;

      switch (sortField) {
        case "bsr":
          aVal = a.bsr;
          bVal = b.bsr;
          break;
        case "reviews_count":
          aVal = a.reviews_count;
          bVal = b.reviews_count;
          break;
        case "rating":
          aVal = a.rating;
          bVal = b.rating;
          break;
        case "price":
          aVal = a.price;
          bVal = b.price;
          break;
        case "estimated_revenue":
          aVal = a.estimated_revenue ?? null;
          bVal = b.estimated_revenue ?? null;
          break;
        case "title":
          aVal = a.title.toLowerCase();
          bVal = b.title.toLowerCase();
          break;
      }

      // Null values always sort to the end
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      let cmp: number;
      if (typeof aVal === "string" && typeof bVal === "string") {
        cmp = aVal.localeCompare(bVal);
      } else {
        cmp = (aVal as number) - (bVal as number);
      }

      return sortDirection === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [books, sortField, sortDirection]);

  // ---- Pagination ----
  const totalPages = Math.ceil(sortedBooks.length / PAGE_SIZE);
  const pageStart = currentPage * PAGE_SIZE;
  const pageEnd = Math.min(pageStart + PAGE_SIZE, sortedBooks.length);
  const pageBooks = sortedBooks.slice(pageStart, pageEnd);

  // ---- Row expansion ----
  const toggleExpand = useCallback((asin: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(asin)) {
        next.delete(asin);
      } else {
        next.add(asin);
      }
      return next;
    });
  }, []);

  // ---- Bulk selection ----
  const toggleSelect = useCallback((asin: string) => {
    setSelectedAsins((prev) => {
      const next = new Set(prev);
      if (next.has(asin)) {
        next.delete(asin);
      } else {
        next.add(asin);
      }
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelectedAsins((prev) => {
      const allPageAsins = pageBooks.map((b) => b.asin);
      const allSelected = allPageAsins.every((a) => prev.has(a));
      const next = new Set(prev);
      if (allSelected) {
        allPageAsins.forEach((a) => next.delete(a));
      } else {
        allPageAsins.forEach((a) => next.add(a));
      }
      return next;
    });
  }, [pageBooks]);

  const handleTrackSelected = useCallback(() => {
    if (!onTrack) return;
    selectedAsins.forEach((asin) => onTrack(asin));
    setSelectedAsins(new Set());
  }, [onTrack, selectedAsins]);

  const allPageSelected =
    pageBooks.length > 0 && pageBooks.every((b) => selectedAsins.has(b.asin));

  // ---- Render ----
  if (!books.length) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        No competing books found.
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b bg-muted/30">
        <h3 className="text-base font-semibold">
          {t("results.topBooks")} ({books.length} {t("results.found")})
        </h3>
        <div className="flex items-center gap-2">
          {selectedAsins.size > 0 && onTrack && (
            <button
              type="button"
              onClick={handleTrackSelected}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              {t("results.trackSelected")} ({selectedAsins.size})
            </button>
          )}
          <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
            {t("results.sort")}:
            <select
              className="text-xs border rounded px-2 py-1 bg-background text-foreground"
              value={sortField}
              onChange={(e) => {
                setSortField(e.target.value as SortField);
                setCurrentPage(0);
              }}
            >
              <option value="bsr">{t("results.bsr")}</option>
              <option value="reviews_count">{t("results.reviewCount")}</option>
              <option value="rating">Rating</option>
              <option value="price">{t("results.price")}</option>
              <option value="estimated_revenue">{t("results.estRev")}</option>
              <option value="title">{t("results.bookTitle")}</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() =>
              setSortDirection((d) => (d === "asc" ? "desc" : "asc"))
            }
            className="px-2 py-1 text-xs border rounded hover:bg-muted transition-colors"
            aria-label={t("results.filter")}
          >
            {sortDirection === "asc" ? "\u25B2" : "\u25BC"}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-3 py-3 w-10">
                <input
                  type="checkbox"
                  checked={allPageSelected}
                  onChange={toggleSelectAll}
                  className="rounded border-gray-300"
                  aria-label="Select all"
                />
              </th>
              <th className="px-4 py-3 font-medium text-left w-10">
                {t("results.rank")}
              </th>
              <SortableHeader
                label={t("results.bookTitle")}
                field="title"
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={handleSort}
                className="text-left"
              />
              <SortableHeader
                label={t("results.bsr")}
                field="bsr"
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={handleSort}
                className="text-right"
              />
              <SortableHeader
                label={t("results.reviewCount")}
                field="reviews_count"
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={handleSort}
                className="text-right"
              />
              <SortableHeader
                label={t("results.price")}
                field="price"
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={handleSort}
                className="text-right"
              />
              <SortableHeader
                label={t("results.estRev")}
                field="estimated_revenue"
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={handleSort}
                className="text-right"
              />
              <th className="px-4 py-3 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {pageBooks.map((book, idx) => {
              const rank = pageStart + idx + 1;
              const isExpanded = expandedRows.has(book.asin);
              const isSelected = selectedAsins.has(book.asin);

              return (
                <Fragment key={book.asin}>
                  <tr
                    className={cn(
                      "border-b last:border-b-0 hover:bg-muted/30 transition-colors cursor-pointer",
                      isSelected && "bg-primary/5",
                      isExpanded && "bg-muted/20",
                    )}
                    onClick={() => toggleExpand(book.asin)}
                    title={isExpanded ? t("results.collapseRow") : t("results.expandRow")}
                  >
                    {/* Checkbox */}
                    <td
                      className="px-3 py-3"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(book.asin)}
                        className="rounded border-gray-300"
                        aria-label={`Select ${book.title}`}
                      />
                    </td>

                    {/* Rank */}
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                      {rank}
                    </td>

                    {/* Title + Author + Rating + Image */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {book.image_url && (
                          <img
                            src={book.image_url}
                            alt={book.title}
                            className="w-10 h-14 object-cover rounded-sm flex-shrink-0"
                            loading="lazy"
                          />
                        )}
                        <div className="min-w-0">
                          <div className="font-medium text-foreground truncate max-w-xs">
                            {book.title}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">
                            {book.author}
                          </div>
                          {book.rating != null && (
                            <div className="flex items-center gap-1 mt-0.5">
                              <span className="text-yellow-500 text-xs">
                                {"\u2605"}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatRating(book.rating)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* BSR + trend */}
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <span>{formatBsr(book.bsr)}</span>
                      {bsrTrendArrow(book.bsr_trend)}
                    </td>

                    {/* Reviews + rating */}
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <span>{book.reviews_count.toLocaleString()}</span>
                      {book.rating != null && (
                        <span className="text-xs text-muted-foreground ml-1">
                          ({formatRating(book.rating)})
                        </span>
                      )}
                    </td>

                    {/* Price */}
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {formatPrice(book.price)}
                    </td>

                    {/* Est Revenue */}
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <span>{formatRevenue(book.estimated_revenue)}</span>
                      {book.estimated_revenue != null && (
                        <span className="text-xs text-muted-foreground">
                          /{t("results.perMonth")}
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td
                      className="px-4 py-3 text-center"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="flex items-center justify-center gap-1">
                        {onTrack && (
                          <button
                            type="button"
                            onClick={() => onTrack(book.asin)}
                            className="px-2 py-1 text-xs font-medium rounded border border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
                          >
                            {t("results.track")}
                          </button>
                        )}
                        {onAnalyze && (
                          <button
                            type="button"
                            onClick={() => onAnalyze(book.asin)}
                            className="px-2 py-1 text-xs font-medium rounded border border-muted-foreground/30 text-muted-foreground hover:bg-muted transition-colors"
                          >
                            {t("results.analyze")}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>

                  {/* Expanded detail row */}
                  {isExpanded && <ExpandedRow book={book} t={t} />}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t bg-muted/20 text-sm">
          <span className="text-muted-foreground">
            {t("results.showing")} {pageStart + 1}-{pageEnd} of{" "}
            {sortedBooks.length}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={currentPage === 0}
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded border transition-colors",
                currentPage === 0
                  ? "opacity-50 cursor-not-allowed border-muted text-muted-foreground"
                  : "border-border hover:bg-muted text-foreground",
              )}
            >
              {t("results.previous")}
            </button>
            <span className="text-xs text-muted-foreground">
              {currentPage + 1} / {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages - 1}
              onClick={() =>
                setCurrentPage((p) => Math.min(totalPages - 1, p + 1))
              }
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded border transition-colors",
                currentPage >= totalPages - 1
                  ? "opacity-50 cursor-not-allowed border-muted text-muted-foreground"
                  : "border-border hover:bg-muted text-foreground",
              )}
            >
              {t("results.next")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
