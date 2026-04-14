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
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Workflow } from "lucide-react";
import { useDashboardAggregate } from "@/modules/dashboard/hooks";

/**
 * ActivePipelinesPanel -- shows projects currently in-progress with stage
 * and progress bar. Sourced from GET /api/v1/dashboard.active_pipelines.
 */
export function ActivePipelinesPanel() {
  const { data, isLoading, isError, refetch } = useDashboardAggregate();
  const pipelines = data?.active_pipelines ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base sm:text-lg flex items-center gap-2">
          <Workflow className="h-4 w-4" />
          Active Pipelines
        </CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          Projects currently being produced
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : isError ? (
          <ErrorState
            message="Could not load active pipelines."
            onRetry={() => refetch()}
          />
        ) : pipelines.length === 0 ? (
          <EmptyState
            icon={<Workflow />}
            title="No active pipelines"
            description="Start a new project to see it here."
            actionLabel="New Project"
            onAction={() => {
              if (typeof window !== "undefined") {
                window.location.href = "/projects/new";
              }
            }}
          />
        ) : (
          <ul className="space-y-4">
            {pipelines.map((p) => (
              <li key={p.id}>
                <Link
                  href={`/projects/${p.id}`}
                  className="block space-y-1.5 hover:bg-muted/40 rounded-md p-2 -m-2 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium truncate">{p.title}</p>
                    {p.stage && (
                      <Badge variant="secondary" className="text-[10px] shrink-0 capitalize">
                        {p.stage.replace(/_/g, " ")}
                      </Badge>
                    )}
                  </div>
                  <Progress value={p.progress_pct ?? 0} className="h-1.5" />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>{p.progress_pct ?? 0}% complete</span>
                    {p.due_date && (
                      <span>
                        Due {new Date(p.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default ActivePipelinesPanel;
