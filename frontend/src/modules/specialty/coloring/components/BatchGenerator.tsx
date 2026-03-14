"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Play,
  Pause,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  DollarSign,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PageStatus =
  | "pending"
  | "generating"
  | "cleaning"
  | "qa"
  | "done"
  | "failed";

export interface PageDescription {
  id: string;
  pageNumber: number;
  description: string;
  status: PageStatus;
  qaPass?: boolean;
  qaIssues?: string[];
}

export interface BatchGeneratorProps {
  pages: PageDescription[];
  onPagesChange: (pages: PageDescription[]) => void;
  onGenerateAll: () => void;
  onPause: () => void;
  onCancel: () => void;
  variationMode: boolean;
  onVariationModeChange: (enabled: boolean) => void;
  isRunning: boolean;
  isPaused: boolean;
  costEstimateCents: number;
  overallProgress: number; // 0-100
}

// ---------------------------------------------------------------------------
// Status chip colors
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  PageStatus,
  { label: string; className: string; icon?: React.ReactNode }
> = {
  pending: {
    label: "Pending",
    className: "bg-muted text-muted-foreground",
  },
  generating: {
    label: "Generating",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  cleaning: {
    label: "Cleaning",
    className:
      "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  qa: {
    label: "QA",
    className:
      "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  done: {
    label: "Done",
    className:
      "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
    icon: <AlertCircle className="h-3 w-3" />,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function generateId(): string {
  return `page-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ---------------------------------------------------------------------------
// PageRow
// ---------------------------------------------------------------------------

interface PageRowProps {
  page: PageDescription;
  index: number;
  total: number;
  onDescriptionChange: (id: string, description: string) => void;
  onRemove: (id: string) => void;
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
  disabled: boolean;
}

function PageRow({
  page,
  index,
  total,
  onDescriptionChange,
  onRemove,
  onMoveUp,
  onMoveDown,
  disabled,
}: PageRowProps) {
  const statusCfg = STATUS_CONFIG[page.status];

  return (
    <div className="flex gap-3 items-start p-3 rounded-lg border bg-card">
      {/* Page number & reorder */}
      <div className="flex flex-col items-center gap-0.5 pt-1">
        <span className="text-xs font-bold text-muted-foreground w-6 text-center">
          {page.pageNumber}
        </span>
        <button
          type="button"
          onClick={() => onMoveUp(index)}
          disabled={index === 0 || disabled}
          className="p-0.5 rounded hover:bg-muted disabled:opacity-30"
          aria-label="Move up"
        >
          <ChevronUp className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onMoveDown(index)}
          disabled={index === total - 1 || disabled}
          className="p-0.5 rounded hover:bg-muted disabled:opacity-30"
          aria-label="Move down"
        >
          <ChevronDown className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Description */}
      <div className="flex-1 space-y-2">
        <Textarea
          value={page.description}
          onChange={(e) => onDescriptionChange(page.id, e.target.value)}
          placeholder={`Describe page ${page.pageNumber} illustration...`}
          rows={2}
          disabled={disabled}
          className="resize-none text-sm"
        />

        {/* Status chip + QA indicator */}
        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className={cn("text-[10px] gap-1", statusCfg.className)}
          >
            {statusCfg.icon}
            {statusCfg.label}
          </Badge>

          {page.status === "done" && page.qaPass !== undefined && (
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="flex items-center gap-0.5">
                    {page.qaPass ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-[10px] text-muted-foreground">
                      {page.qaPass
                        ? "QA Pass"
                        : `${page.qaIssues?.length ?? 0} issue(s)`}
                    </span>
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-[240px]">
                  {page.qaPass ? (
                    <p className="text-xs">
                      All quality checks passed for this page.
                    </p>
                  ) : (
                    <ul className="text-xs space-y-0.5">
                      {page.qaIssues?.map((issue, i) => (
                        <li key={i} className="flex items-start gap-1">
                          <AlertCircle className="h-3 w-3 text-red-500 mt-0.5 shrink-0" />
                          {issue}
                        </li>
                      ))}
                    </ul>
                  )}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>

      {/* Remove button */}
      <button
        type="button"
        onClick={() => onRemove(page.id)}
        disabled={disabled}
        className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive disabled:opacity-30 transition-colors"
        aria-label={`Remove page ${page.pageNumber}`}
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// BatchGenerator
// ---------------------------------------------------------------------------

export function BatchGenerator({
  pages,
  onPagesChange,
  onGenerateAll,
  onPause,
  onCancel,
  variationMode,
  onVariationModeChange,
  isRunning,
  isPaused,
  costEstimateCents,
  overallProgress,
}: BatchGeneratorProps) {
  // --- Page list mutations ---
  const handleDescriptionChange = (id: string, description: string) => {
    onPagesChange(
      pages.map((p) => (p.id === id ? { ...p, description } : p))
    );
  };

  const handleRemove = (id: string) => {
    const updated = pages
      .filter((p) => p.id !== id)
      .map((p, i) => ({ ...p, pageNumber: i + 1 }));
    onPagesChange(updated);
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const updated = [...pages];
    [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
    onPagesChange(
      updated.map((p, i) => ({ ...p, pageNumber: i + 1 }))
    );
  };

  const handleMoveDown = (index: number) => {
    if (index === pages.length - 1) return;
    const updated = [...pages];
    [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
    onPagesChange(
      updated.map((p, i) => ({ ...p, pageNumber: i + 1 }))
    );
  };

  const handleAddPage = () => {
    onPagesChange([
      ...pages,
      {
        id: generateId(),
        pageNumber: pages.length + 1,
        description: "",
        status: "pending",
      },
    ]);
  };

  // --- Derived ---
  const completedCount = pages.filter((p) => p.status === "done").length;
  const failedCount = pages.filter((p) => p.status === "failed").length;

  return (
    <Card className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Batch Page Generator</h2>
          <p className="text-sm text-muted-foreground">
            Define descriptions for each page, then generate all at once.
          </p>
        </div>

        {/* Cost estimate */}
        <div className="flex items-center gap-2 rounded-lg border bg-muted/50 px-3 py-2">
          <DollarSign className="h-4 w-4 text-muted-foreground" />
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Est. Cost</p>
            <p className="text-sm font-semibold">
              {formatCost(costEstimateCents)}
            </p>
          </div>
        </div>
      </div>

      {/* Variation mode toggle */}
      <div className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30">
        <Switch
          id="variation-mode"
          checked={variationMode}
          onCheckedChange={onVariationModeChange}
          disabled={isRunning}
        />
        <Label
          htmlFor="variation-mode"
          className="text-sm font-medium cursor-pointer"
        >
          Variation Mode
        </Label>
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-4 w-4 text-muted-foreground" />
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-[260px]">
              <p className="text-xs">
                When enabled, the generator analyzes composition across all
                pages to prevent similar layouts and poses, ensuring visual
                variety throughout the book.
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Overall progress (visible when running) */}
      {isRunning && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Overall Progress
              {isPaused && (
                <Badge variant="outline" className="ml-2 text-[10px]">
                  Paused
                </Badge>
              )}
            </span>
            <span className="font-medium">
              {completedCount}/{pages.length} pages
              {failedCount > 0 && (
                <span className="text-red-500 ml-1">
                  ({failedCount} failed)
                </span>
              )}
            </span>
          </div>
          <Progress value={overallProgress} className="h-2" />
        </div>
      )}

      {/* Page description list */}
      <div className="space-y-2">
        {pages.map((page, index) => (
          <PageRow
            key={page.id}
            page={page}
            index={index}
            total={pages.length}
            onDescriptionChange={handleDescriptionChange}
            onRemove={handleRemove}
            onMoveUp={handleMoveUp}
            onMoveDown={handleMoveDown}
            disabled={isRunning}
          />
        ))}
      </div>

      {/* Add page button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleAddPage}
        disabled={isRunning}
        className="w-full"
      >
        <Plus className="h-4 w-4 mr-1.5" />
        Add Page
      </Button>

      {/* Action buttons */}
      <div className="flex items-center gap-3 pt-2 border-t">
        {!isRunning ? (
          <Button
            onClick={onGenerateAll}
            disabled={pages.length === 0}
            className="flex-1"
          >
            <Play className="h-4 w-4 mr-1.5" />
            Generate All ({pages.length} pages)
          </Button>
        ) : (
          <>
            <Button
              variant="outline"
              onClick={onPause}
              className="flex-1"
            >
              <Pause className="h-4 w-4 mr-1.5" />
              {isPaused ? "Resume" : "Pause"}
            </Button>
            <Button
              variant="destructive"
              onClick={onCancel}
              className="flex-1"
            >
              <X className="h-4 w-4 mr-1.5" />
              Cancel
            </Button>
          </>
        )}
      </div>
    </Card>
  );
}
