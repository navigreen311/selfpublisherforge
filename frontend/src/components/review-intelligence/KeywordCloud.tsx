"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { useTranslations } from "@/hooks/use-translations";

interface Keyword {
  text: string;
  value: number;
  sentiment: "positive" | "negative" | "neutral";
}

interface KeywordCloudProps {
  keywords: Keyword[];
  maxKeywords?: number;
}

const SENTIMENT_COLORS: Record<Keyword["sentiment"], string> = {
  positive: "text-green-600",
  negative: "text-red-600",
  neutral: "text-gray-500",
};

function getFontSize(value: number, min: number, max: number): number {
  if (max === min) return 24;
  const scale = (value - min) / (max - min);
  return Math.round(12 + scale * (36 - 12));
}

function getFontWeight(value: number, min: number, max: number): number {
  if (max === min) return 500;
  const scale = (value - min) / (max - min);
  // Map to font-weight range: 400 (normal) to 800 (extra-bold)
  return Math.round(400 + scale * 400);
}

export function KeywordCloud({
  keywords,
  maxKeywords = 30,
}: KeywordCloudProps) {
  const t = useTranslations("reviews");

  const visible = keywords.slice(0, maxKeywords);

  const values = visible.map((k) => k.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">
          {t("insights.keywordCloud")}
        </CardTitle>
      </CardHeader>

      <CardContent>
        {visible.length > 0 ? (
          <div className="flex flex-wrap items-center justify-center gap-2">
            {visible.map((keyword) => (
              <span
                key={keyword.text}
                className={`inline-block cursor-default transition-opacity hover:opacity-80 ${SENTIMENT_COLORS[keyword.sentiment]}`}
                style={{
                  fontSize: getFontSize(keyword.value, minValue, maxValue),
                  fontWeight: getFontWeight(keyword.value, minValue, maxValue),
                }}
                title={`${keyword.text}: ${keyword.value}`}
              >
                {keyword.text}
              </span>
            ))}
          </div>
        ) : (
          <div className="flex h-[200px] items-center justify-center">
            <p className="text-sm text-muted-foreground">
              {t("insights.keywordCloud")} &mdash; No data available
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
