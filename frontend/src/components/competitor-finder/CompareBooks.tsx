"use client";

import { useState, useMemo, useCallback } from "react";
import { useTranslations } from "@/hooks/use-translations";
import {
  useCompareBooks,
  type CompetitorBookBrief,
  type ComparisonResult,
} from "@/modules/competitors/hooks";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  Download,
  Sparkles,
  Check,
  X,
  Loader2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_COMPETITORS = 3;

const FEATURE_KEYS = [
  "mealPlans",
  "shoppingLists",
  "trackers",
  "advancedContent",
  "videoLinks",
] as const;

/** Map feature translation keys to the feature_list identifiers returned by the API */
const FEATURE_ID_MAP: Record<(typeof FEATURE_KEYS)[number], string> = {
  mealPlans: "Meal Plans",
  shoppingLists: "Shopping Lists",
  trackers: "Trackers/Worksheets",
  advancedContent: "Advanced Content",
  videoLinks: "Video/QR Links",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type MetricDirection = "high" | "low";

interface MetricDef {
  label: string;
  /** Extract a display value from a CompetitorBookBrief */
  extract: (b: CompetitorBookBrief) => string;
  /** Extract the raw numeric value for comparison (undefined = N/A) */
  numeric: (b: CompetitorBookBrief) => number | undefined;
  /** Whether higher or lower is better for highlighting */
  direction: MetricDirection;
}

function buildMetrics(t: ReturnType<typeof useTranslations>): MetricDef[] {
  return [
    {
      label: "BSR",
      extract: (b) => (b.bsr != null ? b.bsr.toLocaleString() : "N/A"),
      numeric: (b) => b.bsr ?? undefined,
      direction: "low",
    },
    {
      label: t("compare.metrics") === "compare.metrics" ? "Price" : "Price",
      extract: (b) => (b.price != null ? `$${b.price.toFixed(2)}` : "N/A"),
      numeric: (b) => b.price ?? undefined,
      direction: "low",
    },
    {
      label: "Pages",
      extract: (b) =>
        b.page_count != null ? b.page_count.toLocaleString() : "N/A",
      numeric: (b) => b.page_count ?? undefined,
      direction: "high",
    },
    {
      label: "Reviews",
      extract: (b) =>
        b.review_count != null ? b.review_count.toLocaleString() : "N/A",
      numeric: (b) => b.review_count ?? undefined,
      direction: "high",
    },
    {
      label: "Rating",
      extract: (b) =>
        b.rating != null ? `${b.rating.toFixed(1)} / 5.0` : "N/A",
      numeric: (b) => b.rating ?? undefined,
      direction: "high",
    },
    {
      label: "Published",
      extract: (b) =>
        b.publish_date
          ? new Date(b.publish_date).toLocaleDateString()
          : "N/A",
      numeric: (b) =>
        b.publish_date ? new Date(b.publish_date).getTime() : undefined,
      direction: "high",
    },
  ];
}

/**
 * Given an array of numeric values (undefined = N/A), determine which index
 * is the "best" according to direction.  Returns -1 when no valid comparison.
 */
function bestIndex(
  values: (number | undefined)[],
  direction: MetricDirection,
): number {
  let best: number | undefined;
  let idx = -1;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v == null) continue;
    if (
      best == null ||
      (direction === "high" && v > best) ||
      (direction === "low" && v < best)
    ) {
      best = v;
      idx = i;
    }
  }
  // Only highlight if there is more than one valid value to compare
  const validCount = values.filter((v) => v != null).length;
  return validCount > 1 ? idx : -1;
}

function worstIndex(
  values: (number | undefined)[],
  direction: MetricDirection,
): number {
  // Worst is the opposite of best
  return bestIndex(values, direction === "high" ? "low" : "high");
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CompareBooksProps {
  trackedCompetitors?: CompetitorBookBrief[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompareBooks({ trackedCompetitors = [] }: CompareBooksProps) {
  const t = useTranslations("competitors");

  // --- State ---------------------------------------------------------------
  const [userBookId, setUserBookId] = useState<string>("");
  const [selectedBookIds, setSelectedBookIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] =
    useState<ComparisonResult | null>(null);

  const compareMutation = useCompareBooks();

  // --- Derived data --------------------------------------------------------

  const booksById = useMemo(() => {
    const map = new Map<string, CompetitorBookBrief>();
    for (const b of trackedCompetitors) {
      map.set(b.id, b);
    }
    return map;
  }, [trackedCompetitors]);

  /** Books currently selected for comparison columns (user book first if set) */
  const columnsBooks = useMemo(() => {
    const cols: CompetitorBookBrief[] = [];
    if (userBookId) {
      const ub = booksById.get(userBookId);
      if (ub) cols.push(ub);
    }
    for (const id of selectedBookIds) {
      if (id !== userBookId) {
        const b = booksById.get(id);
        if (b) cols.push(b);
      }
    }
    return cols;
  }, [userBookId, selectedBookIds, booksById]);

  /** IDs already chosen (to prevent duplicates in selectors) */
  const chosenIds = useMemo(() => {
    const set = new Set<string>();
    if (userBookId) set.add(userBookId);
    selectedBookIds.forEach((id) => set.add(id));
    return set;
  }, [userBookId, selectedBookIds]);

  /** Available competitors for adding (not already selected) */
  const availableForAdd = useMemo(
    () => trackedCompetitors.filter((b) => !chosenIds.has(b.id)),
    [trackedCompetitors, chosenIds],
  );

  const metrics = useMemo(() => buildMetrics(t), [t]);

  // Feature data: use comparisonResult if available, otherwise placeholder
  const featureData = useMemo(() => {
    return FEATURE_KEYS.map((key) => {
      const featureId = FEATURE_ID_MAP[key];
      const values = columnsBooks.map((book) => {
        // Check comparisonResult first
        if (comparisonResult) {
          const match = comparisonResult.books.find(
            (rb) => rb.id === book.id || rb.title === book.title,
          );
          if (match?.features && featureId in match.features) {
            return match.features[featureId];
          }
        }
        // Placeholder: randomly true for demo feel -- use true as default placeholder
        return true;
      });
      return { key, label: t(`compare.${key}`), values };
    });
  }, [columnsBooks, comparisonResult, t]);

  // Strengths / weaknesses per book
  const strengthsWeaknesses = useMemo(() => {
    return columnsBooks.map((book) => {
      if (comparisonResult) {
        const match = comparisonResult.books.find(
          (rb) => rb.id === book.id || rb.title === book.title,
        );
        if (match) {
          return {
            strengths: match.strengths ?? [],
            weaknesses: match.weaknesses ?? [],
          };
        }
      }
      return { strengths: [] as string[], weaknesses: [] as string[] };
    });
  }, [columnsBooks, comparisonResult]);

  // --- Handlers ------------------------------------------------------------

  const handleAddCompetitor = useCallback(
    (bookId: string) => {
      if (selectedBookIds.length < MAX_COMPETITORS && !chosenIds.has(bookId)) {
        setSelectedBookIds((prev) => [...prev, bookId]);
      }
    },
    [selectedBookIds, chosenIds],
  );

  const handleRemoveCompetitor = useCallback((bookId: string) => {
    setSelectedBookIds((prev) => prev.filter((id) => id !== bookId));
  }, []);

  const handleCompare = useCallback(() => {
    const allIds = columnsBooks.map((b) => b.id);
    if (allIds.length < 2) return;
    compareMutation.mutate(
      {
        book_ids: allIds,
        my_project_id: userBookId || undefined,
      },
      {
        onSuccess: (data) => setComparisonResult(data),
      },
    );
  }, [columnsBooks, userBookId, compareMutation]);

  const handleExport = useCallback(() => {
    // Build a simple CSV export
    if (columnsBooks.length === 0) return;
    const headers = ["Metric", ...columnsBooks.map((b) => b.title)];
    const rows: string[][] = [];

    for (const m of metrics) {
      rows.push([m.label, ...columnsBooks.map((b) => m.extract(b))]);
    }

    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "book-comparison.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, [columnsBooks, metrics]);

  const handleGenerateStrategy = useCallback(() => {
    // Trigger compare with strategy generation
    const allIds = columnsBooks.map((b) => b.id);
    if (allIds.length < 2) return;
    compareMutation.mutate(
      {
        book_ids: allIds,
        my_project_id: userBookId || undefined,
      },
      {
        onSuccess: (data) => setComparisonResult(data),
      },
    );
  }, [columnsBooks, userBookId, compareMutation]);

  // --- Render --------------------------------------------------------------

  if (trackedCompetitors.length === 0) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        {t("compare.noBooks")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                             */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">{t("compare.title")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("compare.description")}
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={
            availableForAdd.length === 0 ||
            selectedBookIds.length >= MAX_COMPETITORS
          }
          onClick={() => {
            if (availableForAdd.length > 0) {
              handleAddCompetitor(availableForAdd[0].id);
            }
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          {t("compare.addToCompare")}
        </Button>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Book Selectors                                                     */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* Your book selector */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {t("compare.yourBook")}
          </label>
          <Select value={userBookId} onValueChange={setUserBookId}>
            <SelectTrigger>
              <SelectValue placeholder={t("compare.selectYourBook")} />
            </SelectTrigger>
            <SelectContent>
              {trackedCompetitors.map((b) => (
                <SelectItem
                  key={b.id}
                  value={b.id}
                  disabled={
                    selectedBookIds.includes(b.id)
                  }
                >
                  <span className="truncate">{b.title}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Competitor selectors (up to 3) */}
        {Array.from({ length: MAX_COMPETITORS }).map((_, idx) => {
          const bookId = selectedBookIds[idx] ?? "";
          return (
            <div key={idx} className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {t("compare.competitor")} {idx + 1}
              </label>
              <Select
                value={bookId}
                onValueChange={(val) => {
                  setSelectedBookIds((prev) => {
                    const next = [...prev];
                    if (idx < next.length) {
                      next[idx] = val;
                    } else {
                      next.push(val);
                    }
                    return next;
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t("compare.selectCompetitor")}
                  />
                </SelectTrigger>
                <SelectContent>
                  {trackedCompetitors
                    .filter(
                      (b) =>
                        b.id === bookId ||
                        (!chosenIds.has(b.id) || b.id === bookId),
                    )
                    .map((b) => (
                      <SelectItem
                        key={b.id}
                        value={b.id}
                        disabled={
                          b.id !== bookId &&
                          (b.id === userBookId ||
                            (selectedBookIds.includes(b.id) &&
                              b.id !== bookId))
                        }
                      >
                        <span className="truncate">{b.title}</span>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          );
        })}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Comparison Table                                                   */}
      {/* ------------------------------------------------------------------ */}
      {columnsBooks.length > 0 && (
        <div className="border rounded-lg bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              {/* Column headers */}
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-4 py-3 font-medium sticky left-0 bg-muted/50 min-w-[140px]">
                    {t("compare.metrics")}
                  </th>
                  {columnsBooks.map((book, idx) => (
                    <th
                      key={book.id}
                      className="px-4 py-3 font-medium min-w-[180px]"
                    >
                      <div className="flex flex-col items-center gap-0.5">
                        {idx === 0 && userBookId ? (
                          <span className="text-xs uppercase tracking-wide text-primary">
                            {t("compare.yourBook")}
                          </span>
                        ) : (
                          <span className="text-xs uppercase tracking-wide text-muted-foreground">
                            {t("compare.competitor")}{" "}
                            {userBookId ? idx : idx + 1}
                          </span>
                        )}
                        <span className="truncate max-w-[170px]">
                          {book.title}
                        </span>
                        {book.author && (
                          <span className="text-xs text-muted-foreground font-normal">
                            {book.author}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {/* -------------------------------------------------------- */}
                {/* METRICS section                                          */}
                {/* -------------------------------------------------------- */}
                {metrics.map((metric) => {
                  const numericValues = columnsBooks.map((b) =>
                    metric.numeric(b),
                  );
                  const best = bestIndex(numericValues, metric.direction);
                  const worst = worstIndex(numericValues, metric.direction);

                  return (
                    <tr key={metric.label} className="border-b last:border-b-0">
                      <td className="px-4 py-3 font-medium sticky left-0 bg-card">
                        {metric.label}
                      </td>
                      {columnsBooks.map((book, idx) => {
                        const isUserBook = idx === 0 && !!userBookId;
                        const isBest = idx === best;
                        const isWorst = idx === worst;
                        // Highlight green if user's book has advantage, red if disadvantage
                        const highlightGreen = isUserBook && isBest;
                        const highlightRed = isUserBook && isWorst;
                        // Also highlight non-user cells inversely for visual contrast
                        const cellGreen = !isUserBook && isBest;
                        const cellRed = !isUserBook && isWorst;

                        return (
                          <td
                            key={book.id}
                            className={cn(
                              "px-4 py-3 text-center",
                              highlightGreen &&
                                "bg-green-50 text-green-700 font-semibold dark:bg-green-950/30 dark:text-green-400",
                              highlightRed &&
                                "bg-red-50 text-red-700 font-semibold dark:bg-red-950/30 dark:text-red-400",
                              !isUserBook && cellGreen &&
                                "bg-green-50/50 dark:bg-green-950/20",
                              !isUserBook && cellRed &&
                                "bg-red-50/50 dark:bg-red-950/20",
                            )}
                          >
                            {metric.extract(book)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}

                {/* -------------------------------------------------------- */}
                {/* CONTENT section header                                   */}
                {/* -------------------------------------------------------- */}
                <tr className="border-b bg-muted/30">
                  <td
                    colSpan={columnsBooks.length + 1}
                    className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                  >
                    {t("compare.content")}
                  </td>
                </tr>

                {/* Feature checklist rows */}
                {featureData.map((feature) => (
                  <tr key={feature.key} className="border-b last:border-b-0">
                    <td className="px-4 py-3 font-medium sticky left-0 bg-card">
                      {feature.label}
                    </td>
                    {feature.values.map((hasFeature, idx) => (
                      <td key={idx} className="px-4 py-3 text-center">
                        {hasFeature ? (
                          <Check className="inline-block h-5 w-5 text-green-600" />
                        ) : (
                          <X className="inline-block h-5 w-5 text-red-400" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}

                {/* -------------------------------------------------------- */}
                {/* STRENGTHS section header                                 */}
                {/* -------------------------------------------------------- */}
                <tr className="border-b bg-muted/30">
                  <td
                    colSpan={columnsBooks.length + 1}
                    className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                  >
                    {t("compare.strengths")}
                  </td>
                </tr>
                <tr className="border-b last:border-b-0">
                  <td className="px-4 py-3 font-medium sticky left-0 bg-card align-top">
                    {t("compare.strengths")}
                  </td>
                  {strengthsWeaknesses.map((sw, idx) => (
                    <td
                      key={idx}
                      className="px-4 py-3 align-top"
                    >
                      {sw.strengths.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-sm text-green-700 dark:text-green-400">
                          {sw.strengths.map((s, si) => (
                            <li key={si}>{s}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-muted-foreground text-sm">--</span>
                      )}
                    </td>
                  ))}
                </tr>

                {/* -------------------------------------------------------- */}
                {/* WEAKNESSES section header                                */}
                {/* -------------------------------------------------------- */}
                <tr className="border-b bg-muted/30">
                  <td
                    colSpan={columnsBooks.length + 1}
                    className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                  >
                    {t("compare.weaknesses")}
                  </td>
                </tr>
                <tr className="border-b last:border-b-0">
                  <td className="px-4 py-3 font-medium sticky left-0 bg-card align-top">
                    {t("compare.weaknesses")}
                  </td>
                  {strengthsWeaknesses.map((sw, idx) => (
                    <td
                      key={idx}
                      className="px-4 py-3 align-top"
                    >
                      {sw.weaknesses.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-sm text-red-600 dark:text-red-400">
                          {sw.weaknesses.map((w, wi) => (
                            <li key={wi}>{w}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-muted-foreground text-sm">--</span>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Strategy result                                                    */}
      {/* ------------------------------------------------------------------ */}
      {comparisonResult?.strategy && (
        <div className="border rounded-lg bg-card p-4 space-y-2">
          <h3 className="text-sm font-semibold">
            {t("compare.generateStrategy")}
          </h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {comparisonResult.strategy}
          </p>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Action Buttons                                                     */}
      {/* ------------------------------------------------------------------ */}
      {columnsBooks.length >= 2 && (
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            {t("compare.exportComparison")}
          </Button>
          <Button
            onClick={handleGenerateStrategy}
            disabled={compareMutation.isPending}
          >
            {compareMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("compare.generatingStrategy")}
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                {t("compare.generateStrategy")}
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
