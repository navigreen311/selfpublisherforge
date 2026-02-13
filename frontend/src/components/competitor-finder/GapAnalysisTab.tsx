"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { useGapAnalysis } from "@/modules/competitors/hooks";
import type {
  CompetitorBookBrief,
  GapAnalysis,
} from "@/modules/competitors/hooks";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { WeaknessSignals } from "./WeaknessSignals";
import { OpportunityBlueprintCard } from "./OpportunityBlueprintCard";
import { Play, ChevronDown, Check, Loader2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface GapAnalysisTabProps {
  trackedCompetitors?: CompetitorBookBrief[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GapAnalysisTab({ trackedCompetitors = [] }: GapAnalysisTabProps) {
  const t = useTranslations("competitors");
  const [selectedCompetitorIds, setSelectedCompetitorIds] = useState<string[]>([]);
  const [gapAnalysisResult, setGapAnalysisResult] = useState<GapAnalysis | null>(null);
  const [selectorOpen, setSelectorOpen] = useState(false);

  const gapAnalysisMutation = useGapAnalysis();

  const useAllTracked = selectedCompetitorIds.length === 0;

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleRunAnalysis = () => {
    const bookIds = useAllTracked
      ? trackedCompetitors.map((c) => c.id)
      : selectedCompetitorIds;

    if (bookIds.length === 0) return;

    gapAnalysisMutation.mutate(
      {
        request: {
          niche: trackedCompetitors[0]?.category ?? "general",
          book_ids: bookIds,
          competitor_ids: bookIds,
        },
      },
      {
        onSuccess: (data) => {
          setGapAnalysisResult(data);
        },
      },
    );
  };

  const handleToggleCompetitor = (id: string) => {
    setSelectedCompetitorIds((prev) =>
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id],
    );
  };

  const selectedLabel = useAllTracked
    ? t("gap.allTracked")
    : `${selectedCompetitorIds.length} ${t("gap.books")}`;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{t("gap.title")}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t("gap.description")}
          </p>
        </div>
        <Button
          onClick={handleRunAnalysis}
          disabled={
            gapAnalysisMutation.isPending ||
            (trackedCompetitors.length === 0 && selectedCompetitorIds.length === 0)
          }
        >
          {gapAnalysisMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t("gap.running")}
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              {t("gap.runAnalysis")}
            </>
          )}
        </Button>
      </div>

      {/* Competitor selector */}
      <div className="space-y-2">
        <label className="text-sm font-medium">{t("gap.selectCompetitors")}</label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setSelectorOpen((prev) => !prev)}
            className="flex h-10 w-full max-w-md items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <span>{selectedLabel}</span>
            <ChevronDown className="h-4 w-4 opacity-50" />
          </button>

          {selectorOpen && trackedCompetitors.length > 0 && (
            <div className="absolute z-50 mt-1 w-full max-w-md rounded-md border bg-background shadow-md">
              {/* All Tracked option */}
              <button
                type="button"
                onClick={() => {
                  setSelectedCompetitorIds([]);
                  setSelectorOpen(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
              >
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded border ${
                    useAllTracked
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input"
                  }`}
                >
                  {useAllTracked && <Check className="h-3 w-3" />}
                </span>
                <span className="font-medium">{t("gap.allTracked")}</span>
                <Badge variant="outline" className="ml-auto">
                  {trackedCompetitors.length}
                </Badge>
              </button>

              <div className="border-t" />

              {/* Individual competitor options */}
              <div className="max-h-60 overflow-y-auto">
                {trackedCompetitors.map((competitor) => {
                  const isSelected = selectedCompetitorIds.includes(competitor.id);
                  return (
                    <button
                      key={competitor.id}
                      type="button"
                      onClick={() => handleToggleCompetitor(competitor.id)}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
                    >
                      <span
                        className={`flex h-4 w-4 items-center justify-center rounded border ${
                          isSelected
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-input"
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3" />}
                      </span>
                      <span className="truncate">{competitor.title}</span>
                      {competitor.author && (
                        <span className="ml-auto text-xs text-muted-foreground truncate">
                          {competitor.author}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Loading state */}
      {gapAnalysisMutation.isPending && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm font-medium">{t("gap.running")}</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div className="bg-primary h-full rounded-full animate-pulse w-2/3" />
          </div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        </div>
      )}

      {/* Error state */}
      {gapAnalysisMutation.isError && (
        <Alert variant="destructive">
          <AlertDescription>{t("gap.error")}</AlertDescription>
        </Alert>
      )}

      {/* Results */}
      {!gapAnalysisMutation.isPending && gapAnalysisResult && (
        <div className="space-y-6">
          {/* Weakness Signals */}
          {gapAnalysisResult.weakness_signals &&
          gapAnalysisResult.weakness_signals.length > 0 ? (
            <WeaknessSignals
              signals={gapAnalysisResult.weakness_signals}
              totalSignals={gapAnalysisResult.total_signals ?? 0}
              bookCount={gapAnalysisResult.books_analyzed}
            />
          ) : (
            <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
              {t("gap.noResults")}
            </div>
          )}

          {/* Opportunity Blueprint */}
          {gapAnalysisResult.opportunity_blueprint && (
            <OpportunityBlueprintCard
              blueprint={gapAnalysisResult.opportunity_blueprint}
              differentiationScore={gapAnalysisResult.differentiation_score}
            />
          )}
        </div>
      )}
    </div>
  );
}
