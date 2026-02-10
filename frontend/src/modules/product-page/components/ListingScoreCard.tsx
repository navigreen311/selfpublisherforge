"use client";

import { cn } from "@/lib/utils";
import type { ListingAnalysis } from "../hooks";

interface ListingScoreCardProps {
  analysis: ListingAnalysis;
  className?: string;
}

function ScoreBadge({ score, label }: { score: number; label: string }) {
  const color =
    score >= 80
      ? "bg-green-100 text-green-800"
      : score >= 60
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={cn("rounded-full px-3 py-2 text-lg font-bold", color)}>
        {Math.round(score)}
      </div>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
}

function RecommendationItem({
  area,
  severity,
  message,
  suggestion,
}: {
  area: string;
  severity: string;
  message: string;
  suggestion: string;
}) {
  const severityColors: Record<string, string> = {
    critical: "border-red-400 bg-red-50",
    warning: "border-yellow-400 bg-yellow-50",
    info: "border-blue-400 bg-blue-50",
  };

  return (
    <div
      className={cn(
        "rounded-md border-l-4 p-3",
        severityColors[severity] || "border-gray-400 bg-gray-50"
      )}
    >
      <div className="flex items-center gap-2 text-sm font-medium">
        <span className="uppercase text-xs tracking-wider text-gray-500">{area}</span>
        <span
          className={cn(
            "rounded px-1.5 py-0.5 text-xs font-semibold",
            severity === "critical"
              ? "bg-red-200 text-red-900"
              : severity === "warning"
                ? "bg-yellow-200 text-yellow-900"
                : "bg-blue-200 text-blue-900"
          )}
        >
          {severity}
        </span>
      </div>
      <p className="mt-1 text-sm">{message}</p>
      <p className="mt-1 text-xs text-gray-600">{suggestion}</p>
    </div>
  );
}

export function ListingScoreCard({ analysis, className }: ListingScoreCardProps) {
  return (
    <div className={cn("rounded-lg border bg-white p-6 shadow-sm", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Listing Analysis</h3>
          {analysis.asin && (
            <p className="text-sm text-gray-500">ASIN: {analysis.asin}</p>
          )}
        </div>
        <div className="text-center">
          <div
            className={cn(
              "text-3xl font-bold rounded-full w-16 h-16 flex items-center justify-center",
              analysis.overall_score >= 80
                ? "bg-green-100 text-green-700"
                : analysis.overall_score >= 60
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-red-100 text-red-700"
            )}
          >
            {Math.round(analysis.overall_score)}
          </div>
          <span className="text-xs text-gray-500">Overall</span>
        </div>
      </div>

      {/* Score badges */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-6">
        <ScoreBadge score={analysis.title_score} label="Title" />
        <ScoreBadge score={analysis.blurb_score} label="Blurb" />
        <ScoreBadge score={analysis.keyword_score} label="Keywords" />
        <ScoreBadge score={analysis.category_score} label="Category" />
        <ScoreBadge score={analysis.price_score} label="Price" />
      </div>

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold mb-3">
            Recommendations ({analysis.recommendations.length})
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {analysis.recommendations.map((rec, i) => (
              <RecommendationItem
                key={i}
                area={rec.area}
                severity={rec.severity}
                message={rec.message}
                suggestion={rec.suggestion}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
