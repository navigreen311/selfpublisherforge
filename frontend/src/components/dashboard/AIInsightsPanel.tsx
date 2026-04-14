"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Lightbulb, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { useDashboardAggregate } from "@/modules/dashboard/hooks";

const PRIORITY_STYLES: Record<
  string,
  { icon: React.ComponentType<{ className?: string }>; className: string }
> = {
  warning: { icon: AlertTriangle, className: "text-amber-600 bg-amber-50" },
  success: { icon: CheckCircle2, className: "text-green-600 bg-green-50" },
  info: { icon: Info, className: "text-blue-600 bg-blue-50" },
};

/**
 * AIInsightsPanel -- renders AI-surfaced insights from GET /api/v1/dashboard.
 * Phase 2.1 widget.
 */
export function AIInsightsPanel() {
  const { data, isLoading, isError, refetch } = useDashboardAggregate();
  const insights = data?.ai_insights ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base sm:text-lg flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-amber-500" />
          AI Insights
        </CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          Proactive recommendations for your portfolio
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : isError ? (
          <ErrorState
            message="Could not load AI insights."
            onRetry={() => refetch()}
          />
        ) : insights.length === 0 ? (
          <EmptyState
            icon={<Lightbulb />}
            title="No insights yet"
            description="As you publish and track performance, the system will surface recommendations here."
          />
        ) : (
          <ul className="space-y-2">
            {insights.map((insight) => {
              const style =
                PRIORITY_STYLES[insight.priority] ?? PRIORITY_STYLES.info;
              const Icon = style.icon;
              const body = (
                <div
                  className={`flex items-start gap-3 rounded-lg p-3 ${style.className}`}
                >
                  <Icon className="h-4 w-4 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">
                      {insight.type.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm font-medium">{insight.message}</p>
                  </div>
                </div>
              );
              return (
                <li key={insight.id}>
                  {insight.action_url ? (
                    <Link href={insight.action_url} className="block">
                      {body}
                    </Link>
                  ) : (
                    body
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default AIInsightsPanel;
