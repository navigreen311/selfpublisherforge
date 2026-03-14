"use client";

import { useState, useMemo } from "react";
import {
  FileDown,
  CheckCircle,
  XCircle,
  RefreshCw,
  FileText,
  BookOpen,
  List,
  Badge as BadgeIcon,
  SeparatorHorizontal,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

// ─── Types ──────────────────────────────────────────────────────────────────

interface PreflightCheck {
  id: string;
  label: string;
  passed: boolean;
  detail?: string;
}

interface ExportPanelProps {
  bookId: string;
  bookTitle: string;
  totalPuzzles: number;
  onRunPreflight: () => void;
  onExport: (options: ExportOptions) => void;
  preflightChecks?: PreflightCheck[];
  isRunningPreflight?: boolean;
  isExporting?: boolean;
  exportProgress?: number;
  exportResult?: {
    download_url: string;
    format: string;
    file_size: number;
    page_count: number;
  } | null;
}

interface ExportOptions {
  format: "pdf";
  include_toc: boolean;
  include_instructions: boolean;
  include_difficulty_badges: boolean;
  include_section_dividers: boolean;
  include_answer_key: boolean;
}

// ─── Component ──────────────────────────────────────────────────────────────

export function ExportPanel({
  bookId,
  bookTitle,
  totalPuzzles,
  onRunPreflight,
  onExport,
  preflightChecks,
  isRunningPreflight,
  isExporting,
  exportProgress,
  exportResult,
}: ExportPanelProps) {
  const [includeToc, setIncludeToc] = useState(true);
  const [includeInstructions, setIncludeInstructions] = useState(true);
  const [includeDifficultyBadges, setIncludeDifficultyBadges] = useState(true);
  const [includeSectionDividers, setIncludeSectionDividers] = useState(true);
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true);

  const allPreflightPassed = preflightChecks?.every((c) => c.passed) ?? false;
  const preflightRun = !!preflightChecks;

  const handleExport = () => {
    onExport({
      format: "pdf",
      include_toc: includeToc,
      include_instructions: includeInstructions,
      include_difficulty_badges: includeDifficultyBadges,
      include_section_dividers: includeSectionDividers,
      include_answer_key: includeAnswerKey,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Export</h2>
        <p className="text-sm text-muted-foreground">
          Export "{bookTitle}" as a print-ready PDF
        </p>
      </div>

      {/* ── Format ─────────────────────────────────────────────────────── */}
      <div className="border rounded-lg p-4">
        <Label className="font-medium">Format</Label>
        <div className="mt-2 flex items-center gap-3 border-2 border-primary rounded-lg p-3 bg-primary/5">
          <FileText className="h-5 w-5 text-primary" />
          <div>
            <p className="font-medium">Print PDF</p>
            <p className="text-xs text-muted-foreground">
              KDP-ready interior with bleed, trim marks, 300 DPI
            </p>
          </div>
        </div>
      </div>

      {/* ── Include Options ────────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <Label className="font-medium">Include Options</Label>
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <Checkbox
              checked={includeToc}
              onCheckedChange={(v) => setIncludeToc(!!v)}
            />
            <List className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Table of Contents</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <Checkbox
              checked={includeInstructions}
              onCheckedChange={(v) => setIncludeInstructions(!!v)}
            />
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Instructions per puzzle type</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <Checkbox
              checked={includeDifficultyBadges}
              onCheckedChange={(v) => setIncludeDifficultyBadges(!!v)}
            />
            <BadgeIcon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Difficulty badges on puzzles</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <Checkbox
              checked={includeSectionDividers}
              onCheckedChange={(v) => setIncludeSectionDividers(!!v)}
            />
            <SeparatorHorizontal className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Section dividers between types</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <Checkbox
              checked={includeAnswerKey}
              onCheckedChange={(v) => setIncludeAnswerKey(!!v)}
            />
            <Key className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Answer key</span>
          </label>
        </div>
      </div>

      {/* ── Preflight Checklist ─────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Preflight Checklist</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={onRunPreflight}
            disabled={isRunningPreflight}
          >
            {isRunningPreflight ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                Run Preflight
              </>
            )}
          </Button>
        </div>

        {!preflightRun ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            Run preflight to check for export issues before generating the PDF.
          </p>
        ) : (
          <div className="space-y-2">
            {preflightChecks!.map((check) => (
              <div
                key={check.id}
                className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/30"
              >
                <div className="flex items-center gap-2">
                  {check.passed ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm">{check.label}</span>
                </div>
                {check.detail && (
                  <span className="text-xs text-muted-foreground">
                    {check.detail}
                  </span>
                )}
              </div>
            ))}

            <div className="pt-2">
              {allPreflightPassed ? (
                <Badge
                  variant="secondary"
                  className="bg-green-100 text-green-800"
                >
                  All checks passed - ready to export
                </Badge>
              ) : (
                <Badge
                  variant="secondary"
                  className="bg-yellow-100 text-yellow-800"
                >
                  Some checks failed - review before exporting
                </Badge>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Export Progress ─────────────────────────────────────────────── */}
      {isExporting && (
        <div className="border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Exporting...</span>
            <span className="text-sm text-muted-foreground">
              {exportProgress ?? 0}%
            </span>
          </div>
          <Progress value={exportProgress ?? 0} />
        </div>
      )}

      {/* ── Export Result ──────────────────────────────────────────────── */}
      {exportResult && !isExporting && (
        <div className="border border-green-200 rounded-lg p-4 bg-green-50 space-y-3">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Export Complete</span>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Format</p>
              <p className="font-medium">{exportResult.format.toUpperCase()}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Pages</p>
              <p className="font-medium">{exportResult.page_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">File Size</p>
              <p className="font-medium">
                {(exportResult.file_size / 1024 / 1024).toFixed(1)} MB
              </p>
            </div>
          </div>
          <Button asChild className="w-full">
            <a href={exportResult.download_url} download>
              <FileDown className="h-4 w-4 mr-2" />
              Download PDF
            </a>
          </Button>
        </div>
      )}

      {/* ── Export Button ──────────────────────────────────────────────── */}
      {!isExporting && !exportResult && (
        <div className="flex justify-end">
          <Button
            size="lg"
            onClick={handleExport}
            disabled={totalPuzzles === 0}
          >
            <FileDown className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      )}
    </div>
  );
}
