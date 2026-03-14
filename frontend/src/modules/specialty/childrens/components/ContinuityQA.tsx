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
import {
  useContinuityCheck,
  useAutoFixPrompts,
  type ContinuityIssue,
  type ContinuityIssueType,
  type ContinuitySeverity,
} from "../hooks";

// ---------------------------------------------------------------------------
// Labels & variants
// ---------------------------------------------------------------------------

const ISSUE_TYPE_LABELS: Record<ContinuityIssueType, string> = {
  missing_clothing: "Missing Clothing Reference",
  scale_mismatch: "Scale Mismatch",
  location_inconsistency: "Location Inconsistency",
  time_of_day_mismatch: "Time-of-Day Mismatch",
  style_drift: "Style Drift",
};

const SEVERITY_VARIANT: Record<ContinuitySeverity, "destructive" | "default" | "secondary"> = {
  critical: "destructive",
  warning: "default",
  info: "secondary",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ContinuityQAProps {
  bookId: string;
}

export function ContinuityQA({ bookId }: ContinuityQAProps) {
  const [issues, setIssues] = useState<ContinuityIssue[]>([]);
  const [hasRun, setHasRun] = useState(false);

  const continuityCheck = useContinuityCheck(bookId);
  const autoFix = useAutoFixPrompts(bookId);

  const fixableCount = issues.filter((i) => i.autoFixable).length;
  const allResolved = hasRun && issues.length === 0;

  const runCheck = async () => {
    const result = await continuityCheck.mutateAsync();
    setIssues(result);
    setHasRun(true);
  };

  const autoFixAll = async () => {
    const result = await autoFix.mutateAsync();
    setIssues(result.remaining_issues);
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
                disabled={autoFix.isPending}
              >
                {autoFix.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Wand2 className="mr-2 h-4 w-4" />
                )}
                {autoFix.isPending
                  ? "Fixing..."
                  : `Auto-Fix All (${fixableCount})`}
              </Button>
            )}

            <Button onClick={runCheck} disabled={continuityCheck.isPending}>
              {continuityCheck.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <PlayCircle className="mr-2 h-4 w-4" />
              )}
              {continuityCheck.isPending ? "Scanning..." : "Run Continuity Check"}
            </Button>
          </div>
        </div>

        {/* Error states */}
        {continuityCheck.isError && (
          <div className="flex items-center gap-2 text-destructive text-sm p-3 bg-destructive/10 rounded-md">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <p>Failed to run continuity check. Please try again.</p>
          </div>
        )}

        {autoFix.isError && (
          <div className="flex items-center gap-2 text-destructive text-sm p-3 bg-destructive/10 rounded-md">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <p>Auto-fix failed. Please try again.</p>
          </div>
        )}

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
        {!hasRun && !continuityCheck.isPending && (
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
