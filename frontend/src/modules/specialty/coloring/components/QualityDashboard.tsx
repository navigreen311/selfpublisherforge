"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  RefreshCw,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type IssueSeverity = "critical" | "warning" | "info";
export type IssueStatus = "open" | "fixed" | "ignored";

export interface QualityIssue {
  id: string;
  pageNumber: number;
  issue: string;
  severity: IssueSeverity;
  status: IssueStatus;
}

export interface PrintQualityMetrics {
  lineQuality: number; // 0-100
  closedShapes: number;
  strokeUniformity: number;
  inkDensity: number;
  backgroundPurity: number;
}

export interface ComplexityDistribution {
  easy: number;
  medium: number;
  hard: number;
}

export interface QualityDashboardProps {
  overallScore: number; // 0-100
  themeCohesionScore: number; // 0-100
  themeCohesionExplanation: string;
  printMetrics: PrintQualityMetrics;
  complexity: ComplexityDistribution;
  issues: QualityIssue[];
  onFixAllIssues: () => void;
  onRerunQA: () => void;
  isFixing: boolean;
  isRerunning: boolean;
}

// ---------------------------------------------------------------------------
// Circular Gauge
// ---------------------------------------------------------------------------

function CircularGauge({
  score,
  size = 140,
  strokeWidth = 10,
  label,
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const center = size / 2;

  const color =
    score >= 80
      ? "text-green-500"
      : score >= 60
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="-rotate-90"
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            className="stroke-muted"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            className={cn("stroke-current transition-all duration-700", color)}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-3xl font-bold", color)}>{score}</span>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
            / 100
          </span>
        </div>
      </div>
      {label && (
        <span className="text-sm font-medium text-muted-foreground">
          {label}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metric Bar
// ---------------------------------------------------------------------------

function MetricBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 80
      ? "bg-green-500"
      : value >= 60
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm">{label}</span>
        <span className="text-sm font-semibold">{value}%</span>
      </div>
      <div className="h-2.5 rounded-full bg-muted overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Complexity Distribution Bar
// ---------------------------------------------------------------------------

function ComplexityBar({ distribution }: { distribution: ComplexityDistribution }) {
  const total = distribution.easy + distribution.medium + distribution.hard;
  if (total === 0) return null;

  const easyPct = (distribution.easy / total) * 100;
  const mediumPct = (distribution.medium / total) * 100;
  const hardPct = (distribution.hard / total) * 100;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">Complexity Distribution</h3>

      {/* Stacked bar */}
      <div className="h-6 rounded-full overflow-hidden flex">
        {easyPct > 0 && (
          <div
            className="bg-green-400 flex items-center justify-center text-[10px] font-semibold text-green-900"
            style={{ width: `${easyPct}%` }}
          >
            {distribution.easy}
          </div>
        )}
        {mediumPct > 0 && (
          <div
            className="bg-yellow-400 flex items-center justify-center text-[10px] font-semibold text-yellow-900"
            style={{ width: `${mediumPct}%` }}
          >
            {distribution.medium}
          </div>
        )}
        {hardPct > 0 && (
          <div
            className="bg-red-400 flex items-center justify-center text-[10px] font-semibold text-red-900"
            style={{ width: `${hardPct}%` }}
          >
            {distribution.hard}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
          Easy ({distribution.easy})
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
          Medium ({distribution.medium})
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
          Hard ({distribution.hard})
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Severity helpers
// ---------------------------------------------------------------------------

const SEVERITY_ICON: Record<IssueSeverity, React.ReactNode> = {
  critical: <AlertCircle className="h-4 w-4 text-red-500" />,
  warning: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  info: <Info className="h-4 w-4 text-blue-500" />,
};

const SEVERITY_BADGE_CLASS: Record<IssueSeverity, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  warning:
    "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  info: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
};

const STATUS_BADGE_CLASS: Record<IssueStatus, string> = {
  open: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  fixed: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  ignored: "bg-muted text-muted-foreground",
};

// ---------------------------------------------------------------------------
// QualityDashboard
// ---------------------------------------------------------------------------

export function QualityDashboard({
  overallScore,
  themeCohesionScore,
  themeCohesionExplanation,
  printMetrics,
  complexity,
  issues,
  onFixAllIssues,
  onRerunQA,
  isFixing,
  isRerunning,
}: QualityDashboardProps) {
  const openIssuesCount = issues.filter((i) => i.status === "open").length;

  return (
    <div className="space-y-6">
      {/* Top row: Overall Score + Theme Cohesion */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 flex flex-col items-center justify-center">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4">
            Overall Quality Score
          </h3>
          <CircularGauge score={overallScore} size={160} strokeWidth={12} />
        </Card>

        <Card className="p-6 flex flex-col items-center justify-center">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4">
            Theme Cohesion
          </h3>
          <CircularGauge
            score={themeCohesionScore}
            size={120}
            strokeWidth={8}
          />
          <p className="text-xs text-muted-foreground text-center mt-3 max-w-[280px]">
            {themeCohesionExplanation}
          </p>
        </Card>
      </div>

      {/* Complexity distribution */}
      <Card className="p-6">
        <ComplexityBar distribution={complexity} />
      </Card>

      {/* Print quality metrics */}
      <Card className="p-6 space-y-4">
        <h3 className="text-sm font-semibold">Print Quality Summary</h3>
        <MetricBar label="Line Quality" value={printMetrics.lineQuality} />
        <MetricBar label="Closed Shapes" value={printMetrics.closedShapes} />
        <MetricBar
          label="Stroke Uniformity"
          value={printMetrics.strokeUniformity}
        />
        <MetricBar label="Ink Density" value={printMetrics.inkDensity} />
        <MetricBar
          label="Background Purity"
          value={printMetrics.backgroundPurity}
        />
      </Card>

      {/* Issues table */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">
            Issues
            {openIssuesCount > 0 && (
              <Badge variant="destructive" className="ml-2 text-[10px]">
                {openIssuesCount} open
              </Badge>
            )}
          </h3>
        </div>

        {issues.length === 0 ? (
          <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            No issues found. All quality checks passed.
          </div>
        ) : (
          <div className="rounded-md border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[70px]">Page #</TableHead>
                  <TableHead>Issue</TableHead>
                  <TableHead className="w-[100px]">Severity</TableHead>
                  <TableHead className="w-[90px]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {issues.map((issue) => (
                  <TableRow key={issue.id}>
                    <TableCell className="font-medium">
                      {issue.pageNumber}
                    </TableCell>
                    <TableCell className="text-sm">
                      <div className="flex items-center gap-2">
                        {SEVERITY_ICON[issue.severity]}
                        {issue.issue}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-[10px] capitalize",
                          SEVERITY_BADGE_CLASS[issue.severity]
                        )}
                      >
                        {issue.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-[10px] capitalize",
                          STATUS_BADGE_CLASS[issue.status]
                        )}
                      >
                        {issue.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            variant="default"
            onClick={onFixAllIssues}
            disabled={openIssuesCount === 0 || isFixing}
          >
            {isFixing ? (
              <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <Wrench className="h-4 w-4 mr-1.5" />
            )}
            Fix All Issues{openIssuesCount > 0 && ` (${openIssuesCount})`}
          </Button>
          <Button
            variant="outline"
            onClick={onRerunQA}
            disabled={isRerunning}
          >
            {isRerunning ? (
              <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-1.5" />
            )}
            Re-run Full QA
          </Button>
        </div>
      </Card>
    </div>
  );
}
