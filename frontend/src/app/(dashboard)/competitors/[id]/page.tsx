"use client";

import { use } from "react";
import { useCompetitorAnalysis, useWeaknesses, useOpportunity } from "@/modules/competitors/hooks";
import { OpportunityCard } from "@/modules/competitors/components/OpportunityCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { WeaknessSignal } from "@/modules/competitors/types";

interface CompetitorDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CompetitorDetailPage({ params }: CompetitorDetailPageProps) {
  const { id } = use(params);
  const { data: analysis, isLoading: analysisLoading } = useCompetitorAnalysis(id);
  const { data: weaknesses = [], isLoading: weaknessesLoading } = useWeaknesses(id);
  const { data: opportunity, isLoading: opportunityLoading } = useOpportunity(id);

  if (analysisLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="h-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        Competitor analysis not found
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">
          {analysis.book?.title ?? "Competitor Analysis"}
        </h1>
        {analysis.book?.author && (
          <p className="text-muted-foreground mt-1">by {analysis.book.author}</p>
        )}
      </div>

      {/* Overview Card */}
      <div className="border rounded-lg bg-card p-6">
        <h3 className="font-semibold text-lg mb-4">Overview</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="BSR" value={analysis.book?.bsr?.toLocaleString() ?? "N/A"} />
          <StatCard
            label="Price"
            value={analysis.book?.price ? `$${analysis.book.price.toFixed(2)}` : "N/A"}
          />
          <StatCard
            label="Rating"
            value={
              analysis.book?.rating ? `${analysis.book.rating.toFixed(1)} ★` : "N/A"
            }
          />
          <StatCard
            label="Reviews"
            value={analysis.book?.review_count?.toLocaleString() ?? "0"}
          />
          <StatCard
            label="Overall Score"
            value={
              analysis.overall_score !== undefined
                ? Math.round(analysis.overall_score).toString()
                : "N/A"
            }
          />
          <StatCard
            label="Sentiment"
            value={
              analysis.sentiment_score !== undefined
                ? `${(analysis.sentiment_score * 100).toFixed(0)}%`
                : "N/A"
            }
          />
          <StatCard label="Weaknesses" value={analysis.weakness_count.toString()} />
          <StatCard label="Strengths" value={analysis.strength_count.toString()} />
        </div>

        {analysis.review_summary && (
          <div className="mt-4 p-3 rounded bg-muted/50">
            <h4 className="text-sm font-medium mb-2">Review Summary</h4>
            <p className="text-sm text-muted-foreground">{analysis.review_summary}</p>
          </div>
        )}
      </div>

      {/* Weaknesses */}
      {weaknessesLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        weaknesses.length > 0 && (
          <div className="border rounded-lg bg-card p-6">
            <h3 className="font-semibold text-lg mb-4">
              Detected Weaknesses ({weaknesses.length})
            </h3>
            <div className="space-y-3">
              {weaknesses.map((weakness) => (
                <WeaknessCard key={weakness.id} weakness={weakness} />
              ))}
            </div>
          </div>
        )
      )}

      {/* Opportunity Blueprint */}
      {opportunityLoading ? (
        <Skeleton className="h-96" />
      ) : (
        opportunity && <OpportunityCard opportunity={opportunity} />
      )}

      {analysis.status === "failed" && analysis.error_message && (
        <div className="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
          <strong>Analysis Failed:</strong> {analysis.error_message}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-md bg-muted/50 text-center">
      <div className="text-lg font-semibold">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function WeaknessCard({ weakness }: { weakness: WeaknessSignal }) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={weakness.severity} />
            <CategoryBadge category={weakness.category} />
            {weakness.actionable && (
              <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                Actionable
              </Badge>
            )}
          </div>
          <p className="text-sm font-medium">{weakness.signal_text}</p>
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <div>Frequency: {weakness.frequency}</div>
          <div>Confidence: {(weakness.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>

      {weakness.suggestion && (
        <div className="mt-3 p-3 rounded bg-blue-50 border border-blue-200">
          <p className="text-xs text-blue-900">
            <strong>Suggestion:</strong> {weakness.suggestion}
          </p>
        </div>
      )}

      {weakness.evidence && weakness.evidence.length > 0 && (
        <div className="mt-3">
          <h5 className="text-xs font-medium text-muted-foreground mb-2">Evidence:</h5>
          <div className="space-y-2">
            {weakness.evidence.slice(0, 2).map((evidence, idx) => (
              <div key={idx} className="p-2 rounded bg-muted/50 text-xs">
                <p className="italic">"{evidence.excerpt}"</p>
                {evidence.rating !== undefined && (
                  <div className="mt-1 text-muted-foreground">
                    Rating: {evidence.rating}/5
                    {evidence.helpful_votes !== undefined &&
                      ` • ${evidence.helpful_votes} found helpful`}
                  </div>
                )}
              </div>
            ))}
            {weakness.evidence.length > 2 && (
              <p className="text-xs text-muted-foreground">
                +{weakness.evidence.length - 2} more evidence items
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const config: Record<string, { label: string; className: string }> = {
    low: { label: "Low", className: "bg-gray-100 text-gray-700" },
    medium: { label: "Medium", className: "bg-yellow-100 text-yellow-700" },
    high: { label: "High", className: "bg-orange-100 text-orange-700" },
    critical: { label: "Critical", className: "bg-red-100 text-red-700" },
  };

  const { label, className } = config[severity] ?? config.low;
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      {label}
    </Badge>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const labels: Record<string, string> = {
    content_quality: "Content",
    format_layout: "Format",
    missing_features: "Features",
    pricing: "Pricing",
    coverage_gaps: "Coverage",
  };

  return (
    <Badge variant="outline" className="bg-purple-50 text-purple-700 text-xs">
      {labels[category] ?? category}
    </Badge>
  );
}
