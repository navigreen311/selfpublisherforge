"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ShieldCheck,
  ShieldAlert,
  Loader2,
  ScanSearch,
  AlertTriangle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Severity = "critical" | "warning" | "info";

interface TrademarkHit {
  id: string;
  page: number;
  term: string;
  context: string;
}

type SensitivityCategory =
  | "violence"
  | "fear"
  | "stereotypes"
  | "mature_themes";

interface SensitivityIssue {
  id: string;
  page: number;
  category: SensitivityCategory;
  description: string;
  severity: Severity;
}

const CATEGORY_LABELS: Record<SensitivityCategory, string> = {
  violence: "Violence",
  fear: "Fear",
  stereotypes: "Stereotypes",
  mature_themes: "Mature Themes",
};

const SEVERITY_VARIANT: Record<Severity, "destructive" | "default" | "secondary"> = {
  critical: "destructive",
  warning: "default",
  info: "secondary",
};

const BLOCKED_TERMS_DISPLAY = [
  "Disney",
  "Pixar",
  "Peppa Pig",
  "Bluey",
  "Paw Patrol",
  "Marvel",
  "Frozen",
  "Cocomelon",
  "Sesame Street",
  "in the style of [artist]",
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SafetyPanel() {
  const [scanning, setScanning] = useState(false);
  const [hasRun, setHasRun] = useState(false);
  const [trademarkHits, setTrademarkHits] = useState<TrademarkHit[]>([]);
  const [sensitivityIssues, setSensitivityIssues] = useState<
    SensitivityIssue[]
  >([]);

  const totalIssues = trademarkHits.length + sensitivityIssues.length;
  const hasCritical =
    sensitivityIssues.some((i) => i.severity === "critical") ||
    trademarkHits.length > 0;
  const isSafe = hasRun && totalIssues === 0;

  const runSafetyScan = async () => {
    setScanning(true);
    // TODO: call API  POST /api/v1/specialty/childrens-books/{bookId}/safety-check
    await new Promise((r) => setTimeout(r, 2000));

    // Simulated results
    setTrademarkHits([
      {
        id: "t1",
        page: 3,
        term: "Frozen",
        context: '...a dress like in "Frozen"...',
      },
      {
        id: "t2",
        page: 11,
        term: "in the style of",
        context: "...in the style of Hayao Miyazaki...",
      },
    ]);

    setSensitivityIssues([
      {
        id: "s1",
        page: 8,
        category: "fear",
        description:
          "Illustration prompt references 'dark shadowy monster lurking behind door' - may exceed mild fear threshold for ages 3-5.",
        severity: "warning",
      },
      {
        id: "s2",
        page: 14,
        category: "stereotypes",
        description:
          "Character description uses potentially stereotypical cultural trope. Review for sensitivity.",
        severity: "info",
      },
    ]);

    setHasRun(true);
    setScanning(false);
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-6">
        {/* Header + Button */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Safety &amp; Compliance</h3>
            <p className="text-sm text-muted-foreground">
              Trademark enforcement, content sensitivity scanning, and
              compliance checks.
            </p>
          </div>
          <Button onClick={runSafetyScan} disabled={scanning}>
            {scanning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ScanSearch className="mr-2 h-4 w-4" />
            )}
            {scanning ? "Scanning..." : "Run Safety Scan"}
          </Button>
        </div>

        {/* Banner */}
        {hasRun && (
          <div
            className={`flex items-center gap-3 rounded-lg px-4 py-3 ${
              isSafe
                ? "bg-green-50 border border-green-200 text-green-800"
                : "bg-red-50 border border-red-200 text-red-800"
            }`}
          >
            {isSafe ? (
              <>
                <ShieldCheck className="h-5 w-5" />
                <span className="font-semibold">Safe for Publishing</span>
                <span className="text-sm ml-1">
                  No trademark or content sensitivity issues found.
                </span>
              </>
            ) : (
              <>
                <ShieldAlert className="h-5 w-5" />
                <span className="font-semibold">Issues Found</span>
                <span className="text-sm ml-1">
                  {totalIssues} issue{totalIssues !== 1 ? "s" : ""} detected
                  {hasCritical ? " (includes critical)" : ""}.
                </span>
              </>
            )}
          </div>
        )}

        {/* Trademark Section */}
        {hasRun && (
          <>
            <div>
              <h4 className="text-sm font-semibold mb-2">
                Trademark Enforcement
              </h4>
              <p className="text-xs text-muted-foreground mb-3">
                Blocked terms:{" "}
                {BLOCKED_TERMS_DISPLAY.map((t, i) => (
                  <span key={t}>
                    <code className="bg-muted px-1 py-0.5 rounded text-xs">
                      {t}
                    </code>
                    {i < BLOCKED_TERMS_DISPLAY.length - 1 ? ", " : ""}
                  </span>
                ))}
              </p>

              {trademarkHits.length === 0 ? (
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <ShieldCheck className="h-4 w-4" />
                  No trademark violations found.
                </p>
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">Page</TableHead>
                        <TableHead className="w-40">Flagged Term</TableHead>
                        <TableHead>Context</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {trademarkHits.map((hit) => (
                        <TableRow key={hit.id}>
                          <TableCell className="font-medium">
                            {hit.page}
                          </TableCell>
                          <TableCell>
                            <Badge variant="destructive">{hit.term}</Badge>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {hit.context}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>

            <Separator />

            {/* Content Sensitivity Section */}
            <div>
              <h4 className="text-sm font-semibold mb-3">
                Content Sensitivity
              </h4>

              {sensitivityIssues.length === 0 ? (
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <ShieldCheck className="h-4 w-4" />
                  No content sensitivity issues found.
                </p>
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">Page</TableHead>
                        <TableHead className="w-32">Category</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="w-24">Severity</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sensitivityIssues.map((issue) => (
                        <TableRow key={issue.id}>
                          <TableCell className="font-medium">
                            {issue.page}
                          </TableCell>
                          <TableCell className="text-sm">
                            {CATEGORY_LABELS[issue.category]}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {issue.description}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={SEVERITY_VARIANT[issue.severity]}
                            >
                              {issue.severity}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          </>
        )}

        {/* Not-yet-run state */}
        {!hasRun && !scanning && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mb-3 opacity-40" />
            <p className="text-sm">
              Click &quot;Run Safety Scan&quot; to check for trademark
              violations and content sensitivity issues.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
