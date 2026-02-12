"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Wrench,
  Download,
  RefreshCw,
  Shield,
  FileAudio,
} from "lucide-react";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type CheckStatus = "pass" | "fail" | "warn" | "pending";

interface ACXCheck {
  id: string;
  label: string;
  description: string;
  status: CheckStatus;
  actual?: string;
  expected?: string;
  fixable: boolean;
}

interface ChapterValidation {
  chapterId: string;
  chapterTitle: string;
  chapterNumber: number;
  checks: ACXCheck[];
}

interface ACXValidationResult {
  overallStatus: "ready" | "issues" | "not_validated";
  score: number;
  totalChecks: number;
  passed: number;
  failed: number;
  warnings: number;
  globalChecks: ACXCheck[];
  chapterResults: ChapterValidation[];
  validatedAt?: string;
}

interface ACXValidatorProps {
  projectId: string;
  validationResult?: ACXValidationResult;
  onValidate: () => void;
  onAutoFix: (issues: string[]) => void;
  onExportValidated?: () => void;
  isValidating: boolean;
  isFixing?: boolean;
}

// ---------------------------------------------------------------------------
// ACX requirement definitions
// ---------------------------------------------------------------------------

const ACX_REQUIREMENTS: { id: string; label: string; description: string }[] = [
  { id: "file_format", label: "File Format", description: "MP3 CBR 192kbps" },
  { id: "sample_rate", label: "Sample Rate", description: "44.1kHz" },
  { id: "mono_channel", label: "Mono Channel", description: "Single audio channel" },
  { id: "peak_level", label: "Peak Level", description: "\u2264 -3dB" },
  { id: "rms_level", label: "RMS Level", description: "Between -23dB and -18dB" },
  { id: "noise_floor", label: "Noise Floor", description: "< -60dB" },
  { id: "head_room_tone", label: "Head Room Tone", description: "0.5\u20131 second" },
  { id: "tail_room_tone", label: "Tail Room Tone", description: "1\u20135 seconds" },
  { id: "chapter_length", label: "Chapter Length", description: "\u2264 120 minutes" },
  { id: "opening_credits", label: "Opening Credits", description: "Opening credits file present" },
  { id: "closing_credits", label: "Closing Credits", description: "Closing credits file present" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStatusIcon(status: CheckStatus) {
  switch (status) {
    case "pass":
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    case "fail":
      return <XCircle className="h-5 w-5 text-red-600" />;
    case "warn":
      return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    default:
      return <div className="h-5 w-5 rounded-full border-2 border-gray-300" />;
  }
}

function getStatusBadge(status: "ready" | "issues" | "not_validated", failed: number) {
  switch (status) {
    case "ready":
      return (
        <Badge className="bg-green-100 text-green-800 hover:bg-green-100 text-sm px-3 py-1">
          <CheckCircle className="h-4 w-4 mr-1.5" />
          ACX Ready
        </Badge>
      );
    case "issues":
      return (
        <Badge
          className={`text-sm px-3 py-1 ${
            failed > 3
              ? "bg-red-100 text-red-800 hover:bg-red-100"
              : "bg-yellow-100 text-yellow-800 hover:bg-yellow-100"
          }`}
        >
          <AlertTriangle className="h-4 w-4 mr-1.5" />
          {failed} issue{failed !== 1 ? "s" : ""} to fix
        </Badge>
      );
    default:
      return (
        <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100 text-sm px-3 py-1">
          Not Validated
        </Badge>
      );
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function CheckRow({ check }: { check: ACXCheck }) {
  return (
    <div className="flex items-center justify-between py-2.5 px-1 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-3">
        {getStatusIcon(check.status)}
        <div>
          <p className="text-sm font-medium text-gray-900">{check.label}</p>
          <p className="text-xs text-gray-500">{check.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {check.status === "fail" && check.actual && (
          <span className="text-xs text-red-600">
            Got: {check.actual} | Expected: {check.expected}
          </span>
        )}
        {check.fixable && check.status === "fail" && (
          <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100 text-xs">
            <Wrench className="h-3 w-3 mr-1" />
            Auto-fixable
          </Badge>
        )}
      </div>
    </div>
  );
}

function ChapterAccordion({
  chapter,
  isOpen,
  onToggle,
}: {
  chapter: ChapterValidation;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const chapterPassed = chapter.checks.filter((c) => c.status === "pass").length;
  const chapterTotal = chapter.checks.length;
  const allPassed = chapterPassed === chapterTotal;

  return (
    <div className="rounded-lg border border-gray-200">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-500" />
          )}
          <FileAudio className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-900">
            Ch. {chapter.chapterNumber}: {chapter.chapterTitle}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {chapterPassed}/{chapterTotal} passed
          </span>
          {allPassed ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <XCircle className="h-4 w-4 text-red-600" />
          )}
        </div>
      </button>
      {isOpen && (
        <div className="border-t border-gray-200 px-4 py-2">
          {chapter.checks.map((check) => (
            <CheckRow key={check.id} check={check} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ACXValidator({
  projectId,
  validationResult,
  onValidate,
  onAutoFix,
  onExportValidated,
  isValidating,
  isFixing = false,
}: ACXValidatorProps) {
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());

  const fixableIssues = useMemo(() => {
    if (!validationResult) return [];
    const issues: string[] = [];
    for (const check of validationResult.globalChecks) {
      if (check.fixable && check.status === "fail") {
        issues.push(check.id);
      }
    }
    for (const chapter of validationResult.chapterResults) {
      for (const check of chapter.checks) {
        if (check.fixable && check.status === "fail") {
          issues.push(`${chapter.chapterId}:${check.id}`);
        }
      }
    }
    return issues;
  }, [validationResult]);

  const toggleChapter = (chapterId: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  };

  const handleAutoFix = () => {
    if (fixableIssues.length === 0) {
      toast.error("No auto-fixable issues found");
      return;
    }
    onAutoFix(fixableIssues);
  };

  const handleExport = () => {
    if (onExportValidated) {
      onExportValidated();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">ACX Validation</h2>
          <p className="mt-1 text-sm text-gray-600">
            Pre-submission validation against ACX/Audible requirements
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onValidate}
            disabled={isValidating}
            className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {isValidating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Validating...
              </>
            ) : (
              <>
                <Shield className="h-4 w-4" />
                Run Validation
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isValidating && (
        <Card className="p-12 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
          <h3 className="mt-4 font-semibold text-gray-900">Running ACX Validation...</h3>
          <p className="mt-2 text-sm text-gray-600">
            Checking audio files against all ACX requirements
          </p>
        </Card>
      )}

      {/* Empty State */}
      {!validationResult && !isValidating && (
        <Card className="p-12 text-center">
          <Shield className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 font-semibold text-gray-900">No Validation Results</h3>
          <p className="mt-2 text-sm text-gray-600">
            Run a validation check to verify your audiobook meets ACX requirements
          </p>
          <button
            onClick={onValidate}
            className="mt-6 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Run First Validation
          </button>
        </Card>
      )}

      {/* Results */}
      {validationResult && !isValidating && (
        <>
          {/* Overall Status Card */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Shield className="h-6 w-6 text-indigo-600" />
                <div>
                  <h3 className="font-semibold text-gray-900">Overall Status</h3>
                  {validationResult.validatedAt && (
                    <p className="text-sm text-gray-500">
                      Last checked: {new Date(validationResult.validatedAt).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
              {getStatusBadge(
                validationResult.overallStatus,
                validationResult.failed,
              )}
            </div>

            {/* Score */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Compliance Score</span>
                <span className="text-2xl font-bold text-indigo-600">
                  {validationResult.score}%
                </span>
              </div>
              <Progress value={validationResult.score} className="h-2" />
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{validationResult.passed}</p>
                <p className="text-xs font-medium text-green-800">Passed</p>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center">
                <p className="text-2xl font-bold text-red-600">{validationResult.failed}</p>
                <p className="text-xs font-medium text-red-800">Failed</p>
              </div>
              <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{validationResult.warnings}</p>
                <p className="text-xs font-medium text-yellow-800">Warnings</p>
              </div>
            </div>
          </Card>

          {/* Action Buttons */}
          {(fixableIssues.length > 0 || validationResult.overallStatus === "ready") && (
            <div className="flex items-center gap-3">
              {fixableIssues.length > 0 && (
                <button
                  onClick={handleAutoFix}
                  disabled={isFixing}
                  className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  <Wrench className="h-4 w-4" />
                  {isFixing
                    ? "Fixing..."
                    : `Auto-Fix ${fixableIssues.length} Issue${fixableIssues.length !== 1 ? "s" : ""}`}
                </button>
              )}
              {validationResult.overallStatus === "ready" && onExportValidated && (
                <button
                  onClick={handleExport}
                  className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                >
                  <Download className="h-4 w-4" />
                  Export Validated Files
                </button>
              )}
            </div>
          )}

          {/* Global Checks */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-700">
                ACX Requirements Checklist
              </CardTitle>
            </CardHeader>
            <CardContent>
              {validationResult.globalChecks.map((check) => (
                <CheckRow key={check.id} check={check} />
              ))}
            </CardContent>
          </Card>

          {/* Per-Chapter Results */}
          {validationResult.chapterResults.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Per-Chapter Results ({validationResult.chapterResults.length} chapters)
              </h3>
              <div className="space-y-2">
                {validationResult.chapterResults.map((chapter) => (
                  <ChapterAccordion
                    key={chapter.chapterId}
                    chapter={chapter}
                    isOpen={expandedChapters.has(chapter.chapterId)}
                    onToggle={() => toggleChapter(chapter.chapterId)}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
