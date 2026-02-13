"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTranslations } from "@/hooks/use-translations";

interface SentimentDataPoint {
  date: string;
  sentiment_score: number;
  genre_avg: number;
}

interface SentimentTrendChartProps {
  data?: SentimentDataPoint[];
  bookFilter: string;
  onBookFilterChange: (bookId: string) => void;
  period: string;
  onPeriodChange: (period: string) => void;
}

const PERIOD_OPTIONS = [
  { value: "3mo", labelKey: "charts.range3m" },
  { value: "6mo", labelKey: "charts.range6m" },
  { value: "12mo", labelKey: "charts.range12m" },
  { value: "all", labelKey: "charts.allTime" },
] as const;

export function SentimentTrendChart({
  data,
  bookFilter,
  onBookFilterChange,
  period,
  onPeriodChange,
}: SentimentTrendChartProps) {
  const t = useTranslations("reviews");

  const hasData = data && data.length > 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">
            {t("charts.sentimentTrend")}
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Book filter dropdown */}
            <Select value={bookFilter} onValueChange={onBookFilterChange}>
              <SelectTrigger className="h-8 w-[160px] text-xs">
                <SelectValue placeholder={t("charts.filterByBook")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">
                  {t("charts.filterByBook")}
                </SelectItem>
                {/* Placeholder for book list - populated by parent */}
              </SelectContent>
            </Select>

            {/* Time range selector */}
            <div className="flex rounded-md border">
              {PERIOD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => onPeriodChange(opt.value)}
                  className={`px-2.5 py-1 text-xs font-medium transition-colors first:rounded-l-md last:rounded-r-md ${
                    period === opt.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-background text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {t(opt.labelKey)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {hasData ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  fontSize: 12,
                  borderRadius: 8,
                  border: "1px solid hsl(var(--border))",
                  backgroundColor: "hsl(var(--background))",
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                iconType="line"
                wrapperStyle={{ fontSize: 12 }}
              />
              <Line
                type="monotone"
                dataKey="sentiment_score"
                name={t("charts.yourScore")}
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 3, fill: "#3b82f6" }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="genre_avg"
                name={t("charts.genreAvg")}
                stroke="#9ca3af"
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-sm text-muted-foreground">
              {t("charts.sentimentTrend")} &mdash; No data available
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
