"use client";

import { useTranslations } from "@/hooks/use-translations";
import type { OpportunityBlueprint } from "@/modules/competitors/hooks";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Download, FolderPlus, ArrowRight, CheckCircle2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OpportunityBlueprintCardProps {
  blueprint: OpportunityBlueprint;
  differentiationScore?: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OpportunityBlueprintCard({
  blueprint,
  differentiationScore,
}: OpportunityBlueprintCardProps) {
  const t = useTranslations("competitors");

  const score = differentiationScore ?? blueprint.differentiation_score ?? 0;
  const actionItems = blueprint.action_items ?? [];

  // Determine the score color based on value
  const scoreColor =
    score >= 70
      ? "text-green-600"
      : score >= 40
        ? "text-yellow-600"
        : "text-red-600";

  const scoreBg =
    score >= 70
      ? "bg-green-50 border-green-200"
      : score >= 40
        ? "bg-yellow-50 border-yellow-200"
        : "bg-red-50 border-red-200";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t("gap.opportunityBlueprint")}</CardTitle>
        <CardDescription>{t("gap.blueprintIntro")}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Action items checklist */}
        {actionItems.length > 0 && (
          <ul className="space-y-3">
            {actionItems.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-500 mt-0.5" />
                <span className="text-sm">{item}</span>
              </li>
            ))}
          </ul>
        )}

        {/* Differentiation Score */}
        <div className={`rounded-lg border p-4 ${scoreBg}`}>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${scoreColor}`}>
              {score}/100
            </span>
            <span className="text-sm font-medium">{t("gap.differentiationScore")}</span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {t("gap.differentiationDesc", {
              score: String(score),
            })}
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex flex-wrap items-center gap-3 border-t pt-6">
        <Button variant="outline" size="sm">
          <Download className="mr-2 h-4 w-4" />
          {t("gap.exportBlueprint")}
        </Button>
        <Button variant="outline" size="sm">
          <FolderPlus className="mr-2 h-4 w-4" />
          {t("gap.addToProjectBrief")}
        </Button>
        <Button size="sm" className="ml-auto">
          {t("gap.startWriting")}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
