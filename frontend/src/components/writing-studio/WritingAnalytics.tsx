"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useTranslations } from "@/hooks/use-translations";
import { useWritingAnalytics } from "@/modules/writing/hooks";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Period options mapped to API parameter values
// ---------------------------------------------------------------------------

const PERIOD_OPTIONS = [
  { value: "7d", labelKey: "analytics.thisWeek" },
  { value: "30d", labelKey: "analytics.thisMonth" },
  { value: "90d", labelKey: "analytics.last3Months" },
  { value: "all", labelKey: "analytics.allTime" },
] as const;

const DEFAULT_DAILY_GOAL = 1500;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface WritingAnalyticsProps {
  className?: string;
}

// ---------------------------------------------------------------------------
// Skeleton sub-components
// ---------------------------------------------------------------------------

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16" />
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-64 w-full" />
      </CardContent>
    </Card>
  );
}

function SessionTableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Helper: format duration from minutes
// ---------------------------------------------------------------------------

function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

// ---------------------------------------------------------------------------
// Period Selector sub-component
// ---------------------------------------------------------------------------

function PeriodSelector({
  period,
  onChange,
  t,
}: {
  period: string;
  onChange: (value: string) => void;
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <Select value={period} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder={t("analytics.selectPeriod")} />
      </SelectTrigger>
      <SelectContent>
        {PERIOD_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {t(opt.labelKey)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function WritingAnalytics({ className }: WritingAnalyticsProps) {
  const t = useTranslations("writing");
  const [period, setPeriod] = useState<string>("30d");

  const { data, isLoading, isError } = useWritingAnalytics(period);

  // ---- Loading state ----
  if (isLoading) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <ChartSkeleton />
        <ChartSkeleton />
        <SessionTableSkeleton />
      </div>
    );
  }

  // ---- Error state ----
  if (isError) {
    return (
      <div className={cn("space-y-6", className)}>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-destructive">
              {t("analytics.error")}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ---- Empty state ----
  if (!data || (data.total_words === 0 && data.sessions_count === 0)) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold tracking-tight">
            {t("analytics.title")}
          </h2>
          <PeriodSelector period={period} onChange={setPeriod} t={t} />
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <p className="text-sm text-muted-foreground max-w-sm">
              {t("analytics.empty")}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ---- Data present ----
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header + Period Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">
          {t("analytics.title")}
        </h2>
        <PeriodSelector period={period} onChange={setPeriod} t={t} />
      </div>

      {/* Stat cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Words */}
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">
              {t("analytics.totalWords")}
            </p>
            <p className="text-3xl font-bold mt-1">
              {data.total_words.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        {/* Sessions */}
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">
              {t("analytics.sessions")}
            </p>
            <p className="text-3xl font-bold mt-1">
              {data.sessions_count.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        {/* Avg WPM */}
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">
              {t("analytics.avgWpm")}
            </p>
            <p className="text-3xl font-bold mt-1">
              {data.avg_wpm.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        {/* Streak */}
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">
              {t("analytics.streak")}
            </p>
            <p className="text-3xl font-bold mt-1">
              <span aria-hidden="true">{"\uD83D\uDD25"}</span>{" "}
              {data.streak} {t("analytics.days")}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Daily Word Count bar chart */}
      {data.daily_data.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">
              {t("analytics.dailyWordCount")}
            </h3>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.daily_data}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value: string) => {
                    const d = new Date(value);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                  }}
                />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  labelFormatter={(value: string) => {
                    const d = new Date(value);
                    return d.toLocaleDateString();
                  }}
                  formatter={(value: number) => [
                    value.toLocaleString(),
                    t("analytics.words"),
                  ]}
                />
                <ReferenceLine
                  y={DEFAULT_DAILY_GOAL}
                  stroke="#94a3b8"
                  strokeDasharray="6 4"
                  label={{
                    value: `${t("analytics.dailyGoal")} (${DEFAULT_DAILY_GOAL.toLocaleString()})`,
                    position: "insideTopRight",
                    fontSize: 11,
                    fill: "#94a3b8",
                  }}
                />
                <Bar
                  dataKey="words"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* By Manuscript breakdown */}
      {data.by_manuscript.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">
              {t("analytics.byManuscript")}
            </h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.by_manuscript.map((ms) => (
              <div key={ms.manuscript_id} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium truncate mr-4">{ms.title}</span>
                  <span className="text-muted-foreground whitespace-nowrap">
                    {ms.words.toLocaleString()} {t("analytics.words")} ({ms.pct}%)
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-muted">
                  <div
                    className="h-2.5 rounded-full bg-primary transition-all duration-300"
                    style={{ width: `${Math.max(ms.pct, 1)}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Session Log table */}
      {data.session_log.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">
              {t("analytics.sessionLog")}
            </h3>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("analytics.date")}</TableHead>
                  <TableHead>{t("analytics.manuscript")}</TableHead>
                  <TableHead>{t("analytics.chapter")}</TableHead>
                  <TableHead className="text-right">
                    {t("analytics.words")}
                  </TableHead>
                  <TableHead className="text-right">
                    {t("analytics.duration")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.session_log.map((session) => (
                  <TableRow key={session.id}>
                    <TableCell>
                      {new Date(session.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{session.book_title ?? "-"}</TableCell>
                    <TableCell>{session.chapter_title ?? "-"}</TableCell>
                    <TableCell className="text-right">
                      {session.words_written.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatDuration(session.duration_minutes)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
