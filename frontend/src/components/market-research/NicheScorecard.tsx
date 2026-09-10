"use client";

import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import type { NicheAnalysisResponse } from "@/modules/market/hooks";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Save } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return color classes based on a 0-100 score. */
function scoreColorClasses(score: number) {
  if (score >= 70) {
    return {
      bg: "bg-green-50",
      border: "border-green-200",
      text: "text-green-700",
    };
  }
  if (score >= 40) {
    return {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      text: "text-yellow-700",
    };
  }
  return {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-700",
  };
}

/** Map a 0-100 score to a human-readable translation key. */
function scoreLabelKey(score: number): string {
  if (score >= 80) return "scores.veryGood";
  if (score >= 60) return "scores.good";
  if (score >= 40) return "scores.moderate";
  return "scores.low";
}

/** Format currency for display (e.g. $1,234/mo). */
function formatRevenue(amount: number): string {
  return `$${Math.round(amount).toLocaleString()}/mo`;
}

/** Format an ISO date string to a readable time string. */
function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ScoreCardItemProps {
  label: string;
  value: string;
  subtitle: string;
  colorClasses: ReturnType<typeof scoreColorClasses>;
}

function ScoreCardItem({ label, value, subtitle, colorClasses }: ScoreCardItemProps) {
  return (
    <Card className={cn("border", colorClasses.border, colorClasses.bg)}>
      <CardContent className="p-4 text-center">
        <p className="text-xs font-medium text-muted-foreground mb-1">
          {label}
        </p>
        <p className={cn("text-3xl font-bold", colorClasses.text)}>
          {value}
        </p>
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

interface RevenueCardItemProps {
  label: string;
  value: string;
  subtitle: string;
}

function RevenueCardItem({ label, value, subtitle }: RevenueCardItemProps) {
  return (
    <Card className="border border-border">
      <CardContent className="p-4 text-center">
        <p className="text-xs font-medium text-muted-foreground mb-1">
          {label}
        </p>
        <p className="text-3xl font-bold text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface NicheScorecardProps {
  analysis: NicheAnalysisResponse;
  onExportPdf?: () => void;
  onSave?: () => void;
}

export function NicheScorecard({
  analysis,
  onExportPdf,
  onSave,
}: NicheScorecardProps) {
  const t = useTranslations("market");

  const opportunityColor = scoreColorClasses(analysis.opportunity_score);
  const demandColor = scoreColorClasses(analysis.demand_score);
  // Supply score is INVERSE: lower competition = higher score displayed,
  // but the score itself already represents "how good" the supply situation is.
  // Color: high supply_score means low competition = green.
  const supplyColor = scoreColorClasses(analysis.supply_score);

  const totalBooks = analysis.total_books ?? analysis.top_competitors.length;

  return (
    <Card>
      {/* Header */}
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <CardTitle className="text-xl">
              {t("scores.nicheAnalysis", { fallback: "Niche Analysis" })}:{" "}
              {analysis.niche}
            </CardTitle>
            <CardDescription className="mt-1">
              {t("analyzed", {
                count: totalBooks,
                fallback: `Analyzed ${totalBooks} competing titles`,
              })}{" "}
              &middot; Last updated: {formatTimestamp(analysis.analyzed_at)}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onExportPdf}>
              <Download className="mr-2 h-4 w-4" />
              {t("results.exportPdf")}
            </Button>
            <Button variant="outline" size="sm" onClick={onSave}>
              <Save className="mr-2 h-4 w-4" />
              {t("results.save")}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Score Cards Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Opportunity Score */}
          <ScoreCardItem
            label={t("scores.opportunity")}
            value={String(Math.round(analysis.opportunity_score))}
            subtitle={t(scoreLabelKey(analysis.opportunity_score))}
            colorClasses={opportunityColor}
          />

          {/* Demand Score */}
          <ScoreCardItem
            label={t("scores.demand")}
            value={String(Math.round(analysis.demand_score))}
            subtitle={t(scoreLabelKey(analysis.demand_score))}
            colorClasses={demandColor}
          />

          {/* Supply Score (inverse -- high = less competition = good) */}
          <ScoreCardItem
            label={t("scores.supply")}
            value={String(Math.round(analysis.supply_score))}
            subtitle={
              analysis.supply_score >= 60
                ? t("scores.low")
                : analysis.supply_score >= 40
                  ? t("scores.moderate")
                  : t("scores.high")
            }
            colorClasses={supplyColor}
          />

          {/* Avg Revenue */}
          <RevenueCardItem
            label={t("scores.avgRevenue")}
            value={
              analysis.avg_monthly_revenue != null
                ? formatRevenue(analysis.avg_monthly_revenue)
                : "--"
            }
            subtitle={t("scores.topAvg")}
          />
        </div>

        {/* Verdict Section */}
        {analysis.recommendation && (
          <div
            className={cn(
              "rounded-lg border p-4",
              opportunityColor.bg,
              opportunityColor.border
            )}
          >
            <h4 className="text-sm font-semibold mb-1">
              {t("scores.verdict")}
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {analysis.recommendation}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
