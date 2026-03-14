"use client";

import { useState, useMemo } from "react";
import {
  BookOpen,
  CheckCircle,
  XCircle,
  RefreshCw,
  Eye,
  LayoutGrid,
  ArrowLeft,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AnswerKeyPosition, Puzzle } from "../hooks";

// ─── Types ──────────────────────────────────────────────────────────────────

interface VerificationCheck {
  label: string;
  passed: boolean;
  detail?: string;
}

interface AnswerKeyPanelProps {
  bookId: string;
  puzzles: Puzzle[];
  answerKeyPosition: AnswerKeyPosition;
  onPositionChange: (position: AnswerKeyPosition) => void;
  onGenerate: () => void;
  onVerifyAll: () => void;
  verificationChecks?: VerificationCheck[];
  isGenerating?: boolean;
  isVerifying?: boolean;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const POSITION_LABELS: Record<AnswerKeyPosition, string> = {
  back: "Back of Book",
  reverse: "Reverse of Page",
  none: "None",
};

const POSITION_DESCRIPTIONS: Record<AnswerKeyPosition, string> = {
  back: "All answer keys collected at the end of the book",
  reverse: "Each answer appears on the back of its puzzle page",
  none: "No answer key included (e.g., for classroom use)",
};

// ─── Component ──────────────────────────────────────────────────────────────

export function AnswerKeyPanel({
  bookId,
  puzzles,
  answerKeyPosition,
  onPositionChange,
  onGenerate,
  onVerifyAll,
  verificationChecks,
  isGenerating,
  isVerifying,
}: AnswerKeyPanelProps) {
  const [compactLayout, setCompactLayout] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);

  const keysGenerated = puzzles.filter((p) => p.answer_key_url).length;
  const totalPuzzles = puzzles.length;
  const allGenerated = keysGenerated === totalPuzzles && totalPuzzles > 0;

  // Default checks when none provided
  const checks: VerificationCheck[] = verificationChecks || [
    {
      label: "All keys generated",
      passed: allGenerated,
      detail: `${keysGenerated}/${totalPuzzles} keys generated`,
    },
    {
      label: "All keys match puzzles",
      passed: false,
      detail: "Run verification to check",
    },
    {
      label: "Numbering correct",
      passed: false,
      detail: "Run verification to check",
    },
  ];

  const allPassed = checks.every((c) => c.passed);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Answer Key</h2>
          <p className="text-sm text-muted-foreground">
            Manage answer key generation and verification for{" "}
            {totalPuzzles} puzzle{totalPuzzles !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={onVerifyAll}
            disabled={isVerifying || totalPuzzles === 0}
          >
            {isVerifying ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Verify All
              </>
            )}
          </Button>
          <Button
            onClick={onGenerate}
            disabled={isGenerating || totalPuzzles === 0 || answerKeyPosition === "none"}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <BookOpen className="h-4 w-4 mr-2" />
                Generate Answer Keys
              </>
            )}
          </Button>
        </div>
      </div>

      {/* ── Position Selector ──────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-3">
        <Label className="font-medium">Answer Key Position</Label>
        <Select
          value={answerKeyPosition}
          onValueChange={(v) => onPositionChange(v as AnswerKeyPosition)}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="back">Back of Book</SelectItem>
            <SelectItem value="reverse">Reverse of Page</SelectItem>
            <SelectItem value="none">None</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          {POSITION_DESCRIPTIONS[answerKeyPosition]}
        </p>
      </div>

      {/* ── Compact Layout Toggle ──────────────────────────────────────── */}
      {answerKeyPosition !== "none" && (
        <div className="flex items-center justify-between border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <LayoutGrid className="h-5 w-5 text-muted-foreground" />
            <div>
              <Label className="font-medium">Compact Layout</Label>
              <p className="text-sm text-muted-foreground">
                4 answers per page to reduce total page count
              </p>
            </div>
          </div>
          <Switch checked={compactLayout} onCheckedChange={setCompactLayout} />
        </div>
      )}

      {/* ── Verification Status ────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Verification Status</h3>
          <Badge
            variant="secondary"
            className={
              allPassed
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }
          >
            {allPassed ? "All Passed" : "Needs Attention"}
          </Badge>
        </div>

        <div className="space-y-2">
          {checks.map((check, i) => (
            <div
              key={i}
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
        </div>
      </div>

      {/* ── Answer Key Preview ─────────────────────────────────────────── */}
      {answerKeyPosition !== "none" && (
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Answer Key Preview
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPreviewVisible(!previewVisible)}
            >
              {previewVisible ? "Hide Preview" : "Show Preview"}
            </Button>
          </div>

          {previewVisible && (
            <div className="space-y-4">
              {puzzles.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  No puzzles to preview.
                </p>
              ) : (
                <div
                  className={`grid gap-4 ${
                    compactLayout
                      ? "grid-cols-1 md:grid-cols-2"
                      : "grid-cols-1"
                  }`}
                >
                  {puzzles.map((puzzle) => (
                    <div
                      key={puzzle.id}
                      className="border rounded-lg p-4 bg-white"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium">
                          Puzzle #{puzzle.puzzle_number} -{" "}
                          {puzzle.puzzle_type.replace(/_/g, " ")}
                        </h4>
                        {puzzle.answer_key_url ? (
                          <Badge
                            variant="secondary"
                            className="bg-green-100 text-green-800"
                          >
                            Generated
                          </Badge>
                        ) : (
                          <Badge
                            variant="secondary"
                            className="bg-gray-100 text-gray-700"
                          >
                            Pending
                          </Badge>
                        )}
                      </div>

                      {puzzle.solution_data ? (
                        <div className="bg-muted/30 rounded p-3">
                          <pre className="text-xs font-mono whitespace-pre-wrap overflow-x-auto">
                            {JSON.stringify(puzzle.solution_data, null, 2)}
                          </pre>
                        </div>
                      ) : puzzle.word_list && puzzle.word_list.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {puzzle.word_list.map((word, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {word}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground italic">
                          Answer key not yet generated.
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
