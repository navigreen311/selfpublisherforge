"use client";

import Link from "next/link";
import { Bot, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface AgentTask {
  id: string;
  type: string;
  description: string;
  status: "running" | "completed" | "failed";
  progress?: number;
  completedAt?: string;
}

interface AgentActivityFeedProps {
  tasks?: AgentTask[];
}

function getRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  return `${diffDays}d ago`;
}

function StatusIcon({ status }: { status: AgentTask["status"] }) {
  switch (status) {
    case "completed":
      return (
        <CheckCircle2
          className="h-4 w-4 shrink-0 text-green-600"
          aria-hidden="true"
        />
      );
    case "running":
      return (
        <Loader2
          className="h-4 w-4 shrink-0 animate-spin text-blue-600"
          aria-hidden="true"
        />
      );
    case "failed":
      return (
        <XCircle
          className="h-4 w-4 shrink-0 text-red-600"
          aria-hidden="true"
        />
      );
  }
}

export function AgentActivityFeed({ tasks = [] }: AgentActivityFeedProps) {
  const t = useTranslations("dashboard");

  // Show last 5 tasks
  const recentTasks = tasks.slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Bot className="h-5 w-5" aria-hidden="true" />
          {t("agentActivity.title")}
        </CardTitle>
        <CardDescription>{t("agentActivity.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {recentTasks.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("agentActivity.noActivity")}
          </p>
        ) : (
          <div className="space-y-3">
            {recentTasks.map((task) => (
              <div key={task.id} className="flex items-start gap-3">
                <div className="mt-0.5">
                  <StatusIcon status={task.status} />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-foreground">
                      {task.description}
                    </p>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {task.status === "running"
                        ? t("agentActivity.running")
                        : task.status === "failed"
                          ? t("agentActivity.failed")
                          : task.completedAt
                            ? getRelativeTime(task.completedAt)
                            : t("agentActivity.completed")}
                    </span>
                  </div>
                  {task.status === "running" &&
                    task.progress != null &&
                    task.progress >= 0 && (
                      <div className="space-y-1">
                        <div
                          className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
                          role="progressbar"
                          aria-valuenow={task.progress}
                          aria-valuemin={0}
                          aria-valuemax={100}
                        >
                          <div
                            className="h-full rounded-full bg-blue-600 transition-all duration-300"
                            style={{ width: `${Math.min(task.progress, 100)}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {task.progress}%
                        </p>
                      </div>
                    )}
                  <p className="text-xs text-muted-foreground">{task.type}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <Button variant="outline" size="sm" className="w-full" asChild>
          <Link href="/agents">{t("agentActivity.viewAll")}</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
