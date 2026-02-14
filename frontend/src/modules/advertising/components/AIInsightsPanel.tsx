"use client";

import { Lightbulb, AlertTriangle, TrendingUp, Target } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AIInsight } from "../types";

interface AIInsightsPanelProps {
  insights: AIInsight[];
}

function getIcon(type: AIInsight["type"]) {
  switch (type) {
    case "opportunity":
      return Lightbulb;
    case "warning":
      return AlertTriangle;
    case "performance":
      return TrendingUp;
    case "budget":
      return Target;
    case "keyword":
      return Lightbulb;
    default:
      return Lightbulb;
  }
}

function getSeverityStyles(severity: AIInsight["severity"]) {
  switch (severity) {
    case "info":
      return {
        bg: "bg-blue-50 dark:bg-blue-950/30",
        border: "border-blue-200 dark:border-blue-800",
        icon: "text-blue-600 dark:text-blue-400",
      };
    case "warning":
      return {
        bg: "bg-amber-50 dark:bg-amber-950/30",
        border: "border-amber-200 dark:border-amber-800",
        icon: "text-amber-600 dark:text-amber-400",
      };
    case "success":
      return {
        bg: "bg-green-50 dark:bg-green-950/30",
        border: "border-green-200 dark:border-green-800",
        icon: "text-green-600 dark:text-green-400",
      };
    default:
      return {
        bg: "bg-muted/10",
        border: "border-border",
        icon: "text-muted-foreground",
      };
  }
}

export function AIInsightsPanel({ insights }: AIInsightsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">AI Insights</CardTitle>
      </CardHeader>
      <CardContent>
        {insights.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-center text-muted-foreground text-sm">
            <p>
              No insights available yet. Run campaigns to get AI
              recommendations.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {insights.map((insight, index) => {
              const Icon = getIcon(insight.type);
              const styles = getSeverityStyles(insight.severity);

              return (
                <div
                  key={index}
                  className={`flex gap-3 p-3 rounded-lg border ${styles.bg} ${styles.border}`}
                >
                  <div className={`mt-0.5 shrink-0 ${styles.icon}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-relaxed">{insight.message}</p>
                    {insight.action && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Suggested action: {insight.action}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
