"use client";

import { useEffect, useCallback } from "react";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/hooks/use-translations";
import {
  useAIMarketSummary,
  type NicheAnalysisResponse,
  type AIMarketSummaryData,
} from "@/modules/market/hooks";

interface AIMarketSummaryProps {
  nicheData: NicheAnalysisResponse;
  onExportToProject?: () => void;
  onStartWriting?: () => void;
}

function SkeletonLoader({ message }: { message: string }) {
  return (
    <div className="space-y-4 animate-pulse">
      <p className="text-sm text-muted-foreground">{message}</p>
      <div className="space-y-3">
        <div className="h-4 bg-muted rounded w-full" />
        <div className="h-4 bg-muted rounded w-5/6" />
        <div className="h-4 bg-muted rounded w-4/6" />
      </div>
      <div className="space-y-3 pt-2">
        <div className="h-4 bg-muted rounded w-full" />
        <div className="h-4 bg-muted rounded w-3/4" />
      </div>
      <div className="space-y-2 pt-2">
        <div className="h-3 bg-muted rounded w-2/3" />
        <div className="h-3 bg-muted rounded w-1/2" />
        <div className="h-3 bg-muted rounded w-3/5" />
      </div>
    </div>
  );
}

function SummaryContent({
  data,
  t,
}: {
  data: AIMarketSummaryData;
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <div className="space-y-6">
      {/* Market Overview */}
      <section>
        <h4 className="font-medium text-sm mb-2">{t("ai.marketOverview")}</h4>
        <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
          {data.summary}
        </div>
      </section>

      {/* Content Gaps Identified */}
      {data.content_gaps.length > 0 && (
        <section>
          <h4 className="font-medium text-sm mb-2">{t("ai.contentGaps")}</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            {data.content_gaps.map((gap, idx) => (
              <li key={idx}>{gap}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Recommended Positioning */}
      {data.positioning && (
        <section>
          <h4 className="font-medium text-sm mb-2">{t("ai.positioning")}</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {data.positioning}
          </p>
        </section>
      )}
    </div>
  );
}

function FallbackContent({
  text,
  label,
}: {
  text: string;
  label: string;
}) {
  return (
    <section>
      <h4 className="font-medium text-sm mb-2">{label}</h4>
      <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
        {text}
      </p>
    </section>
  );
}

export function AIMarketSummary({
  nicheData,
  onExportToProject,
  onStartWriting,
}: AIMarketSummaryProps) {
  const t = useTranslations("market");
  const mutation = useAIMarketSummary();

  const generate = useCallback(() => {
    mutation.mutate({ niche_data: nicheData });
  }, [nicheData]); // eslint-disable-line react-hooks/exhaustive-deps

  // Trigger AI summary generation on mount or when nicheData changes
  useEffect(() => {
    generate();
  }, [generate]);

  const aiData = mutation.data;
  const isLoading = mutation.isPending;
  const isError = mutation.isError;

  // Determine what content to show
  const hasAIData = !!aiData;
  const hasFallbackAISummary = !!nicheData.ai_summary;
  const hasFallbackRecommendation = !!nicheData.recommendation;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <h3 className="text-lg font-semibold">{t("ai.title")}</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={generate}
          disabled={isLoading}
        >
          {isLoading ? t("ai.regenerating") : t("ai.regenerate")}
        </Button>
      </CardHeader>

      <CardContent>
        {isLoading && (
          <SkeletonLoader message={t("ai.loading")} />
        )}

        {!isLoading && isError && (
          <div className="space-y-4">
            {hasFallbackAISummary ? (
              <FallbackContent
                text={nicheData.ai_summary!}
                label={t("ai.marketOverview")}
              />
            ) : hasFallbackRecommendation ? (
              <FallbackContent
                text={nicheData.recommendation}
                label={t("ai.marketOverview")}
              />
            ) : (
              <p className="text-sm text-destructive">
                {mutation.error?.message ?? "Failed to generate AI analysis."}
              </p>
            )}
          </div>
        )}

        {!isLoading && !isError && hasAIData && (
          <SummaryContent data={aiData} t={t} />
        )}

        {!isLoading && !isError && !hasAIData && (
          <div className="space-y-4">
            {hasFallbackAISummary ? (
              <FallbackContent
                text={nicheData.ai_summary!}
                label={t("ai.marketOverview")}
              />
            ) : hasFallbackRecommendation ? (
              <FallbackContent
                text={nicheData.recommendation}
                label={t("ai.marketOverview")}
              />
            ) : null}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={isLoading || (!hasAIData && !hasFallbackAISummary)}
        >
          {t("ai.saveAnalysis")}
        </Button>
        {onExportToProject && (
          <Button
            variant="outline"
            size="sm"
            onClick={onExportToProject}
            disabled={isLoading}
          >
            {t("results.exportToProject")}
          </Button>
        )}
        {onStartWriting && (
          <Button
            size="sm"
            onClick={onStartWriting}
            disabled={isLoading}
          >
            {t("results.startWriting")} &rarr;
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
