"use client";

import { useTranslations } from "@/hooks/use-translations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Pencil } from "lucide-react";

interface WritingProgressProps {
  wordsToday?: number;
  dailyGoal?: number;
  streak?: number;
  weeklyTotal?: number;
  dailyData?: { date: string; words: number }[];
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function WritingProgress({
  wordsToday = 0,
  dailyGoal = 1000,
  streak = 0,
  weeklyTotal = 0,
  dailyData = [],
}: WritingProgressProps) {
  const t = useTranslations("dashboard");

  const percentage = dailyGoal > 0 ? Math.min(Math.round((wordsToday / dailyGoal) * 100), 100) : 0;

  const maxWords = dailyData.length > 0
    ? Math.max(...dailyData.map((d) => d.words), 1)
    : 1;

  const hasData = dailyGoal > 0 && (wordsToday > 0 || weeklyTotal > 0 || dailyData.length > 0);

  if (!hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("writingProgress.title")}</CardTitle>
          <CardDescription>{t("writingProgress.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t("writingProgress.noGoal")}
          </p>
          <Button variant="outline" size="sm" className="mt-4">
            <Pencil className="mr-2 h-4 w-4" />
            {t("writingProgress.setGoal")}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("writingProgress.title")}</CardTitle>
        <CardDescription>{t("writingProgress.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Today's progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>
              {t("writingProgress.wordsToday")}:{" "}
              <span className="font-semibold">
                {wordsToday.toLocaleString()} / {dailyGoal.toLocaleString()}
              </span>
            </span>
            <span className="text-muted-foreground">{percentage}%</span>
          </div>
          <div className="h-2.5 rounded-full bg-muted" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
            <div
              className="h-2.5 rounded-full bg-primary transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-1.5">
            <span aria-hidden="true">🔥</span>
            <span className="font-semibold">{streak}-day {t("writingProgress.streak").toLowerCase()}</span>
          </div>
          <div>
            {t("writingProgress.weeklyTotal")}:{" "}
            <span className="font-semibold">{weeklyTotal.toLocaleString()}</span>
          </div>
        </div>

        {/* Mini bar chart */}
        <div className="space-y-1">
          <div className="flex items-end gap-1" style={{ height: "64px" }}>
            {DAY_LABELS.map((day, index) => {
              const dayEntry = dailyData[index];
              const words = dayEntry ? dayEntry.words : 0;
              const heightPercent = maxWords > 0 ? (words / maxWords) * 100 : 0;

              return (
                <div
                  key={day}
                  className="w-full min-h-[4px] rounded-t bg-primary/70 transition-all duration-300"
                  style={{ height: `${Math.max(heightPercent, 4)}%` }}
                  title={`${day}: ${words.toLocaleString()} words`}
                  role="img"
                  aria-label={`${day}: ${words.toLocaleString()} words`}
                />
              );
            })}
          </div>
          <div className="flex gap-1">
            {DAY_LABELS.map((day) => (
              <span
                key={day}
                className="w-full text-center text-xs text-muted-foreground"
              >
                {day}
              </span>
            ))}
          </div>
        </div>

        {/* Set Goal button */}
        <Button variant="outline" size="sm">
          <Pencil className="mr-2 h-4 w-4" />
          {t("writingProgress.setGoal")}
        </Button>
      </CardContent>
    </Card>
  );
}
