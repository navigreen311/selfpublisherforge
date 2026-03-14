"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Wand2,
  PlayCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type IssueType =
  | "missing_clothing"
  | "scale_mismatch"
  | "location_inconsistency"
  | "time_of_day_mismatch"
  | "style_drift";

type Severity = "critical" | "warning" | "info";

interface ContinuityIssue {
  id: string;
  page: number;
  issueType: IssueType;
  description: string;
  severity: Severity;
  autoFixable: boolean;
}

const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  missing_clothing: "Missing Clothing Reference",
  scale_mismatch: "Scale Mismatch",
  location_inconsistency: "Location Inconsistency",
  time_of_day_mismatch: "Time-of-Day Mismatch",
  style_drift: "Style Drift",
};

const SEVERITY_VARIANT: Record<Severity, "destructive" | "default" | "secondary"> = {
  critical: "destructive",
  warning: "default",
  info: "secondary",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ContinuityQA() {
  const [issues, setIssues] = useState<ContinuityIssue[]>([]);
  const [scanning, setScanning] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  const fixableCount = issues.filter((i) => i.autoFixable).length;
  const allResolved = hasRun && issues.length === 0;

  const runCheck = async () => {
    setScanning(true);
    // TODO: call API  POST /api/v1/specialty/childrens-books/{bookId}/continuity-check
    await new Promise((r) => setTimeout(r, 1800));

    // Simulated results for UI demonstration
    const mockIssues: ContinuityIssue[] = [
      {
        id: "1",
        page: 4,
        issueType: "missing_clothing",
        description:
          "Character 'Luna' prompt on page 4 does not mention red collar with gold bell.",
        severity: "warning",
        autoFixable: true,
      },
      {
        id: "2",
        page: 7,
        issueType: "scale_mismatch",
        description:
          "Luna described as same height as rabbit on page 7, but scale rule says twice the size.",
        severity: "critical",
        autoFixable: true,
      },
      {
        id: "3",
        page: 12,
        issueType: "location_inconsistency",
        description:
          "Garden gate described as green on page 12, but setting rule specifies blue gate.",
        severity: "warning",
        autoFixable: true,
      },
      {
        id: "4",
        page: 15,
        issueType: "time_of_day_mismatch",
        description:
          "Page 15 prompt says 'bright midday sun' but time-of-day rules specify sunset for pages 13-16.",
        severity: "warning",
        autoFixable: true,
      },
      {
        id: "5",
        page: 9,
        issueType: "style_drift",
        description:
          "Generated image on page 9 shows significant style deviation from watercolor baseline.",
        severity: "info",
        autoFixable: false,
      },
    ];

    setIssues(mockIssues);
    setHasRun(true);
    setScanning(false);
  };

  const autoFixAll = async () => {
    setFixing(true);
    // TODO: call API  POST /api/v1/specialty/childrens-books/{bookId}/auto-fix-prompts
    await new Promise((r) => setTimeout(r, 2000));
    setIssues((prev) => prev.filter((i) => !i.autoFixable));
    setFixing(false);
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Continuity QA</h3>
            <p className="text-sm text-muted-foreground">
              Checks illustration prompts against character sheets and scene
              rules.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {hasRun && fixableCount > 0 && (
              <Button
                variant="outline"
                onClick={autoFixAll}
                disabled={fixing}
              >
                {fixing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Wand2 className="mr-2 h-4 w-4" />
                )}
                {fixing
                  ? "Fixing..."
                  : `Auto-Fix All (${fixableCount})`}
              </Button>
            )}

            <Button onClick={runCheck} disabled={scanning}>
              {scanning ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <PlayCircle className="mr-2 h-4 w-4" />
              )}
              {scanning ? "Scanning..." : "Run Continuity Check"}
            </Button>
          </div>
        </div>

        {/* All-clear state */}
        {allResolved && (
          <div className="flex flex-col items-center justify-center py-12 text-green-600">
            <CheckCircle2 className="h-16 w-16 mb-3" />
            <p className="text-lg font-semibold">All Issues Resolved</p>
            <p className="text-sm text-muted-foreground">
              Character consistency and scene continuity checks pass.
            </p>
          </div>
        )}

        {/* Issues table */}
        {hasRun && issues.length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Page</TableHead>
                  <TableHead className="w-48">Issue Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-24">Severity</TableHead>
                  <TableHead className="w-28 text-center">
                    Auto-fixable?
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {issues.map((issue) => (
                  <TableRow key={issue.id}>
                    <TableCell className="font-medium">{issue.page}</TableCell>
                    <TableCell className="text-sm">
                      {ISSUE_TYPE_LABELS[issue.issueType]}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {issue.description}
                    </TableCell>
                    <TableCell>
                      <Badge variant={SEVERITY_VARIANT[issue.severity]}>
                        {issue.severity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {issue.autoFixable ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600 mx-auto" />
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          Manual
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Not-yet-run state */}
        {!hasRun && !scanning && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mb-3 opacity-40" />
            <p className="text-sm">
              Click &quot;Run Continuity Check&quot; to scan for inconsistencies
              across pages.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
