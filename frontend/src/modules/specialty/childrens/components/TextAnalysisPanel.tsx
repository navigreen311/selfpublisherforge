"use client";

import * as React from "react";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Music,
  Sparkles,
  Eye,
  Wand2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AgeBandRule {
  rule: string;
  pass: boolean;
  message: string;
}

interface Violation {
  rule: string;
  message: string;
  page: number | null;
  line: number | null;
  offending_text: string | null;
  suggestion: string | null;
}

interface PageBreakdown {
  page_number: number;
  word_count: number;
  longest_sentence: number;
  longest_word: string;
  vocab_level: string;
  issues: string[];
}

interface RhymeAnalysis {
  pattern: "AABB" | "ABAB" | "ABCB" | null;
  detected_scheme: string;
  issues: string[];
}

interface PageTurnEntry {
  page_num: number;
  surprise_score: number;
}

interface TextAnalysisData {
  readability_score: number;
  rhythm_score: number;
  look_inside_score: number;
  age_band_rules: AgeBandRule[];
  page_breakdown: PageBreakdown[];
  violations: Violation[];
  page_turn_map: PageTurnEntry[];
  rhyme_analysis: RhymeAnalysis | null;
}

interface TextAnalysisPanelProps {
  bookId: string;
  ageRange: string;
  storyMode?: string;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/childrens-books";

function useTextAnalysis(bookId: string) {
  return useQuery<TextAnalysisData>({
    queryKey: ["childrens-books", "text-analysis", bookId],
    queryFn: async () => {
      const { data } = await api.post(`${API_BASE}/${bookId}/analyze-text`);
      return data;
    },
    enabled: !!bookId,
  });
}

function useFixRhymes(bookId: string) {
  return useMutation<{ fixed_text: string }, Error>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/fix-rhymes`
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Rhyme fixes applied successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Score Gauge (circular, 0-100, color-coded)
// ---------------------------------------------------------------------------

function ScoreGauge({
  score,
  label,
  size = "md",
}: {
  score: number;
  label: string;
  size?: "sm" | "md" | "lg";
}) {
  const dims = { sm: 64, md: 96, lg: 128 };
  const dim = dims[size];
  const strokeWidth = size === "sm" ? 4 : size === "md" ? 6 : 8;
  const radius = (dim - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 80
      ? "text-green-500"
      : score >= 50
        ? "text-yellow-500"
        : "text-red-500";

  const textSize =
    size === "sm" ? "text-sm" : size === "md" ? "text-xl" : "text-3xl";
  const labelSize = size === "sm" ? "text-[8px]" : "text-[10px]";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: dim, height: dim }}>
        <svg
          className="-rotate-90"
          width={dim}
          height={dim}
          viewBox={`0 0 ${dim} ${dim}`}
        >
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="none"
            className="stroke-muted"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="none"
            className={cn("stroke-current transition-all duration-700", color)}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <span
          className={cn(
            "absolute inset-0 flex items-center justify-center font-bold",
            textSize
          )}
        >
          {Math.round(score)}
        </span>
      </div>
      <span className={cn("font-medium text-muted-foreground", labelSize)}>
        {label}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Age Band Compliance
// ---------------------------------------------------------------------------

function AgeBandCompliance({ rules }: { rules: AgeBandRule[] }) {
  return (
    <div className="space-y-1.5">
      <h4 className="text-sm font-semibold">Age Band Compliance</h4>
      <div className="grid grid-cols-2 gap-1.5">
        {rules.map((rule) => (
          <div
            key={rule.rule}
            className={cn(
              "flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs",
              rule.pass
                ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200"
                : "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
            )}
          >
            {rule.pass ? (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
            ) : (
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            )}
            <span className="truncate">{rule.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page Breakdown Table
// ---------------------------------------------------------------------------

function PageBreakdownTable({ pages }: { pages: PageBreakdown[] }) {
  return (
    <div className="space-y-1.5">
      <h4 className="text-sm font-semibold">Per-Page Breakdown</h4>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-14">Page</TableHead>
              <TableHead className="w-20">Words</TableHead>
              <TableHead className="w-28">Longest Sent.</TableHead>
              <TableHead className="w-28">Longest Word</TableHead>
              <TableHead className="w-24">Vocab Level</TableHead>
              <TableHead>Issues</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pages.map((p) => (
              <TableRow key={p.page_number}>
                <TableCell className="font-medium">{p.page_number}</TableCell>
                <TableCell>{p.word_count}</TableCell>
                <TableCell>{p.longest_sentence} words</TableCell>
                <TableCell className="font-mono text-xs">
                  {p.longest_word}
                </TableCell>
                <TableCell>{p.vocab_level}</TableCell>
                <TableCell>
                  {p.issues.length > 0 ? (
                    <Badge variant="destructive" className="text-[10px]">
                      {p.issues.length} issue{p.issues.length > 1 ? "s" : ""}
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="text-[10px] text-green-600"
                    >
                      OK
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Violation List (expandable)
// ---------------------------------------------------------------------------

function ViolationList({ violations }: { violations: Violation[] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (violations.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200">
        <CheckCircle2 className="h-4 w-4" />
        No violations found. Text is fully compliant.
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <h4 className="text-sm font-semibold">
        Flagged Items ({violations.length})
      </h4>
      <div className="space-y-1">
        {violations.map((v, idx) => {
          const isOpen = expandedIdx === idx;
          return (
            <Collapsible
              key={idx}
              open={isOpen}
              onOpenChange={() =>
                setExpandedIdx(isOpen ? null : idx)
              }
            >
              <CollapsibleTrigger className="flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm hover:bg-accent">
                {isOpen ? (
                  <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                )}
                <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                <span className="flex-1 truncate">{v.message}</span>
                {v.page && (
                  <Badge variant="outline" className="ml-auto text-[10px]">
                    Page {v.page}
                    {v.line ? `, Line ${v.line}` : ""}
                  </Badge>
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="px-9 pb-2 pt-1">
                {v.offending_text && (
                  <div className="mb-1.5 rounded bg-red-50 px-2 py-1 text-xs dark:bg-red-950">
                    <span className="font-medium text-red-700 dark:text-red-300">
                      Text:{" "}
                    </span>
                    <span className="font-mono text-red-600 dark:text-red-400">
                      &quot;{v.offending_text}&quot;
                    </span>
                  </div>
                )}
                {v.suggestion && (
                  <div className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-800 dark:bg-blue-950 dark:text-blue-200">
                    <span className="font-medium">Fix: </span>
                    {v.suggestion}
                  </div>
                )}
              </CollapsibleContent>
            </Collapsible>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page-Turn Surprise Map (horizontal timeline)
// ---------------------------------------------------------------------------

function PageTurnSurpriseMap({ entries }: { entries: PageTurnEntry[] }) {
  const maxScore = Math.max(...entries.map((e) => e.surprise_score), 1);

  return (
    <div className="space-y-1.5">
      <h4 className="text-sm font-semibold">Page-Turn Surprise Map</h4>
      <TooltipProvider delayDuration={100}>
        <div className="flex items-end gap-0.5 rounded-md border bg-muted/30 p-3">
          <div className="relative flex flex-1 items-end justify-between gap-px">
            {entries.map((entry) => {
              const normalised = entry.surprise_score / maxScore;
              const dotSize = Math.max(6, normalised * 24);
              return (
                <Tooltip key={entry.page_num}>
                  <TooltipTrigger asChild>
                    <div className="flex flex-col items-center gap-0.5">
                      <div
                        className={cn(
                          "rounded-full transition-all",
                          entry.surprise_score >= 60
                            ? "bg-amber-500"
                            : entry.surprise_score >= 30
                              ? "bg-blue-400"
                              : "bg-muted-foreground/30"
                        )}
                        style={{
                          width: dotSize,
                          height: dotSize,
                        }}
                      />
                      <span className="text-[8px] text-muted-foreground">
                        {entry.page_num}
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top">
                    <p className="font-medium">Page {entry.page_num}</p>
                    <p className="text-xs text-muted-foreground">
                      Surprise: {entry.surprise_score}
                    </p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </div>
      </TooltipProvider>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Rhyme Section
// ---------------------------------------------------------------------------

function RhymeSection({
  rhyme,
  onFixRhymes,
  isFixing,
}: {
  rhyme: RhymeAnalysis;
  onFixRhymes: () => void;
  isFixing: boolean;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Rhyme Analysis</h4>
        <Button
          size="sm"
          variant="outline"
          onClick={onFixRhymes}
          disabled={isFixing || rhyme.issues.length === 0}
          className="gap-1.5"
        >
          <Wand2 className="h-3.5 w-3.5" />
          {isFixing ? "Fixing..." : "AI Fix Rhymes"}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* Pattern detection */}
        <Card className="p-3">
          <p className="text-xs text-muted-foreground">Detected Pattern</p>
          <p className="text-lg font-bold">
            {rhyme.pattern ?? "None detected"}
          </p>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            Scheme: {rhyme.detected_scheme || "N/A"}
          </p>
        </Card>

        {/* Issue count */}
        <Card className="p-3">
          <p className="text-xs text-muted-foreground">Rhyme Issues</p>
          <p
            className={cn(
              "text-lg font-bold",
              rhyme.issues.length === 0 ? "text-green-600" : "text-red-600"
            )}
          >
            {rhyme.issues.length}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {rhyme.issues.length === 0
              ? "All rhymes consistent"
              : "Near-rhymes & meter issues"}
          </p>
        </Card>
      </div>

      {/* Issue list */}
      {rhyme.issues.length > 0 && (
        <div className="space-y-1">
          {rhyme.issues.map((issue, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
            >
              <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
              <span>{issue}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Panel
// ---------------------------------------------------------------------------

export function TextAnalysisPanel({
  bookId,
  ageRange,
  storyMode,
}: TextAnalysisPanelProps) {
  const { data, isLoading, error } = useTextAnalysis(bookId);
  const fixRhymes = useFixRhymes(bookId);
  const isRhyming = storyMode === "rhyming";

  if (isLoading) {
    return (
      <Card className="flex h-64 items-center justify-center">
        <p className="text-sm text-muted-foreground">
          Analyzing text readability...
        </p>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="flex h-64 items-center justify-center">
        <p className="text-sm text-red-500">
          {error ? extractApiError(error) : "No analysis data available."}
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Score gauges row ─────────────────────────────────── */}
      <div className="flex flex-wrap items-start justify-center gap-6 rounded-lg border bg-card p-4">
        <ScoreGauge
          score={data.readability_score}
          label="Readability"
          size="lg"
        />
        <ScoreGauge
          score={data.rhythm_score}
          label="Read-Aloud Rhythm"
          size="md"
        />
        <ScoreGauge
          score={data.look_inside_score}
          label="Look Inside"
          size="md"
        />
      </div>

      {/* ── Age band compliance ──────────────────────────────── */}
      <AgeBandCompliance rules={data.age_band_rules} />

      {/* ── Per-page breakdown ───────────────────────────────── */}
      <PageBreakdownTable pages={data.page_breakdown} />

      {/* ── Violations ───────────────────────────────────────── */}
      <ViolationList violations={data.violations} />

      {/* ── Page-Turn Surprise Map ───────────────────────────── */}
      {data.page_turn_map.length > 0 && (
        <PageTurnSurpriseMap entries={data.page_turn_map} />
      )}

      {/* ── Rhyme section (only for rhyming story mode) ─────── */}
      {isRhyming && data.rhyme_analysis && (
        <RhymeSection
          rhyme={data.rhyme_analysis}
          onFixRhymes={() => fixRhymes.mutate()}
          isFixing={fixRhymes.isPending}
        />
      )}
    </div>
  );
}
