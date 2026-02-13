"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import type { WeaknessSignalGroup } from "@/modules/competitors/hooks";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronRight } from "lucide-react";

// ---------------------------------------------------------------------------
// Category configuration
// ---------------------------------------------------------------------------

type PriorityLevel = "critical" | "moderate" | "lower";

interface CategoryConfig {
  priority: PriorityLevel;
  translationKey: string;
}

const CATEGORY_CONFIG: Record<string, CategoryConfig> = {
  content_depth: { priority: "critical", translationKey: "gap.contentDepthGaps" },
  missing_deliverables: { priority: "critical", translationKey: "gap.missingDeliverables" },
  practical_gaps: { priority: "moderate", translationKey: "gap.practicalGaps" },
  production_quality: { priority: "moderate", translationKey: "gap.productionQuality" },
  voice_mismatch: { priority: "moderate", translationKey: "gap.voiceMismatch" },
  currency_gaps: { priority: "lower", translationKey: "gap.currencyGaps" },
  value_perception: { priority: "lower", translationKey: "gap.valuePerception" },
  promise_delivery: { priority: "lower", translationKey: "gap.promiseDelivery" },
};

const PRIORITY_STYLES: Record<PriorityLevel, { dot: string; border: string; bg: string }> = {
  critical: {
    dot: "bg-red-500",
    border: "border-red-200",
    bg: "bg-red-50",
  },
  moderate: {
    dot: "bg-yellow-500",
    border: "border-yellow-200",
    bg: "bg-yellow-50",
  },
  lower: {
    dot: "bg-green-500",
    border: "border-green-200",
    bg: "bg-green-50",
  },
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface WeaknessSignalsProps {
  signals: WeaknessSignalGroup[];
  totalSignals: number;
  bookCount: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WeaknessSignals({
  signals,
  totalSignals,
  bookCount,
}: WeaknessSignalsProps) {
  const t = useTranslations("competitors");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  // Sort signals by priority: critical first, then moderate, then lower
  const priorityOrder: PriorityLevel[] = ["critical", "moderate", "lower"];
  const sortedSignals = [...signals].sort((a, b) => {
    const aPriority = CATEGORY_CONFIG[a.category]?.priority ?? "lower";
    const bPriority = CATEGORY_CONFIG[b.category]?.priority ?? "lower";
    return priorityOrder.indexOf(aPriority) - priorityOrder.indexOf(bPriority);
  });

  return (
    <div className="border rounded-lg bg-card">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h3 className="font-semibold text-lg">{t("gap.weaknessSignals")}</h3>
          <p className="text-sm text-muted-foreground mt-0.5">
            {totalSignals} {t("gap.signals")} {t("gap.from")} {bookCount} {t("gap.books")}
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
            Critical
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500" />
            Moderate
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" />
            Lower
          </span>
        </div>
      </div>

      {/* Category sections */}
      <div className="divide-y">
        {sortedSignals.map((group) => {
          const config = CATEGORY_CONFIG[group.category];
          const priority = config?.priority ?? "lower";
          const styles = PRIORITY_STYLES[priority];
          const isExpanded = expandedCategories.has(group.category);
          const categoryLabel = config
            ? t(config.translationKey)
            : group.label;

          return (
            <div key={group.category}>
              {/* Collapsible header */}
              <button
                type="button"
                onClick={() => toggleCategory(group.category)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors"
              >
                {/* Priority dot */}
                <span
                  className={`inline-block h-3 w-3 flex-shrink-0 rounded-full ${styles.dot}`}
                />

                {/* Category label */}
                <span className="flex-1 font-medium text-sm">{categoryLabel}</span>

                {/* Signal count badge */}
                <Badge
                  variant="outline"
                  className={`${styles.bg} ${styles.border} text-xs`}
                >
                  {group.count} {t("gap.signals")}
                </Badge>

                {/* Expand/collapse icon */}
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                )}
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-4 pb-4 pl-10 space-y-3">
                  {/* Signal texts */}
                  <ul className="space-y-2">
                    {group.signals.map((signal, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-sm text-muted-foreground"
                      >
                        <span className={`mt-1.5 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full ${styles.dot}`} />
                        <span>{signal}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Book sources */}
                  {group.book_sources && group.book_sources.length > 0 && (
                    <div className="text-xs text-muted-foreground pt-1 border-t">
                      <span className="font-medium">{t("gap.foundIn")}:</span>{" "}
                      {group.book_sources.join(", ")}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
