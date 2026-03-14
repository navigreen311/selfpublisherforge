"use client";

import { useState, useCallback, useMemo } from "react";
import {
  Sparkles,
  Upload,
  ShieldCheck,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { WordDifficulty } from "../hooks";

// ─── Types ──────────────────────────────────────────────────────────────────

interface RemovedWord {
  word: string;
  reason: string;
}

type RegionalEnglish = "US" | "UK" | "CA" | "AU";

const REASON_STYLES: Record<string, string> = {
  offensive: "bg-red-100 text-red-800",
  trademark: "bg-purple-100 text-purple-800",
  abbreviation: "bg-orange-100 text-orange-800",
  spelling: "bg-yellow-100 text-yellow-800",
  duplicate: "bg-blue-100 text-blue-800",
  "too long": "bg-gray-100 text-gray-800",
  "too short": "bg-gray-100 text-gray-800",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "text-green-600",
  medium: "text-yellow-600",
  hard: "text-red-600",
};

// ─── Props ──────────────────────────────────────────────────────────────────

interface WordListManagerProps {
  words: string[];
  onWordsChange: (words: string[]) => void;
  onAIGenerate: (theme: string, count: number, difficulty: WordDifficulty) => void;
  onSanitize: (words: string[]) => void;
  onImportFile: (file: File) => void;
  sanitizationResults?: {
    clean_words: string[];
    removed: RemovedWord[];
  } | null;
  isGenerating?: boolean;
  isSanitizing?: boolean;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function estimateWordDifficulty(word: string): "easy" | "medium" | "hard" {
  const len = word.length;
  if (len <= 5) return "easy";
  if (len <= 9) return "medium";
  return "hard";
}

// ─── Component ──────────────────────────────────────────────────────────────

export function WordListManager({
  words,
  onWordsChange,
  onAIGenerate,
  onSanitize,
  onImportFile,
  sanitizationResults,
  isGenerating,
  isSanitizing,
}: WordListManagerProps) {
  const [themeInput, setThemeInput] = useState("");
  const [wordCount, setWordCount] = useState(20);
  const [difficulty, setDifficulty] = useState<WordDifficulty>("standard");
  const [regionalEnglish, setRegionalEnglish] = useState<RegionalEnglish>("US");
  const [manualText, setManualText] = useState(words.join("\n"));

  // Keep manual text and words in sync
  const handleManualChange = useCallback(
    (value: string) => {
      setManualText(value);
      const parsed = value
        .split("\n")
        .map((w) => w.trim())
        .filter(Boolean);
      onWordsChange(parsed);
    },
    [onWordsChange]
  );

  const handleGenerate = useCallback(() => {
    if (!themeInput.trim()) return;
    onAIGenerate(themeInput.trim(), wordCount, difficulty);
  }, [themeInput, wordCount, difficulty, onAIGenerate]);

  const handleFileImport = useCallback(() => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".txt,.csv";
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) onImportFile(file);
    };
    input.click();
  }, [onImportFile]);

  const wordDifficulties = useMemo(
    () => words.map((w) => ({ word: w, difficulty: estimateWordDifficulty(w) })),
    [words]
  );

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Word List Manager</h2>

      {/* ── Theme-Based Generation ─────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <h3 className="font-medium flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          AI Theme-Based Generation
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-1">
            <Label>Theme</Label>
            <Input
              value={themeInput}
              onChange={(e) => setThemeInput(e.target.value)}
              placeholder="e.g., Ocean Animals"
            />
          </div>
          <div>
            <Label>Word Count</Label>
            <Input
              type="number"
              value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              min={5}
              max={100}
            />
          </div>
          <div>
            <Label>Difficulty</Label>
            <Select
              value={difficulty}
              onValueChange={(v) => setDifficulty(v as WordDifficulty)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simple">Simple (3-6 letters)</SelectItem>
                <SelectItem value="standard">Standard (4-10 letters)</SelectItem>
                <SelectItem value="advanced">Advanced (6-15 letters)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button
              onClick={handleGenerate}
              disabled={!themeInput.trim() || isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Sparkles className="h-4 w-4 mr-2 animate-pulse" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  AI Generate
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* ── Regional English Selector ──────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <Label>Regional English</Label>
        <Select
          value={regionalEnglish}
          onValueChange={(v) => setRegionalEnglish(v as RegionalEnglish)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="US">US English</SelectItem>
            <SelectItem value="UK">UK English</SelectItem>
            <SelectItem value="CA">Canadian English</SelectItem>
            <SelectItem value="AU">Australian English</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">
          Affects spelling validation (color vs colour, etc.)
        </span>
      </div>

      {/* ── Manual Word List Editor ────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Word List (one word per line)</Label>
            <Button variant="outline" size="sm" onClick={handleFileImport}>
              <Upload className="h-3.5 w-3.5 mr-1.5" />
              Import from File
            </Button>
          </div>
          <Textarea
            value={manualText}
            onChange={(e) => handleManualChange(e.target.value)}
            rows={14}
            placeholder="DOLPHIN&#10;WHALE&#10;OCTOPUS&#10;STARFISH&#10;..."
            className="font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            {words.length} word{words.length !== 1 ? "s" : ""} entered
          </p>
        </div>

        {/* ── Word Difficulty Indicators ───────────────────────────────── */}
        <div className="space-y-3">
          <Label>Word Difficulty Indicators</Label>
          <div className="border rounded-lg max-h-[340px] overflow-y-auto">
            {wordDifficulties.length === 0 ? (
              <p className="text-sm text-muted-foreground p-4 text-center">
                No words added yet.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr>
                    <th className="text-left py-2 px-3 font-medium">Word</th>
                    <th className="text-left py-2 px-3 font-medium">
                      Length
                    </th>
                    <th className="text-left py-2 px-3 font-medium">
                      Difficulty
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {wordDifficulties.map(({ word, difficulty: d }, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-1.5 px-3 font-mono">{word}</td>
                      <td className="py-1.5 px-3 text-muted-foreground">
                        {word.length}
                      </td>
                      <td className="py-1.5 px-3">
                        <span
                          className={`text-xs font-medium ${DIFFICULTY_COLORS[d]}`}
                        >
                          {d}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* ── Sanitization Panel ─────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            Word List Sanitization
          </h3>
          <Button
            variant="outline"
            onClick={() => onSanitize(words)}
            disabled={words.length === 0 || isSanitizing}
          >
            {isSanitizing ? (
              <>
                <ShieldCheck className="h-4 w-4 mr-2 animate-pulse" />
                Running...
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4 mr-2" />
                Run Sanitization
              </>
            )}
          </Button>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Info className="h-3 w-3" />
            Checks:
          </span>
          <span>Offensive language</span>
          <span>Trademarks</span>
          <span>Abbreviations</span>
          <span>Spelling</span>
          <span>Duplicates</span>
          <span>Length validation</span>
        </div>

        {sanitizationResults && (
          <div className="space-y-3">
            {sanitizationResults.removed.length === 0 ? (
              <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-lg p-3">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm">
                  Word list is clean. All {sanitizationResults.clean_words.length}{" "}
                  words passed sanitization.
                </span>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 text-amber-700 bg-amber-50 rounded-lg p-3">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">
                    {sanitizationResults.removed.length} word
                    {sanitizationResults.removed.length !== 1 ? "s" : ""} removed.{" "}
                    {sanitizationResults.clean_words.length} words remaining.
                  </span>
                </div>

                <div className="border rounded-lg max-h-[200px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-background border-b">
                      <tr>
                        <th className="text-left py-2 px-3 font-medium">
                          Removed Word
                        </th>
                        <th className="text-left py-2 px-3 font-medium">
                          Reason
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sanitizationResults.removed.map((item, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="py-1.5 px-3 font-mono line-through text-muted-foreground">
                            {item.word}
                          </td>
                          <td className="py-1.5 px-3">
                            <Badge
                              variant="secondary"
                              className={
                                REASON_STYLES[item.reason] ||
                                "bg-gray-100 text-gray-800"
                              }
                            >
                              {item.reason}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onWordsChange(sanitizationResults.clean_words)}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                  Apply: Use Clean List
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
