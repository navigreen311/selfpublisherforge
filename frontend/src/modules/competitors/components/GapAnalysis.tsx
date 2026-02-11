"use client";

import { cn } from "@/lib/utils";
import type { GapAnalysis, CoverGap, TitleGap, ContentGap } from "../types";
import { Badge } from "@/components/ui/badge";

interface GapAnalysisProps {
  analysis: GapAnalysis;
}

export function GapAnalysisComponent({ analysis }: GapAnalysisProps) {
  return (
    <div className="border rounded-lg bg-card p-6 space-y-6">
      {/* Header */}
      <div>
        <h3 className="font-semibold text-lg">Gap Analysis: {analysis.niche}</h3>
        {analysis.summary && (
          <p className="text-sm text-muted-foreground mt-1">{analysis.summary}</p>
        )}
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <span>{analysis.books_analyzed} books analyzed</span>
          <span>•</span>
          <span>Status: {analysis.status}</span>
        </div>
      </div>

      {/* Cover Gaps */}
      {analysis.cover_gaps && analysis.cover_gaps.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
            Cover Design Gaps
            <Badge variant="outline" className="bg-purple-100 text-purple-700">
              {analysis.cover_gaps.length}
            </Badge>
          </h4>
          <div className="space-y-2">
            {analysis.cover_gaps.map((gap, idx) => (
              <CoverGapCard key={idx} gap={gap} />
            ))}
          </div>
        </div>
      )}

      {/* Title Gaps */}
      {analysis.title_gaps && analysis.title_gaps.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
            Title & Subtitle Gaps
            <Badge variant="outline" className="bg-blue-100 text-blue-700">
              {analysis.title_gaps.length}
            </Badge>
          </h4>
          <div className="space-y-2">
            {analysis.title_gaps.map((gap, idx) => (
              <TitleGapCard key={idx} gap={gap} />
            ))}
          </div>
        </div>
      )}

      {/* Content Gaps */}
      {analysis.content_gaps && analysis.content_gaps.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
            Content Coverage Gaps
            <Badge variant="outline" className="bg-green-100 text-green-700">
              {analysis.content_gaps.length}
            </Badge>
          </h4>
          <div className="space-y-2">
            {analysis.content_gaps.map((gap, idx) => (
              <ContentGapCard key={idx} gap={gap} />
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <div className="pt-4 border-t">
          <h4 className="font-medium text-sm mb-3">Recommendations</h4>
          <ul className="space-y-2">
            {analysis.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-green-600 mt-0.5">✓</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Gap card components
// ---------------------------------------------------------------------------

function CoverGapCard({ gap }: { gap: CoverGap }) {
  const prevalenceColor =
    gap.prevalence >= 0.7 ? "text-red-600" :
    gap.prevalence >= 0.4 ? "text-yellow-600" :
    "text-green-600";

  return (
    <div className="p-3 rounded-md bg-muted/50">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">{gap.gap_type}</span>
            <span className={cn("text-xs font-medium", prevalenceColor)}>
              {Math.round(gap.prevalence * 100)}% prevalence
            </span>
          </div>
          <p className="text-xs text-muted-foreground">{gap.description}</p>
          {gap.opportunity && (
            <div className="mt-2 p-2 rounded bg-purple-50 border border-purple-200">
              <p className="text-xs text-purple-900">
                <strong>Opportunity:</strong> {gap.opportunity}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TitleGapCard({ gap }: { gap: TitleGap }) {
  return (
    <div className="p-3 rounded-md bg-muted/50">
      <div className="flex-1">
        <div className="text-sm font-medium mb-1">{gap.gap_type}</div>
        <p className="text-xs text-muted-foreground mb-2">{gap.description}</p>
        {gap.missing_keywords && gap.missing_keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {gap.missing_keywords.map((kw, idx) => (
              <Badge key={idx} variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                {kw}
              </Badge>
            ))}
          </div>
        )}
        {gap.opportunity && (
          <div className="p-2 rounded bg-blue-50 border border-blue-200">
            <p className="text-xs text-blue-900">
              <strong>Opportunity:</strong> {gap.opportunity}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ContentGapCard({ gap }: { gap: ContentGap }) {
  const coverageColor =
    gap.competitor_coverage >= 0.7 ? "text-red-600" :
    gap.competitor_coverage >= 0.4 ? "text-yellow-600" :
    "text-green-600";

  return (
    <div className="p-3 rounded-md bg-muted/50">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium">{gap.topic}</span>
          <span className={cn("text-xs font-medium", coverageColor)}>
            {Math.round(gap.competitor_coverage * 100)}% covered
          </span>
        </div>
        <p className="text-xs text-muted-foreground mb-2">{gap.description}</p>
        {gap.demand_signal && (
          <div className="p-2 rounded bg-green-50 border border-green-200">
            <p className="text-xs text-green-900">
              <strong>Demand Signal:</strong> {gap.demand_signal}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
