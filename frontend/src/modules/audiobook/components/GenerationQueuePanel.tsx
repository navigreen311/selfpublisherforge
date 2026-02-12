"use client";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Zap,
  Radio,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAudiobookWebSocket } from "../hooks";
import { useAudiobookStudioStore } from "../store";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type JobStatus = "queued" | "processing" | "completed" | "failed";

interface ChapterInput {
  id: string;
  chapter_number: number;
  chapter_title: string | null;
  status: string;
}

export interface GenerationQueuePanelProps {
  projectId: string;
  chapters: ChapterInput[];
}

interface JobEntry {
  chapterId: string;
  chapterNumber: number;
  chapterTitle: string;
  status: JobStatus;
  progress: number;
  stage: string;
  provider: string | null;
  startedAt: string | null;
  completedAt: string | null;
  costUsd: number | null;
  errorMessage: string | null;
}

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  JobStatus,
  { icon: typeof Clock; color: string; badgeClass: string; label: string }
> = {
  queued: {
    icon: Clock,
    color: "text-blue-500",
    badgeClass: "bg-blue-100 text-blue-800 border-blue-200",
    label: "Queued",
  },
  processing: {
    icon: Loader2,
    color: "text-yellow-500",
    badgeClass: "bg-yellow-100 text-yellow-800 border-yellow-200",
    label: "Processing",
  },
  completed: {
    icon: CheckCircle2,
    color: "text-green-500",
    badgeClass: "bg-green-100 text-green-800 border-green-200",
    label: "Completed",
  },
  failed: {
    icon: AlertCircle,
    color: "text-red-500",
    badgeClass: "bg-red-100 text-red-800 border-red-200",
    label: "Failed",
  },
};

const PROGRESS_COLORS: Record<JobStatus, string> = {
  queued: "[&>div]:bg-blue-500",
  processing: "[&>div]:bg-yellow-500",
  completed: "[&>div]:bg-green-500",
  failed: "[&>div]:bg-red-500",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map chapter status strings from the backend to our simplified JobStatus */
function mapStatus(status: string): JobStatus {
  switch (status) {
    case "generating":
    case "preprocessing":
    case "post_processing":
      return "processing";
    case "review":
    case "approved":
      return "completed";
    case "failed":
      return "failed";
    case "pending":
    default:
      return "queued";
  }
}

function formatElapsed(startIso: string, endIso?: string | null): string {
  const start = new Date(startIso).getTime();
  const end = endIso ? new Date(endIso).getTime() : Date.now();
  const seconds = Math.max(0, Math.round((end - start) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GenerationQueuePanel({
  projectId,
  chapters,
}: GenerationQueuePanelProps) {
  const { lastEvent, connected, send } = useAudiobookWebSocket(projectId);
  const generationProgress = useAudiobookStudioStore(
    (s) => s.generationProgress,
  );

  // Track per-job metadata from websocket events
  const [jobMeta, setJobMeta] = useState<
    Record<
      string,
      {
        provider?: string;
        startedAt?: string;
        completedAt?: string;
        costUsd?: number;
        errorMessage?: string;
      }
    >
  >({});

  const [expandedJobs, setExpandedJobs] = useState<Record<string, boolean>>({});
  const activeJobRef = useRef<HTMLDivElement | null>(null);

  // Process incoming websocket events to enrich job metadata
  useEffect(() => {
    if (!lastEvent) return;

    const event = lastEvent as Record<string, unknown>;
    const chapterId = event.chapter_id as string | undefined;
    if (!chapterId) return;

    setJobMeta((prev) => {
      const existing = prev[chapterId] ?? {};
      const updates: Record<string, unknown> = {};

      if (event.provider) updates.provider = event.provider;
      if (event.started_at) updates.startedAt = event.started_at;
      if (event.completed_at) updates.completedAt = event.completed_at;
      if (event.cost_usd != null) updates.costUsd = event.cost_usd;
      if (event.error_message) updates.errorMessage = event.error_message;

      if (
        event.type === "chapter_generation_started" &&
        !existing.startedAt
      ) {
        updates.startedAt = new Date().toISOString();
      }

      if (Object.keys(updates).length === 0) return prev;
      return { ...prev, [chapterId]: { ...existing, ...updates } };
    });
  }, [lastEvent]);

  // Build the job entries list
  const jobs: JobEntry[] = useMemo(() => {
    return chapters.map((ch) => {
      const status = mapStatus(ch.status);
      const progress = generationProgress[ch.id];
      const meta = jobMeta[ch.id];

      return {
        chapterId: ch.id,
        chapterNumber: ch.chapter_number,
        chapterTitle: ch.chapter_title ?? `Chapter ${ch.chapter_number}`,
        status,
        progress: status === "completed" ? 100 : (progress?.percent ?? 0),
        stage: progress?.stage ?? (status === "completed" ? "Done" : "Waiting"),
        provider: meta?.provider ?? null,
        startedAt: meta?.startedAt ?? null,
        completedAt: meta?.completedAt ?? null,
        costUsd: meta?.costUsd ?? null,
        errorMessage: meta?.errorMessage ?? null,
      };
    });
  }, [chapters, generationProgress, jobMeta]);

  // Summary stats
  const completedCount = jobs.filter((j) => j.status === "completed").length;
  const failedCount = jobs.filter((j) => j.status === "failed").length;
  const processingCount = jobs.filter((j) => j.status === "processing").length;
  const totalCount = jobs.length;

  // Estimate remaining time (rough average)
  const estimatedRemaining = useMemo(() => {
    const completedWithTime = jobs.filter(
      (j) => j.status === "completed" && j.startedAt && j.completedAt,
    );
    if (completedWithTime.length === 0) return null;

    const totalMs = completedWithTime.reduce((sum, j) => {
      const start = new Date(j.startedAt!).getTime();
      const end = new Date(j.completedAt!).getTime();
      return sum + (end - start);
    }, 0);
    const avgMs = totalMs / completedWithTime.length;
    const remaining = jobs.filter(
      (j) => j.status === "queued" || j.status === "processing",
    ).length;
    const totalRemaining = Math.round((avgMs * remaining) / 1000);

    if (totalRemaining < 60) return `~${totalRemaining}s remaining`;
    const mins = Math.floor(totalRemaining / 60);
    return `~${mins}m remaining`;
  }, [jobs]);

  // Auto-scroll to active job
  useEffect(() => {
    if (activeJobRef.current) {
      activeJobRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [jobs]);

  const toggleExpand = useCallback((chapterId: string) => {
    setExpandedJobs((prev) => ({
      ...prev,
      [chapterId]: !prev[chapterId],
    }));
  }, []);

  const handleCancel = useCallback(
    (chapterId: string) => {
      send({ type: "cancel_generation", chapter_id: chapterId });
    },
    [send],
  );

  const handleRetry = useCallback(
    (chapterId: string) => {
      send({ type: "retry_generation", chapter_id: chapterId });
    },
    [send],
  );

  // Find the first processing job index for auto-scroll ref
  const activeJobIndex = jobs.findIndex((j) => j.status === "processing");

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Generation Queue</CardTitle>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-block w-2 h-2 rounded-full",
                connected ? "bg-green-500 animate-pulse" : "bg-muted-foreground",
              )}
            />
            <span className="text-xs text-muted-foreground">
              {connected ? "Live" : "Disconnected"}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4 flex-1 min-h-0">
        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="border rounded-lg p-3 bg-card space-y-0.5">
            <p className="text-xs text-muted-foreground">Completed</p>
            <p className="text-lg font-bold text-green-600">
              {completedCount}
              <span className="text-sm font-normal text-muted-foreground">
                /{totalCount}
              </span>
            </p>
          </div>
          <div className="border rounded-lg p-3 bg-card space-y-0.5">
            <p className="text-xs text-muted-foreground">Processing</p>
            <p className="text-lg font-bold text-yellow-600">
              {processingCount}
            </p>
          </div>
          <div className="border rounded-lg p-3 bg-card space-y-0.5">
            <p className="text-xs text-muted-foreground">Failed</p>
            <p className="text-lg font-bold text-red-600">{failedCount}</p>
          </div>
          <div className="border rounded-lg p-3 bg-card space-y-0.5">
            <p className="text-xs text-muted-foreground">ETA</p>
            <p className="text-sm font-medium">
              {estimatedRemaining ?? "---"}
            </p>
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Overall Progress</span>
            <span>
              {totalCount > 0
                ? Math.round((completedCount / totalCount) * 100)
                : 0}
              %
            </span>
          </div>
          <Progress
            value={completedCount}
            max={totalCount || 1}
            className="h-2 [&>div]:bg-green-500"
          />
        </div>

        {/* Job list */}
        <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
          {jobs.map((job, index) => {
            const config = STATUS_CONFIG[job.status];
            const Icon = config.icon;
            const isExpanded = expandedJobs[job.chapterId] ?? false;
            const isActive = index === activeJobIndex;

            return (
              <div
                key={job.chapterId}
                ref={isActive ? activeJobRef : undefined}
                className={cn(
                  "border rounded-lg transition-colors",
                  isActive && "ring-2 ring-yellow-400/50",
                  job.status === "failed" && "border-red-200 bg-red-50/30",
                )}
              >
                {/* Job header */}
                <div className="p-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <Icon
                        className={cn(
                          "h-4 w-4 flex-shrink-0",
                          config.color,
                          job.status === "processing" && "animate-spin",
                        )}
                      />
                      <span className="text-sm font-medium truncate">
                        Ch. {job.chapterNumber}: {job.chapterTitle}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Badge
                        variant="outline"
                        className={cn("text-[10px] px-1.5", config.badgeClass)}
                      >
                        {config.label}
                      </Badge>
                      {job.provider && (
                        <Badge variant="secondary" className="text-[10px] px-1.5">
                          {job.provider}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Progress bar for queued/processing */}
                  {(job.status === "processing" || job.status === "queued") && (
                    <div className="space-y-1">
                      <Progress
                        value={job.progress}
                        className={cn("h-1.5", PROGRESS_COLORS[job.status])}
                      />
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <span>{job.stage}</span>
                        <span>{Math.round(job.progress)}%</span>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => toggleExpand(job.chapterId)}
                      className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      Details
                    </button>

                    <div className="flex items-center gap-1">
                      {job.status === "queued" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[10px] text-muted-foreground hover:text-destructive"
                          onClick={() => handleCancel(job.chapterId)}
                        >
                          <XCircle className="h-3 w-3 mr-1" />
                          Cancel
                        </Button>
                      )}
                      {job.status === "failed" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[10px] text-muted-foreground hover:text-primary"
                          onClick={() => handleRetry(job.chapterId)}
                        >
                          <RefreshCw className="h-3 w-3 mr-1" />
                          Retry
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-0 border-t text-[11px] text-muted-foreground space-y-1">
                    {job.startedAt && (
                      <div className="flex justify-between">
                        <span>Elapsed</span>
                        <span className="font-mono">
                          {formatElapsed(job.startedAt, job.completedAt)}
                        </span>
                      </div>
                    )}
                    {job.costUsd != null && (
                      <div className="flex justify-between">
                        <span>Cost</span>
                        <span className="font-mono">
                          ${job.costUsd.toFixed(4)}
                        </span>
                      </div>
                    )}
                    {job.provider && (
                      <div className="flex justify-between">
                        <span>Provider</span>
                        <span>{job.provider}</span>
                      </div>
                    )}
                    {job.errorMessage && (
                      <div className="mt-1 p-2 rounded bg-red-50 text-red-700 text-[10px]">
                        {job.errorMessage}
                      </div>
                    )}
                    {!job.startedAt && !job.costUsd && !job.errorMessage && (
                      <p className="text-center py-1">No details available yet</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {jobs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Radio className="h-8 w-8 mb-2" />
              <p className="text-sm">No generation jobs</p>
              <p className="text-xs">
                Start generating chapters to see the queue
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
