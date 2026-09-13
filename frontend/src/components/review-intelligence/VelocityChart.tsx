"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
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
import { useTranslations } from "@/hooks/use-translations";

interface VelocityDataPoint {
  week: string;
  yours: number;
  genre_avg: number;
}

interface VelocityChartProps {
  data: VelocityDataPoint[];
  title?: string;
}

export function VelocityChart({ data, title }: VelocityChartProps) {
  const t = useTranslations("reviews");

  const chartTitle = title ?? t("insights.velocityChart");
  const hasData = data && data.length > 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{chartTitle}</CardTitle>
      </CardHeader>

      <CardContent>
        {hasData ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                dataKey="week"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
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
                dataKey="yours"
                name={t("insights.yourBooks")}
                stroke="#3b82f6"
                strokeWidth={2}
                fill="#3b82f6"
                fillOpacity={0.1}
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
              {chartTitle} &mdash; No data available
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
