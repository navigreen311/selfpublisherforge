"use client";

import { cn } from "@/lib/utils";
import type { NicheAnalysisResponse } from "../hooks";

interface NicheScoreCardProps {
  analysis: NicheAnalysisResponse;
}

function ScoreCircle({
  score,
  label,
  size = "lg",
}: {
  score: number;
  label: string;
  size?: "sm" | "lg";
}) {
  const color =
    score >= 70 ? "text-green-600" : score >= 40 ? "text-yellow-600" : "text-red-600";
  const bgColor =
    score >= 70 ? "bg-green-50" : score >= 40 ? "bg-yellow-50" : "bg-red-50";
  const dimension = size === "lg" ? "w-24 h-24" : "w-16 h-16";
  const textSize = size === "lg" ? "text-2xl" : "text-lg";

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={cn(
          "rounded-full flex items-center justify-center font-bold",
          dimension,
          bgColor,
          color
        )}
      >
        <span className={textSize}>{Math.round(score)}</span>
      </div>
      <span className="text-xs text-muted-foreground font-medium">{label}</span>
    </div>
  );
}

export function NicheScoreCard({ analysis }: NicheScoreCardProps) {
  return (
    <div className="border rounded-lg bg-card p-6 space-y-6">
      <div>
        <h3 className="font-semibold text-lg">Niche Analysis: {analysis.niche}</h3>
        <p className="text-sm text-muted-foreground mt-1">{analysis.recommendation}</p>
      </div>

      {/* Score circles */}
      <div className="flex items-center justify-center gap-8">
        <ScoreCircle score={analysis.opportunity_score} label="Opportunity" size="lg" />
        <ScoreCircle score={analysis.demand_score} label="Demand" size="sm" />
        <ScoreCircle score={analysis.supply_score} label="Competition" size="sm" />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {analysis.avg_bsr != null && (
          <div className="text-center">
            <div className="text-lg font-semibold">
              {Math.round(analysis.avg_bsr).toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Avg BSR</div>
          </div>
        )}
        {analysis.avg_monthly_revenue != null && (
          <div className="text-center">
            <div className="text-lg font-semibold">
              ${analysis.avg_monthly_revenue.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Est. Monthly Revenue</div>
          </div>
        )}
        <div className="text-center">
          <div className="text-lg font-semibold">{analysis.top_competitors.length}</div>
          <div className="text-xs text-muted-foreground">Top Competitors</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold">{analysis.gap_analysis.length}</div>
          <div className="text-xs text-muted-foreground">Gaps Found</div>
        </div>
      </div>

      {/* Gap analysis */}
      {analysis.gap_analysis.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-3">Gap Analysis</h4>
          <div className="space-y-2">
            {analysis.gap_analysis.map((gap, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 rounded-md bg-muted/50"
              >
                <span
                  className={cn(
                    "text-xs font-medium px-2 py-0.5 rounded-full mt-0.5 flex-shrink-0",
                    gap.opportunity_level === "high"
                      ? "bg-green-100 text-green-700"
                      : gap.opportunity_level === "medium"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-red-100 text-red-700"
                  )}
                >
                  {gap.opportunity_level}
                </span>
                <div>
                  <div className="text-sm font-medium">{gap.area}</div>
                  <div className="text-xs text-muted-foreground">{gap.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
