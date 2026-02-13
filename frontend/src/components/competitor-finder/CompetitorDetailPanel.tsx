"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useCompetitorBsrHistory } from "@/modules/competitors/hooks";
import { useCompetitorDetail } from "@/modules/market/hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CompetitorDetailPanelProps {
  competitorId: string;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompetitorDetailPanel({
  competitorId,
  onClose,
}: CompetitorDetailPanelProps) {
  const t = useTranslations("competitors");

  const {
    data: competitor,
    isLoading: isDetailLoading,
  } = useCompetitorDetail(competitorId);

  const {
    data: bsrHistoryResponse,
    isLoading: isBsrLoading,
  } = useCompetitorBsrHistory(competitorId, "90d");

  const bsrHistory = bsrHistoryResponse?.data ?? [];

  // Expandable description state
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // -------------------------------------------
  // Loading state
  // -------------------------------------------

  if (isDetailLoading) {
    return (
      <>
        <Backdrop onClick={onClose} />
        <div className="fixed right-0 top-0 h-full w-full max-w-[500px] bg-white shadow-xl z-50 overflow-y-auto">
          <div className="p-6 space-y-6">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
            <Skeleton className="h-64" />
          </div>
        </div>
      </>
    );
  }

  if (!competitor) {
    return (
      <>
        <Backdrop onClick={onClose} />
        <div className="fixed right-0 top-0 h-full w-full max-w-[500px] bg-white shadow-xl z-50 flex items-center justify-center">
          <p className="text-muted-foreground">Competitor not found.</p>
        </div>
      </>
    );
  }

  // -------------------------------------------
  // Derived data
  // -------------------------------------------

  const description = competitor.description ?? "";
  const shouldTruncateDescription = description.length > 300;
  const displayDescription =
    shouldTruncateDescription && !isDescriptionExpanded
      ? description.slice(0, 300) + "..."
      : description;

  const categories: string[] =
    (competitor as unknown as Record<string, unknown>).categories as string[] ??
    (competitor.category ? [competitor.category] : []);

  const keywords: string[] = competitor.keywords_extracted ?? [];

  // Review sentiment from the competitor detail (if available on the object)
  const sentimentData = (competitor as unknown as Record<string, unknown>)
    .review_sentiment as
    | { positive: number; negative: number; neutral: number }
    | undefined;

  // -------------------------------------------
  // Render
  // -------------------------------------------

  return (
    <>
      {/* Backdrop overlay */}
      <Backdrop onClick={onClose} />

      {/* Slide-out panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-[500px] bg-white shadow-xl z-50 overflow-y-auto animate-in slide-in-from-right duration-300">
        {/* ---- Header ---- */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-start justify-between gap-4 z-10">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold leading-tight truncate">
              {competitor.title}
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              {competitor.author}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Close"
          >
            <XIcon />
          </button>
        </div>

        <div className="p-6 space-y-8">
          {/* ---- Metrics Grid (2x3) ---- */}
          <section>
            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                label={t("detail.stats.bsr")}
                value={
                  competitor.bsr != null
                    ? `#${competitor.bsr.toLocaleString()}`
                    : "N/A"
                }
              />
              <MetricCard
                label={t("detail.stats.price")}
                value={
                  competitor.price != null
                    ? `$${competitor.price.toFixed(2)}`
                    : "N/A"
                }
              />
              <MetricCard
                label={t("detail.stats.rating")}
                value={
                  competitor.rating != null
                    ? `${competitor.rating.toFixed(1)} / 5`
                    : "N/A"
                }
              />
              <MetricCard
                label={t("detail.stats.reviews")}
                value={
                  competitor.reviews_count != null
                    ? competitor.reviews_count.toLocaleString()
                    : "0"
                }
              />
              <MetricCard
                label={t("detail.stats.pages")}
                value={
                  competitor.page_count != null
                    ? competitor.page_count.toLocaleString()
                    : "N/A"
                }
              />
              <MetricCard
                label={t("detail.stats.estRevenue")}
                value={
                  competitor.estimated_monthly_revenue != null
                    ? `$${competitor.estimated_monthly_revenue.toLocaleString()}/mo`
                    : "N/A"
                }
              />
            </div>
            {competitor.publish_date && (
              <div className="mt-3 text-sm text-muted-foreground">
                <span className="font-medium">
                  {t("detail.stats.published")}:
                </span>{" "}
                {new Date(competitor.publish_date).toLocaleDateString()}
              </div>
            )}
          </section>

          {/* ---- BSR History Chart ---- */}
          <section>
            <h3 className="text-sm font-semibold mb-3">
              {t("detail.bsrHistory")}
            </h3>
            {isBsrLoading ? (
              <Skeleton className="h-48 w-full" />
            ) : bsrHistory.length > 0 ? (
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={bsrHistory}>
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value: string) => {
                        const d = new Date(value);
                        return `${d.getMonth() + 1}/${d.getDate()}`;
                      }}
                      interval="preserveStartEnd"
                    />
                    <YAxis
                      reversed
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value: number) =>
                        value >= 1000
                          ? `${(value / 1000).toFixed(0)}k`
                          : String(value)
                      }
                      width={50}
                    />
                    <Tooltip
                      labelFormatter={(label: string) =>
                        new Date(label).toLocaleDateString()
                      }
                      formatter={(value: number) => [
                        `#${value.toLocaleString()}`,
                        "BSR",
                      ]}
                    />
                    <Line
                      type="monotone"
                      dataKey="bsr"
                      stroke="#6366f1"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No BSR history data available.
              </p>
            )}
          </section>

          {/* ---- Full Description ---- */}
          {description && (
            <section>
              <h3 className="text-sm font-semibold mb-2">
                {t("detail.fullDescription")}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                {displayDescription}
              </p>
              {shouldTruncateDescription && (
                <button
                  type="button"
                  onClick={() =>
                    setIsDescriptionExpanded((prev) => !prev)
                  }
                  className="text-sm text-indigo-600 hover:text-indigo-800 mt-1 font-medium"
                >
                  {isDescriptionExpanded ? "Show less" : "Show more"}
                </button>
              )}
            </section>
          )}

          {/* ---- Amazon Categories ---- */}
          {categories.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold mb-2">
                {t("detail.amazonCategories")}
              </h3>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                  <Badge
                    key={cat}
                    variant="secondary"
                    className="text-xs"
                  >
                    {cat}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          {/* ---- Estimated Keywords ---- */}
          {keywords.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold mb-2">
                {t("detail.estimatedKeywords")}
              </h3>
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw) => (
                  <Badge
                    key={kw}
                    variant="outline"
                    className="text-xs"
                  >
                    {kw}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          {/* ---- Review Sentiment ---- */}
          {sentimentData && (
            <section>
              <h3 className="text-sm font-semibold mb-3">
                {t("detail.reviewSentiment")}
              </h3>
              <div className="space-y-2">
                <SentimentBar
                  label="Positive"
                  value={sentimentData.positive}
                  total={
                    sentimentData.positive +
                    sentimentData.negative +
                    sentimentData.neutral
                  }
                  colorClass="bg-green-500"
                />
                <SentimentBar
                  label="Neutral"
                  value={sentimentData.neutral}
                  total={
                    sentimentData.positive +
                    sentimentData.negative +
                    sentimentData.neutral
                  }
                  colorClass="bg-gray-400"
                />
                <SentimentBar
                  label="Negative"
                  value={sentimentData.negative}
                  total={
                    sentimentData.positive +
                    sentimentData.negative +
                    sentimentData.neutral
                  }
                  colorClass="bg-red-500"
                />
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Internal helper components
// ---------------------------------------------------------------------------

function Backdrop({ onClick }: { onClick: () => void }) {
  return (
    <div
      className="fixed inset-0 bg-black/40 z-40 animate-in fade-in duration-200"
      onClick={onClick}
      aria-hidden="true"
    />
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold mt-1 truncate">{value}</p>
    </div>
  );
}

function SentimentBar({
  label,
  value,
  total,
  colorClass,
}: {
  label: string;
  value: number;
  total: number;
  colorClass: string;
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-muted-foreground w-16 shrink-0">
        {label}
      </span>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium w-10 text-right">{pct}%</span>
    </div>
  );
}

function XIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
