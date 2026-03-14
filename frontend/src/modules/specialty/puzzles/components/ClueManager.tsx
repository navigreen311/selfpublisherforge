"use client";

import { useState, useCallback } from "react";
import {
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Edit3,
  Filter,
  Wand2,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ClueStyle } from "../hooks";

// ─── Types ──────────────────────────────────────────────────────────────────

interface Clue {
  id: string;
  puzzle_number: number;
  clue_text: string;
  answer: string;
  style: ClueStyle;
  ambiguity_score: number;
  status: "ok" | "flagged" | "error";
}

interface QAResult {
  score: number;
  issues: {
    type: "duplicate_phrasing" | "inconsistent_tense" | "inconsistent_style" | "grade_level";
    description: string;
    affected_clues: string[];
    suggestion: string;
  }[];
}

interface ClueManagerProps {
  bookId: string;
  clues: Clue[];
  onEditClue: (clueId: string, updates: Partial<Clue>) => void;
  onAISuggest: (clueId: string) => void;
  onRunQA: () => void;
  onAutoFixAll: () => void;
  qaResults?: QAResult | null;
  isSuggesting?: boolean;
  isRunningQA?: boolean;
  isAutoFixing?: boolean;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const STYLE_LABELS: Record<ClueStyle, string> = {
  standard: "Standard",
  kid_friendly: "Kid-friendly",
  trivia: "Trivia",
  themed: "Themed",
};

const AMBIGUITY_THRESHOLD_WARNING = 0.4;
const AMBIGUITY_THRESHOLD_ERROR = 0.7;

function getAmbiguityStyle(score: number): string {
  if (score >= AMBIGUITY_THRESHOLD_ERROR) return "bg-red-50";
  if (score >= AMBIGUITY_THRESHOLD_WARNING) return "bg-yellow-50";
  return "";
}

function getAmbiguityBadge(score: number): { label: string; className: string } {
  if (score >= AMBIGUITY_THRESHOLD_ERROR)
    return { label: "High", className: "bg-red-100 text-red-800" };
  if (score >= AMBIGUITY_THRESHOLD_WARNING)
    return { label: "Medium", className: "bg-yellow-100 text-yellow-800" };
  return { label: "Low", className: "bg-green-100 text-green-800" };
}

const QA_ISSUE_STYLES: Record<string, string> = {
  duplicate_phrasing: "bg-blue-100 text-blue-800",
  inconsistent_tense: "bg-orange-100 text-orange-800",
  inconsistent_style: "bg-purple-100 text-purple-800",
  grade_level: "bg-red-100 text-red-800",
};

// ─── Component ──────────────────────────────────────────────────────────────

export function ClueManager({
  bookId,
  clues,
  onEditClue,
  onAISuggest,
  onRunQA,
  onAutoFixAll,
  qaResults,
  isSuggesting,
  isRunningQA,
  isAutoFixing,
}: ClueManagerProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editAnswer, setEditAnswer] = useState("");
  const [styleFilter, setStyleFilter] = useState<ClueStyle | "all">("all");

  const filteredClues =
    styleFilter === "all"
      ? clues
      : clues.filter((c) => c.style === styleFilter);

  const flaggedCount = clues.filter(
    (c) => c.ambiguity_score >= AMBIGUITY_THRESHOLD_WARNING
  ).length;

  // ── Inline editing ──────────────────────────────────────────────────────
  const startEdit = useCallback((clue: Clue) => {
    setEditingId(clue.id);
    setEditText(clue.clue_text);
    setEditAnswer(clue.answer);
  }, []);

  const saveEdit = useCallback(() => {
    if (!editingId) return;
    onEditClue(editingId, { clue_text: editText, answer: editAnswer });
    setEditingId(null);
  }, [editingId, editText, editAnswer, onEditClue]);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setEditText("");
    setEditAnswer("");
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Clue Manager</h2>
          <p className="text-sm text-muted-foreground">
            {clues.length} clue{clues.length !== 1 ? "s" : ""} across all
            puzzles
            {flaggedCount > 0 && (
              <span className="text-amber-600 ml-2">
                ({flaggedCount} flagged for ambiguity)
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRunQA} disabled={isRunningQA}>
            {isRunningQA ? (
              <>
                <CheckCircle className="h-4 w-4 mr-2 animate-pulse" />
                Running QA...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Run Clue QA
              </>
            )}
          </Button>
          <Button variant="outline" onClick={onAutoFixAll} disabled={isAutoFixing}>
            {isAutoFixing ? (
              <>
                <Wand2 className="h-4 w-4 mr-2 animate-pulse" />
                Fixing...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4 mr-2" />
                Auto-Fix All
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Style Filter */}
      <div className="flex items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Label className="text-sm">Clue Style Filter</Label>
        <Select
          value={styleFilter}
          onValueChange={(v) => setStyleFilter(v as ClueStyle | "all")}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Styles</SelectItem>
            <SelectItem value="standard">Standard</SelectItem>
            <SelectItem value="kid_friendly">Kid-friendly</SelectItem>
            <SelectItem value="trivia">Trivia</SelectItem>
            <SelectItem value="themed">Themed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Clue Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[80px]">Puzzle #</TableHead>
              <TableHead>Clue Text</TableHead>
              <TableHead className="w-[120px]">Answer</TableHead>
              <TableHead className="w-[110px]">Style</TableHead>
              <TableHead className="w-[120px]">Ambiguity</TableHead>
              <TableHead className="w-[80px]">Status</TableHead>
              <TableHead className="w-[140px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredClues.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <p className="text-muted-foreground">
                    {clues.length === 0
                      ? "No clues available. Generate puzzles first."
                      : "No clues match the selected filter."}
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              filteredClues.map((clue) => {
                const ambiguity = getAmbiguityBadge(clue.ambiguity_score);
                const isEditing = editingId === clue.id;

                return (
                  <TableRow
                    key={clue.id}
                    className={getAmbiguityStyle(clue.ambiguity_score)}
                  >
                    <TableCell className="font-medium">
                      #{clue.puzzle_number}
                    </TableCell>
                    <TableCell>
                      {isEditing ? (
                        <Input
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          className="h-8"
                        />
                      ) : (
                        <span className="text-sm">{clue.clue_text}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {isEditing ? (
                        <Input
                          value={editAnswer}
                          onChange={(e) => setEditAnswer(e.target.value)}
                          className="h-8"
                        />
                      ) : (
                        <span className="font-mono text-sm">{clue.answer}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {STYLE_LABELS[clue.style]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={ambiguity.className}
                      >
                        {ambiguity.label} ({(clue.ambiguity_score * 100).toFixed(0)}%)
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {clue.status === "ok" ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : clue.status === "flagged" ? (
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {isEditing ? (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={saveEdit}
                            >
                              <Save className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={cancelEdit}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => startEdit(clue)}
                            >
                              <Edit3 className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onAISuggest(clue.id)}
                              disabled={isSuggesting}
                            >
                              <Sparkles className="h-3.5 w-3.5" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* ── Book-Level QA Results ──────────────────────────────────────── */}
      {qaResults && (
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Book-Level Clue QA Results</h3>
            <Badge
              variant="secondary"
              className={
                qaResults.score >= 80
                  ? "bg-green-100 text-green-800"
                  : qaResults.score >= 60
                  ? "bg-yellow-100 text-yellow-800"
                  : "bg-red-100 text-red-800"
              }
            >
              Score: {qaResults.score}/100
            </Badge>
          </div>

          {qaResults.issues.length === 0 ? (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-lg p-3">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm">
                All clues passed QA checks. No issues found.
              </span>
            </div>
          ) : (
            <div className="space-y-3">
              {qaResults.issues.map((issue, i) => (
                <div
                  key={i}
                  className="border rounded-lg p-3 space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className={
                        QA_ISSUE_STYLES[issue.type] || "bg-gray-100 text-gray-800"
                      }
                    >
                      {issue.type.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-sm">{issue.description}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Affected clues: {issue.affected_clues.join(", ")}
                  </p>
                  <p className="text-sm text-green-700">
                    Suggestion: {issue.suggestion}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
