"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  FileText,
  Image,
  Code2,
  Monitor,
  CheckCircle2,
  XCircle,
  Loader2,
  Download,
  ShieldCheck,
  BookOpen,
  Minus,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ExportFormat = "print-pdf" | "png" | "svg" | "digital-pdf";

export interface PreflightCheck {
  id: string;
  label: string;
  passed: boolean | null; // null = not yet run
}

export interface PageCountBreakdown {
  coloringPages: number;
  blankBacks: number;
  bonusPages: number;
}

export interface ExportPanelProps {
  selectedFormat: ExportFormat;
  onFormatChange: (format: ExportFormat) => void;
  pageCount: PageCountBreakdown;
  preflightChecks: PreflightCheck[];
  onRunPreflight: () => void;
  onExport: () => void;
  isPreflighting: boolean;
  isExporting: boolean;
  exportProgress: number; // 0-100
}

// ---------------------------------------------------------------------------
// Format card definitions
// ---------------------------------------------------------------------------

interface FormatOption {
  value: ExportFormat;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    value: "print-pdf",
    label: "Print-Ready PDF",
    description: "KDP-compliant, 300 DPI, B&W interior with bleed and trim marks",
    icon: <FileText className="h-5 w-5" />,
  },
  {
    value: "png",
    label: "Individual PNGs",
    description: "Separate 300 DPI PNG files for each coloring page",
    icon: <Image className="h-5 w-5" />,
  },
  {
    value: "svg",
    label: "SVG Vector Package",
    description: "Scalable vector files for ultra-crisp printing at any size",
    icon: <Code2 className="h-5 w-5" />,
  },
  {
    value: "digital-pdf",
    label: "Digital PDF",
    description: "Screen-optimized PDF for digital coloring or viewing",
    icon: <Monitor className="h-5 w-5" />,
  },
];

// ---------------------------------------------------------------------------
// Default preflight checks
// ---------------------------------------------------------------------------

export const DEFAULT_PREFLIGHT_CHECKS: PreflightCheck[] = [
  { id: "pure-bw", label: "Pure B&W", passed: null },
  { id: "dpi-300", label: "300 DPI", passed: null },
  { id: "stroke-uniformity", label: "Stroke Uniformity", passed: null },
  { id: "closed-shapes", label: "Closed Shapes", passed: null },
  { id: "no-specks", label: "No Specks", passed: null },
  { id: "ink-density", label: "Ink Density", passed: null },
  { id: "no-duplicates", label: "No Duplicates", passed: null },
  { id: "grayscale-verified", label: "Grayscale Verified", passed: null },
  { id: "font-licensing", label: "Font Licensing", passed: null },
];

// ---------------------------------------------------------------------------
// Format Radio Card
// ---------------------------------------------------------------------------

function FormatCard({
  option,
  selected,
  onSelect,
  disabled,
}: {
  option: FormatOption;
  selected: boolean;
  onSelect: () => void;
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      disabled={disabled}
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border-2 text-left transition-all w-full",
        "hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        selected
          ? "border-primary bg-primary/5"
          : "border-muted bg-background"
      )}
    >
      <div
        className={cn(
          "mt-0.5 shrink-0",
          selected ? "text-primary" : "text-muted-foreground"
        )}
      >
        {option.icon}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold">{option.label}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {option.description}
        </p>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Preflight check row
// ---------------------------------------------------------------------------

function PreflightRow({ check }: { check: PreflightCheck }) {
  return (
    <div className="flex items-center gap-2 py-1">
      {check.passed === null ? (
        <Minus className="h-4 w-4 text-muted-foreground" />
      ) : check.passed ? (
        <CheckCircle2 className="h-4 w-4 text-green-500" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500" />
      )}
      <span
        className={cn(
          "text-sm",
          check.passed === false && "text-red-600 font-medium"
        )}
      >
        {check.label}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ExportPanel
// ---------------------------------------------------------------------------

export function ExportPanel({
  selectedFormat,
  onFormatChange,
  pageCount,
  preflightChecks,
  onRunPreflight,
  onExport,
  isPreflighting,
  isExporting,
  exportProgress,
}: ExportPanelProps) {
  const totalPages =
    pageCount.coloringPages + pageCount.blankBacks + pageCount.bonusPages;

  const allChecksPassed = preflightChecks.every((c) => c.passed === true);
  const hasBeenRun = preflightChecks.some((c) => c.passed !== null);
  const failedCount = preflightChecks.filter((c) => c.passed === false).length;

  return (
    <div className="space-y-6">
      {/* Format selection */}
      <Card className="p-6 space-y-4">
        <h3 className="text-sm font-semibold">Export Format</h3>
        <div
          className="grid grid-cols-1 sm:grid-cols-2 gap-3"
          role="radiogroup"
          aria-label="Export format"
        >
          {FORMAT_OPTIONS.map((option) => (
            <FormatCard
              key={option.value}
              option={option}
              selected={selectedFormat === option.value}
              onSelect={() => onFormatChange(option.value)}
              disabled={isExporting}
            />
          ))}
        </div>
      </Card>

      {/* Info section */}
      <Card className="p-6 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <BookOpen className="h-4 w-4" />
          Export Details
        </h3>

        {/* Single-sided + blank backs info */}
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 p-2 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            <span>
              <strong>Single-sided enforced.</strong> Each coloring page is
              followed by a blank back to prevent bleed-through.
            </span>
          </div>

          <div className="flex items-center gap-2 text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
            <span>
              {pageCount.blankBacks} auto-inserted blank back
              {pageCount.blankBacks !== 1 && "s"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
            <span>Coloring-safe inner margin (+0.25in at spine) applied</span>
          </div>
        </div>

        <Separator />

        {/* Page count breakdown */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Total Page Count</h4>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div className="p-2 rounded bg-muted/50">
              <p className="text-lg font-bold">{pageCount.coloringPages}</p>
              <p className="text-[10px] text-muted-foreground">Coloring</p>
            </div>
            <div className="p-2 rounded bg-muted/50 flex flex-col items-center justify-center">
              <span className="text-muted-foreground text-lg">+</span>
            </div>
            <div className="p-2 rounded bg-muted/50">
              <p className="text-lg font-bold">{pageCount.blankBacks}</p>
              <p className="text-[10px] text-muted-foreground">Blank Backs</p>
            </div>
            <div className="p-2 rounded bg-muted/50">
              <p className="text-lg font-bold">{pageCount.bonusPages}</p>
              <p className="text-[10px] text-muted-foreground">Bonus</p>
            </div>
          </div>
          <div className="text-center p-2 rounded bg-primary/10">
            <p className="text-xl font-bold">{totalPages}</p>
            <p className="text-xs text-muted-foreground">Total Pages</p>
          </div>
        </div>
      </Card>

      {/* Preflight checklist */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            Preflight Checklist
          </h3>
          {hasBeenRun && (
            <Badge
              variant={allChecksPassed ? "default" : "destructive"}
              className="text-[10px]"
            >
              {allChecksPassed
                ? "All Passed"
                : `${failedCount} Failed`}
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4">
          {preflightChecks.map((check) => (
            <PreflightRow key={check.id} check={check} />
          ))}
        </div>

        <Separator />

        {/* Action buttons */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={onRunPreflight}
            disabled={isPreflighting || isExporting}
            className="flex-1"
          >
            {isPreflighting ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <ShieldCheck className="h-4 w-4 mr-1.5" />
            )}
            {isPreflighting ? "Running Preflight..." : "Run Preflight"}
          </Button>

          <Button
            onClick={onExport}
            disabled={isExporting || !allChecksPassed}
            className="flex-1"
          >
            {isExporting ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-1.5" />
            )}
            {isExporting
              ? "Exporting..."
              : `Export ${FORMAT_OPTIONS.find((f) => f.value === selectedFormat)?.label ?? ""}`}
          </Button>
        </div>

        {/* Export progress */}
        {isExporting && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Exporting...</span>
              <span>{exportProgress}%</span>
            </div>
            <Progress value={exportProgress} className="h-2" />
          </div>
        )}
      </Card>
    </div>
  );
}
