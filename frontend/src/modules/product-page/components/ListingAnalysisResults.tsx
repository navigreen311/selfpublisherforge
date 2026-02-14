"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Search,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { ListingAnalysisResult, ListingFinding } from "../types";

interface ListingAnalysisResultsProps {
  result: ListingAnalysisResult;
  onSwitchToBlurb?: () => void;
  onSwitchToKeywords?: () => void;
  className?: string;
}

function ScoreCircle({ score, size = "lg" }: { score: number; size?: "sm" | "lg" }) {
  const colorClass =
    score >= 80
      ? "border-green-500 text-green-700 bg-green-50"
      : score >= 60
        ? "border-yellow-500 text-yellow-700 bg-yellow-50"
        : "border-red-500 text-red-700 bg-red-50";

  const dimensions = size === "lg" ? "w-24 h-24 text-3xl border-4" : "w-14 h-14 text-lg border-2";

  return (
    <div
      className={cn(
        "rounded-full flex items-center justify-center font-bold",
        dimensions,
        colorClass
      )}
    >
      {Math.round(score)}
    </div>
  );
}

function FindingIcon({ type }: { type: ListingFinding["type"] }) {
  switch (type) {
    case "good":
      return <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />;
    case "warning":
      return <AlertTriangle className="h-4 w-4 text-yellow-600 shrink-0" />;
    case "problem":
      return <XCircle className="h-4 w-4 text-red-600 shrink-0" />;
  }
}

function DimensionCard({
  dimension,
  score,
  color,
  findings,
  suggestion,
}: {
  dimension: string;
  score: number;
  color: "green" | "yellow" | "red";
  findings: ListingFinding[];
  suggestion?: { current: string; suggested: string };
}) {
  const [open, setOpen] = useState(false);

  const colorStyles = {
    green: "border-l-green-500",
    yellow: "border-l-yellow-500",
    red: "border-l-red-500",
  };

  const badgeColor = {
    green: "bg-green-100 text-green-800",
    yellow: "bg-yellow-100 text-yellow-800",
    red: "bg-red-100 text-red-800",
  };

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn("border-l-4", colorStyles[color])}>
        <CollapsibleTrigger asChild>
          <button className="w-full p-4 flex items-center justify-between text-left hover:bg-accent/50 transition-colors rounded-lg">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold capitalize">
                {dimension.replace(/_/g, " ")}
              </span>
              <span
                className={cn(
                  "px-2 py-0.5 rounded-full text-xs font-bold",
                  badgeColor[color]
                )}
              >
                {Math.round(score)}/100
              </span>
            </div>
            {open ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-3">
            {/* Findings */}
            {findings.length > 0 && (
              <div className="space-y-1.5">
                {findings.map((finding, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <FindingIcon type={finding.type} />
                    <span className="text-muted-foreground">{finding.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Suggestion */}
            {suggestion && (
              <div className="rounded-md bg-muted/50 p-3 space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground">Current:</p>
                <p className="text-sm">{suggestion.current}</p>
                <p className="text-xs font-medium text-muted-foreground mt-2">Suggested:</p>
                <p className="text-sm text-primary">{suggestion.suggested}</p>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export function ListingAnalysisResults({
  result,
  onSwitchToBlurb,
  onSwitchToKeywords,
  className,
}: ListingAnalysisResultsProps) {
  const dimensions = Object.keys(result.scores);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with overall score */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Analysis Results</h3>
              <p className="text-sm text-muted-foreground mt-1">
                ID: {result.id.slice(0, 12)}...
              </p>
            </div>
            <div className="flex flex-col items-center gap-1">
              <ScoreCircle score={result.overall_score} size="lg" />
              <span className="text-xs text-muted-foreground">Overall Score</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Score dimensions grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {dimensions.map((dim) => {
          const scoreData = result.scores[dim];
          const findings = result.findings[dim] ?? [];
          const suggestion = result.suggestions[dim];

          return (
            <DimensionCard
              key={dim}
              dimension={dim}
              score={scoreData.score}
              color={scoreData.color}
              findings={findings}
              suggestion={suggestion}
            />
          );
        })}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        {onSwitchToBlurb && (
          <Button variant="outline" onClick={onSwitchToBlurb}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Optimized Blurb
          </Button>
        )}
        {onSwitchToKeywords && (
          <Button variant="outline" onClick={onSwitchToKeywords}>
            <Search className="mr-2 h-4 w-4" />
            Optimize Keywords
          </Button>
        )}
      </div>
    </div>
  );
}
