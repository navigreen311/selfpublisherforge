"use client";

import { cn } from "@/lib/utils";
import type { CompetitorAnalysisDetail } from "../types";
import { Badge } from "@/components/ui/badge";

interface CompetitorCompareProps {
  analyses: CompetitorAnalysisDetail[];
  maxCompare?: number;
}

export function CompetitorCompare({ analyses, maxCompare = 3 }: CompetitorCompareProps) {
  const compareAnalyses = analyses.slice(0, maxCompare);

  if (compareAnalyses.length === 0) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        Select competitors to compare (up to {maxCompare})
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left px-4 py-3 font-medium sticky left-0 bg-muted/50">
                Metric
              </th>
              {compareAnalyses.map((analysis) => (
                <th key={analysis.id} className="px-4 py-3 font-medium min-w-[200px]">
                  <div className="truncate max-w-[200px]">
                    {analysis.book?.title ?? "Unknown"}
                  </div>
                  <div className="text-xs text-muted-foreground font-normal">
                    {analysis.book?.author ?? ""}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Basic metrics */}
            <CompareRow
              label="BSR Rank"
              values={compareAnalyses.map((a) => a.book?.bsr?.toLocaleString() ?? "N/A")}
              highlightBest="low"
            />
            <CompareRow
              label="Price"
              values={compareAnalyses.map((a) =>
                a.book?.price ? `$${a.book.price.toFixed(2)}` : "N/A"
              )}
            />
            <CompareRow
              label="Rating"
              values={compareAnalyses.map((a) =>
                a.book?.rating ? `${a.book.rating.toFixed(1)} ★` : "N/A"
              )}
              highlightBest="high"
            />
            <CompareRow
              label="Reviews"
              values={compareAnalyses.map((a) =>
                a.book?.review_count?.toLocaleString() ?? "0"
              )}
              highlightBest="high"
            />

            {/* Analysis metrics */}
            <CompareRow
              label="Overall Score"
              values={compareAnalyses.map((a) =>
                a.overall_score !== undefined ? Math.round(a.overall_score).toString() : "N/A"
              )}
              highlightBest="high"
            />
            <CompareRow
              label="Sentiment Score"
              values={compareAnalyses.map((a) =>
                a.sentiment_score !== undefined
                  ? `${(a.sentiment_score * 100).toFixed(0)}%`
                  : "N/A"
              )}
              highlightBest="high"
            />
            <CompareRow
              label="Weaknesses Found"
              values={compareAnalyses.map((a) => a.weakness_count.toString())}
              highlightBest="low"
              highlightColor="green"
            />
            <CompareRow
              label="Strengths Found"
              values={compareAnalyses.map((a) => a.strength_count.toString())}
              highlightBest="high"
            />

            {/* Status */}
            <tr className="border-b last:border-b-0">
              <td className="px-4 py-3 font-medium sticky left-0 bg-card">Analysis Status</td>
              {compareAnalyses.map((analysis) => (
                <td key={analysis.id} className="px-4 py-3 text-center">
                  <StatusBadge status={analysis.status} />
                </td>
              ))}
            </tr>

            {/* Opportunity score if available */}
            <tr className="border-b last:border-b-0">
              <td className="px-4 py-3 font-medium sticky left-0 bg-card">
                Opportunity Score
              </td>
              {compareAnalyses.map((analysis) => (
                <td key={analysis.id} className="px-4 py-3 text-center">
                  {analysis.opportunity?.estimated_opportunity_score !== undefined ? (
                    <OpportunityScoreBadge
                      score={analysis.opportunity.estimated_opportunity_score}
                    />
                  ) : (
                    <span className="text-muted-foreground">N/A</span>
                  )}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Weakness breakdown */}
      <div className="p-4 border-t bg-muted/30">
        <h4 className="text-sm font-medium mb-3">Weakness Breakdown</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {compareAnalyses.map((analysis) => (
            <div key={analysis.id} className="p-3 rounded bg-card border">
              <div className="text-xs font-medium mb-2 truncate">
                {analysis.book?.title ?? "Unknown"}
              </div>
              {analysis.weaknesses && analysis.weaknesses.length > 0 ? (
                <div className="space-y-1">
                  {analysis.weaknesses.slice(0, 3).map((weakness) => (
                    <div key={weakness.id} className="text-xs flex items-start gap-2">
                      <SeverityDot severity={weakness.severity} />
                      <span className="truncate">{weakness.signal_text}</span>
                    </div>
                  ))}
                  {analysis.weaknesses.length > 3 && (
                    <div className="text-xs text-muted-foreground">
                      +{analysis.weaknesses.length - 3} more
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">No weaknesses found</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

interface CompareRowProps {
  label: string;
  values: string[];
  highlightBest?: "high" | "low";
  highlightColor?: "green" | "blue";
}

function CompareRow({ label, values, highlightBest, highlightColor = "blue" }: CompareRowProps) {
  let bestIndex = -1;
  if (highlightBest) {
    const numericValues = values.map((v) => {
      const cleaned = v.replace(/[^0-9.-]/g, "");
      return cleaned ? parseFloat(cleaned) : null;
    });

    if (numericValues.some((v) => v !== null)) {
      const validValues = numericValues.filter((v) => v !== null) as number[];
      const bestValue =
        highlightBest === "high" ? Math.max(...validValues) : Math.min(...validValues);
      bestIndex = numericValues.findIndex((v) => v === bestValue);
    }
  }

  return (
    <tr className="border-b last:border-b-0">
      <td className="px-4 py-3 font-medium sticky left-0 bg-card">{label}</td>
      {values.map((value, idx) => (
        <td
          key={idx}
          className={cn(
            "px-4 py-3 text-center",
            idx === bestIndex &&
              (highlightColor === "green"
                ? "bg-green-50 font-semibold text-green-700"
                : "bg-blue-50 font-semibold text-blue-700")
          )}
        >
          {value}
        </td>
      ))}
    </tr>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: "Pending", className: "bg-gray-100 text-gray-700" },
    processing: { label: "Processing", className: "bg-blue-100 text-blue-700" },
    completed: { label: "Completed", className: "bg-green-100 text-green-700" },
    failed: { label: "Failed", className: "bg-red-100 text-red-700" },
  };

  const { label, className } = config[status] ?? config.pending;
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  );
}

function OpportunityScoreBadge({ score }: { score: number }) {
  const rounded = Math.round(score);
  const color =
    rounded >= 70
      ? "bg-green-100 text-green-700"
      : rounded >= 40
      ? "bg-yellow-100 text-yellow-700"
      : "bg-red-100 text-red-700";

  return (
    <Badge variant="outline" className={cn("font-semibold", color)}>
      {rounded}
    </Badge>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const color =
    severity === "critical"
      ? "bg-red-600"
      : severity === "high"
      ? "bg-orange-600"
      : severity === "medium"
      ? "bg-yellow-600"
      : "bg-gray-600";

  return <span className={cn("w-2 h-2 rounded-full flex-shrink-0 mt-1", color)} />;
}
