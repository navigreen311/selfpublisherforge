"use client";

import { cn } from "@/lib/utils";
import type { OpportunityBlueprint } from "../types";
import { Badge } from "@/components/ui/badge";

interface OpportunityCardProps {
  opportunity: OpportunityBlueprint;
  className?: string;
}

export function OpportunityCard({ opportunity, className }: OpportunityCardProps) {
  const contentStrategy =
    typeof opportunity.content_strategy === "object" && opportunity.content_strategy !== null
      ? opportunity.content_strategy
      : undefined;

  const pricingStrategy =
    typeof opportunity.pricing_strategy === "object" && opportunity.pricing_strategy !== null
      ? opportunity.pricing_strategy
      : undefined;

  return (
    <div className={cn("border rounded-lg bg-card p-6 space-y-6", className)}>
      {/* Header with opportunity score */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-lg">Opportunity Blueprint</h3>
          <p className="text-xs text-muted-foreground mt-1">
            AI-generated strategy to beat this competitor
          </p>
        </div>
        {opportunity.estimated_opportunity_score !== undefined && (
          <OpportunityScoreBadge score={opportunity.estimated_opportunity_score} />
        )}
      </div>

      {/* Target Audience */}
      {opportunity.target_audience && (
        <div>
          <h4 className="text-sm font-medium mb-2">Target Audience</h4>
          <p className="text-sm text-muted-foreground">{opportunity.target_audience}</p>
        </div>
      )}

      {/* Title Suggestions */}
      {opportunity.title_suggestions && opportunity.title_suggestions.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Title Suggestions</h4>
          <ul className="space-y-1">
            {opportunity.title_suggestions.map((title, idx) => (
              <li key={idx} className="text-sm p-2 rounded bg-muted/50">
                {title}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Content Strategy */}
      {contentStrategy && (
        <div>
          <h4 className="text-sm font-medium mb-2">Content Strategy</h4>
          <div className="space-y-3">
            {contentStrategy.key_topics && contentStrategy.key_topics.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Key Topics</div>
                <div className="flex flex-wrap gap-1">
                  {contentStrategy.key_topics.map((topic, idx) => (
                    <Badge key={idx} variant="outline" className="bg-blue-50 text-blue-700">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {contentStrategy.unique_angles && contentStrategy.unique_angles.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Unique Angles</div>
                <ul className="space-y-1">
                  {contentStrategy.unique_angles.map((angle, idx) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <span className="text-green-600 mt-0.5">•</span>
                      <span>{angle}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 text-sm">
              {contentStrategy.depth_level && (
                <div className="p-2 rounded bg-muted/50">
                  <div className="text-xs text-muted-foreground">Depth Level</div>
                  <div className="font-medium capitalize">{contentStrategy.depth_level}</div>
                </div>
              )}
              {contentStrategy.suggested_length && (
                <div className="p-2 rounded bg-muted/50">
                  <div className="text-xs text-muted-foreground">Suggested Length</div>
                  <div className="font-medium">{contentStrategy.suggested_length}</div>
                </div>
              )}
            </div>
            {contentStrategy.structure_notes && (
              <div className="p-2 rounded bg-muted/50 text-sm">
                <div className="text-xs text-muted-foreground mb-1">Structure Notes</div>
                <div>{contentStrategy.structure_notes}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Format Recommendations */}
      {opportunity.format_recommendations && opportunity.format_recommendations.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Format Recommendations</h4>
          <ul className="space-y-1">
            {opportunity.format_recommendations.map((format, idx) => (
              <li key={idx} className="text-sm flex items-start gap-2">
                <span className="text-purple-600 mt-0.5">✓</span>
                <span>{format}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pricing Strategy */}
      {pricingStrategy && (
        <div>
          <h4 className="text-sm font-medium mb-2">Pricing Strategy</h4>
          <div className="space-y-2">
            {pricingStrategy.recommended_price !== undefined && (
              <div className="p-3 rounded bg-green-50 border border-green-200">
                <div className="text-xs text-muted-foreground mb-1">Recommended Price</div>
                <div className="text-xl font-bold text-green-700">
                  ${pricingStrategy.recommended_price.toFixed(2)}
                </div>
                {(pricingStrategy.price_range_low !== undefined || pricingStrategy.price_range_high !== undefined) && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Range: ${pricingStrategy.price_range_low?.toFixed(2) ?? "N/A"} - $
                    {pricingStrategy.price_range_high?.toFixed(2) ?? "N/A"}
                  </div>
                )}
              </div>
            )}
            {pricingStrategy.rationale && (
              <p className="text-sm text-muted-foreground">{pricingStrategy.rationale}</p>
            )}
            {pricingStrategy.bundle_suggestions && pricingStrategy.bundle_suggestions.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Bundle Suggestions</div>
                <ul className="space-y-1">
                  {pricingStrategy.bundle_suggestions.map((bundle, idx) => (
                    <li key={idx} className="text-sm">
                      • {bundle}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Differentiators */}
      {opportunity.differentiators && opportunity.differentiators.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Key Differentiators</h4>
          <ul className="space-y-1">
            {opportunity.differentiators.map((diff, idx) => (
              <li key={idx} className="text-sm flex items-start gap-2">
                <span className="text-orange-600 mt-0.5">★</span>
                <span>{diff}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

function OpportunityScoreBadge({ score }: { score: number }) {
  const rounded = Math.round(score);
  const color =
    rounded >= 70 ? "bg-green-100 text-green-700 border-green-200" :
    rounded >= 40 ? "bg-yellow-100 text-yellow-700 border-yellow-200" :
    "bg-red-100 text-red-700 border-red-200";

  return (
    <div className={cn("px-4 py-2 rounded-lg border-2 text-center", color)}>
      <div className="text-2xl font-bold">{rounded}</div>
      <div className="text-xs font-medium">Opportunity Score</div>
    </div>
  );
}
