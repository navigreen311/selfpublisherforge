"use client";

import { TrendingUp, TrendingDown, Sparkles, PartyPopper } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface Insight {
  type: string;
  message: string;
  severity: "info" | "warning" | "success";
}

interface AnalyticsInsightsPanelProps {
  insights: Insight[];
}

const ICON_MAP: Record<string, { icon: typeof TrendingUp; className: string }> = {
  trending_up: { icon: TrendingUp, className: "text-green-600" },
  trending_down: { icon: TrendingDown, className: "text-red-600" },
  insight: { icon: Sparkles, className: "text-blue-600" },
  milestone: { icon: PartyPopper, className: "text-green-600" },
};

function getIconConfig(type: string, severity: Insight["severity"]) {
  if (ICON_MAP[type]) return ICON_MAP[type];
  // Fallback based on severity
  if (severity === "success") return { icon: TrendingUp, className: "text-green-600" };
  if (severity === "warning") return { icon: TrendingDown, className: "text-red-600" };
  return { icon: Sparkles, className: "text-blue-600" };
}

export function AnalyticsInsightsPanel({ insights }: AnalyticsInsightsPanelProps) {
  if (!insights || insights.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          AI Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => {
            const { icon: Icon, className } = getIconConfig(insight.type, insight.severity);
            return (
              <div
                key={index}
                className="flex items-start gap-3 rounded-lg border p-3 bg-muted/30"
              >
                <div className="mt-0.5 shrink-0">
                  <Icon className={`h-4 w-4 ${className}`} />
                </div>
                <p className="text-sm text-foreground leading-relaxed">
                  {insight.message}
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
