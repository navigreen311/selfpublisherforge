"use client";

import { useMemo } from "react";
import {
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Wand2,
  Gauge,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// ─── Types ──────────────────────────────────────────────────────────────────

interface QualityCheck {
  id: string;
  label: string;
  passed: boolean;
  detail?: string;
}

interface PuzzleIssue {
  puzzle_number: number;
  puzzle_type: string;
  issue: string;
  severity: "error" | "warning" | "info";
}

interface QualityDashboardProps {
  bookId: string;
  overallScore: number;
  checks: QualityCheck[];
  puzzleIssues: PuzzleIssue[];
  onFixAll: () => void;
  onRerunQA: () => void;
  isFixing?: boolean;
  isRunningQA?: boolean;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-yellow-600";
  return "text-red-600";
}

function getScoreRingColor(score: number): string {
  if (score >= 80) return "stroke-green-500";
  if (score >= 60) return "stroke-yellow-500";
  return "stroke-red-500";
}

function getScoreLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 80) return "Good";
  if (score >= 60) return "Fair";
  if (score >= 40) return "Poor";
  return "Critical";
}

const SEVERITY_STYLES: Record<string, string> = {
  error: "bg-red-100 text-red-800",
  warning: "bg-yellow-100 text-yellow-800",
  info: "bg-blue-100 text-blue-800",
};

const SEVERITY_ICONS: Record<string, typeof AlertTriangle> = {
  error: XCircle,
  warning: AlertTriangle,
  info: AlertTriangle,
};

// ─── Default Checks ─────────────────────────────────────────────────────────

const DEFAULT_CHECKS: QualityCheck[] = [
  { id: "no_dup_grids", label: "No duplicate grids", passed: false },
  { id: "no_dup_words", label: "No duplicate word lists", passed: false },
  { id: "all_solvable", label: "All puzzles verified solvable", passed: false },
  { id: "diff_dist", label: "Difficulty distribution correct", passed: false },
  { id: "clues_qa", label: "All clues QA'd", passed: false },
  { id: "font_sizes", label: "Font sizes adequate", passed: false },
];

// ─── Component ──────────────────────────────────────────────────────────────

export function QualityDashboard({
  bookId,
  overallScore,
  checks,
  puzzleIssues,
  onFixAll,
  onRerunQA,
  isFixing,
  isRunningQA,
}: QualityDashboardProps) {
  const activeChecks = checks.length > 0 ? checks : DEFAULT_CHECKS;
  const passedCount = activeChecks.filter((c) => c.passed).length;
  const totalChecks = activeChecks.length;

  const issuesByType = useMemo(() => {
    const counts = { error: 0, warning: 0, info: 0 };
    for (const issue of puzzleIssues) {
      counts[issue.severity]++;
    }
    return counts;
  }, [puzzleIssues]);

  // SVG gauge
  const circumference = 2 * Math.PI * 45;
  const dashOffset = circumference - (overallScore / 100) * circumference;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Quality Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Book-level quality assessment and issue tracking
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={onRerunQA}
            disabled={isRunningQA}
          >
            {isRunningQA ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Running QA...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Re-run QA
              </>
            )}
          </Button>
          <Button onClick={onFixAll} disabled={isFixing || puzzleIssues.length === 0}>
            {isFixing ? (
              <>
                <Wand2 className="h-4 w-4 mr-2 animate-pulse" />
                Fixing...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4 mr-2" />
                Fix All
              </>
            )}
          </Button>
        </div>
      </div>

      {/* ── Score Gauge & Summary ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Gauge */}
        <div className="border rounded-lg p-6 flex flex-col items-center justify-center">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-gray-100"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                className={`transition-all duration-700 ${getScoreRingColor(
                  overallScore
                )}`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className={`text-3xl font-bold ${getScoreColor(overallScore)}`}
              >
                {overallScore}
              </span>
              <span className="text-xs text-muted-foreground">/ 100</span>
            </div>
          </div>
          <p className={`text-sm font-medium mt-2 ${getScoreColor(overallScore)}`}>
            {getScoreLabel(overallScore)}
          </p>
        </div>

        {/* Checks Summary */}
        <div className="border rounded-lg p-6">
          <h3 className="font-medium mb-3 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            Checks ({passedCount}/{totalChecks})
          </h3>
          <div className="space-y-2">
            {activeChecks.map((check) => (
              <div key={check.id} className="flex items-center gap-2">
                {check.passed ? (
                  <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500 shrink-0" />
                )}
                <span className="text-sm">{check.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Issue Counts */}
        <div className="border rounded-lg p-6">
          <h3 className="font-medium mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Issues Summary
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm">Errors</span>
              </div>
              <Badge
                variant="secondary"
                className={
                  issuesByType.error > 0
                    ? "bg-red-100 text-red-800"
                    : "bg-green-100 text-green-800"
                }
              >
                {issuesByType.error}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm">Warnings</span>
              </div>
              <Badge
                variant="secondary"
                className={
                  issuesByType.warning > 0
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-green-100 text-green-800"
                }
              >
                {issuesByType.warning}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-blue-600" />
                <span className="text-sm">Info</span>
              </div>
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                {issuesByType.info}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* ── Per-Puzzle Issues Table ─────────────────────────────────────── */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-muted px-4 py-2 border-b flex items-center justify-between">
          <h3 className="font-medium text-sm">Per-Puzzle Issues</h3>
          <span className="text-xs text-muted-foreground">
            {puzzleIssues.length} issue{puzzleIssues.length !== 1 ? "s" : ""}
          </span>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[90px]">Puzzle #</TableHead>
              <TableHead className="w-[130px]">Type</TableHead>
              <TableHead>Issue</TableHead>
              <TableHead className="w-[100px]">Severity</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {puzzleIssues.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8">
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle className="h-8 w-8 text-green-500" />
                    <p className="text-sm text-muted-foreground">
                      No issues found. All puzzles passed quality checks.
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              puzzleIssues.map((issue, i) => {
                const SeverityIcon = SEVERITY_ICONS[issue.severity];
                return (
                  <TableRow key={i}>
                    <TableCell className="font-medium">
                      #{issue.puzzle_number}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {issue.puzzle_type.replace(/_/g, " ")}
                    </TableCell>
                    <TableCell>{issue.issue}</TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={SEVERITY_STYLES[issue.severity]}
                      >
                        <SeverityIcon className="h-3 w-3 mr-1" />
                        {issue.severity}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
