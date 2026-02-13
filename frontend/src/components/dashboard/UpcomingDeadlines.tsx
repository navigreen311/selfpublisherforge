"use client";

import Link from "next/link";
import { Calendar } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

interface DeadlineItem {
  id: string;
  title: string;
  targetDate: string; // ISO date string
}

interface UpcomingDeadlinesProps {
  deadlines?: DeadlineItem[];
}

function getDaysRemaining(targetDate: string): number {
  const now = new Date();
  const target = new Date(targetDate);
  // Strip time portion for accurate day calculation
  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const targetDateOnly = new Date(
    target.getFullYear(),
    target.getMonth(),
    target.getDate()
  );
  const diffMs = targetDateOnly.getTime() - nowDate.getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

function getDeadlineStyle(daysRemaining: number): string {
  if (daysRemaining < 0) {
    return "bg-red-100 text-red-700";
  }
  if (daysRemaining <= 7) {
    return "bg-yellow-100 text-yellow-700";
  }
  return "bg-green-100 text-green-700";
}

export function UpcomingDeadlines({ deadlines = [] }: UpcomingDeadlinesProps) {
  const t = useTranslations("dashboard");

  // Sort by target date ascending and take top 5
  const sortedDeadlines = [...deadlines]
    .sort(
      (a, b) =>
        new Date(a.targetDate).getTime() - new Date(b.targetDate).getTime()
    )
    .slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Calendar className="h-5 w-5" aria-hidden="true" />
          {t("upcomingDeadlines.title")}
        </CardTitle>
        <CardDescription>{t("upcomingDeadlines.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent>
        {sortedDeadlines.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("upcomingDeadlines.noDeadlines")}
          </p>
        ) : (
          <div className="space-y-3">
            {sortedDeadlines.map((deadline) => {
              const daysRemaining = getDaysRemaining(deadline.targetDate);
              const style = getDeadlineStyle(daysRemaining);

              let label: string;
              if (daysRemaining < 0) {
                label = t("upcomingDeadlines.overdue");
              } else if (daysRemaining === 0) {
                label = t("upcomingDeadlines.dueToday");
              } else {
                label = t("upcomingDeadlines.daysLeft", {
                  count: daysRemaining,
                });
              }

              return (
                <div
                  key={deadline.id}
                  className="flex items-center justify-between gap-3"
                >
                  <Link
                    href={`/projects/${deadline.id}`}
                    className="truncate text-sm font-medium text-foreground hover:underline"
                  >
                    {deadline.title}
                  </Link>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
                  >
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
