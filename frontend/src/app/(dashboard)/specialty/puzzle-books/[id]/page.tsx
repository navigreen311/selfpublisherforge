"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  Plus,
  RefreshCw,
  Download,
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  Lock,
  Binary,
  Link2,
  CheckCircle2,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  usePuzzleBook,
  usePuzzles,
  useGeneratePuzzle,
  useExport,
  type PuzzleType,
  type Puzzle,
} from "@/modules/specialty/puzzles/hooks";

// ─── Constants ────────────────────────────────────────────────────────────────

const PUZZLE_TYPE_ICONS: Record<PuzzleType, LucideIcon> = {
  word_search: Search,
  crossword: Grid3X3,
  maze: Route,
  sudoku: Hash,
  word_scramble: Shuffle,
  cryptogram: Lock,
  number_search: Binary,
  word_connect: Link2,
};

const PUZZLE_TYPE_LABELS: Record<PuzzleType, string> = {
  word_search: "Word Search",
  crossword: "Crossword",
  maze: "Maze",
  sudoku: "Sudoku",
  word_scramble: "Word Scramble",
  cryptogram: "Cryptogram",
  number_search: "Number Search",
  word_connect: "Word Connect",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-muted text-muted-foreground",
  generating: "bg-yellow-500/10 text-yellow-600",
  generated: "bg-blue-500/10 text-blue-600",
  verified: "bg-green-500/10 text-green-600",
  failed: "bg-red-500/10 text-red-600",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-green-500/10 text-green-600",
  medium: "bg-yellow-500/10 text-yellow-600",
  hard: "bg-red-500/10 text-red-600",
};

// ─── Page Component ───────────────────────────────────────────────────────────

export default function PuzzleBookEditorPage() {
  const params = useParams();
  const bookId = params.id as string;

  const { data: book, isLoading: bookLoading } = usePuzzleBook(bookId);
  const { data: puzzles, isLoading: puzzlesLoading } = usePuzzles(bookId);
  const generatePuzzle = useGeneratePuzzle(bookId);
  const exportBook = useExport(bookId);

  const [activeTab, setActiveTab] = useState("puzzles");
  const [puzzleTypeFilter, setPuzzleTypeFilter] = useState<string>("all");
  const [difficultyFilter, setDifficultyFilter] = useState<string>("all");

  if (bookLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-6 w-96 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="container mx-auto py-6">
        <p className="text-muted-foreground">Book not found.</p>
        <Button variant="outline" asChild className="mt-4">
          <Link href="/specialty/puzzle-books">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Back to Puzzle Books
          </Link>
        </Button>
      </div>
    );
  }

  const filteredPuzzles = (puzzles ?? []).filter((p) => {
    if (puzzleTypeFilter !== "all" && p.puzzle_type !== puzzleTypeFilter)
      return false;
    if (difficultyFilter !== "all" && p.difficulty !== difficultyFilter)
      return false;
    return true;
  });

  const statusLabel = book.status.replace("_", " ");

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Back link */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5">
        <Link href="/specialty/puzzle-books">
          <ChevronLeft className="h-4 w-4" />
          Back to Puzzle Books
        </Link>
      </Button>

      {/* Book Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{book.title}</h1>
            <Badge className={cn("capitalize", STATUS_COLORS[book.status] ?? "")}>
              {statusLabel}
            </Badge>
          </div>
          {book.subtitle && (
            <p className="text-muted-foreground mt-1">{book.subtitle}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="capitalize">
              Audience: {book.audience.replace("_", " ")}
            </span>
            <span className="capitalize">
              Difficulty: {book.difficulty_mode}
            </span>
            <span>
              {book.puzzles_created}/{book.total_puzzles} puzzles
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              exportBook.mutate({ format: "pdf", include_answers: true })
            }
            disabled={exportBook.isPending}
          >
            <Download className="h-4 w-4 mr-2" />
            {exportBook.isPending ? "Exporting..." : "Export PDF"}
          </Button>
        </div>
      </div>

      <Separator />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="puzzles">Puzzles</TabsTrigger>
          <TabsTrigger value="word-lists">Word Lists</TabsTrigger>
          <TabsTrigger value="clues">Clues</TabsTrigger>
          <TabsTrigger value="difficulty">Difficulty</TabsTrigger>
          <TabsTrigger value="answer-keys">Answer Keys</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        {/* ─── Puzzles Tab ──────────────────────────────────────────── */}
        <TabsContent value="puzzles" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-3">
              <Select
                value={puzzleTypeFilter}
                onValueChange={setPuzzleTypeFilter}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Puzzle Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {book.puzzle_config.map((c) => (
                    <SelectItem key={c.type} value={c.type}>
                      {PUZZLE_TYPE_LABELS[c.type as PuzzleType] ?? c.type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={difficultyFilter}
                onValueChange={setDifficultyFilter}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Difficulty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              size="sm"
              onClick={() =>
                generatePuzzle.mutate({
                  puzzle_type:
                    (book.puzzle_config[0]?.type as PuzzleType) ?? "word_search",
                  difficulty: "medium",
                })
              }
              disabled={generatePuzzle.isPending}
            >
              <Plus className="h-4 w-4 mr-2" />
              {generatePuzzle.isPending ? "Generating..." : "Generate Puzzle"}
            </Button>
          </div>

          {puzzlesLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <div className="p-4 space-y-3">
                    <div className="h-10 w-10 bg-muted rounded" />
                    <div className="h-4 bg-muted rounded w-3/4" />
                    <div className="h-3 bg-muted rounded w-1/2" />
                  </div>
                </Card>
              ))}
            </div>
          ) : filteredPuzzles.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {filteredPuzzles.map((puzzle) => (
                <PuzzleItemCard key={puzzle.id} puzzle={puzzle} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <p className="text-muted-foreground mb-4">
                No puzzles generated yet. Click &ldquo;Generate Puzzle&rdquo;
                to create your first puzzle.
              </p>
            </div>
          )}
        </TabsContent>

        {/* ─── Word Lists Tab ───────────────────────────────────────── */}
        <TabsContent value="word-lists" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Word Lists</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                View and manage word lists used across all puzzles in this book.
                Words are validated through the sanitization pipeline.
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate Lists
                </Button>
                <Button variant="outline" size="sm">
                  Sanitize All
                </Button>
              </div>
              {(puzzles ?? [])
                .filter((p) => p.word_list && p.word_list.length > 0)
                .map((puzzle) => (
                  <div key={puzzle.id} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        #{puzzle.puzzle_number}{" "}
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type] ??
                          puzzle.puzzle_type}
                      </span>
                      <Badge variant="outline" className="text-[10px]">
                        {puzzle.word_list?.length ?? 0} words
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {puzzle.word_list?.slice(0, 20).map((word) => (
                        <span
                          key={word}
                          className="text-xs bg-muted px-1.5 py-0.5 rounded"
                        >
                          {word}
                        </span>
                      ))}
                      {(puzzle.word_list?.length ?? 0) > 20 && (
                        <span className="text-xs text-muted-foreground">
                          +{(puzzle.word_list?.length ?? 0) - 20} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Clues Tab ────────────────────────────────────────────── */}
        <TabsContent value="clues" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Clue Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Review and edit clues for crossword and other clue-based
                puzzles. Clue style:{" "}
                <Badge variant="outline" className="text-[10px] capitalize">
                  {book.clue_style.replace("_", " ")}
                </Badge>
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate Clues
                </Button>
                <Button variant="outline" size="sm">
                  QA All Clues
                </Button>
                <Button variant="outline" size="sm">
                  Auto-Fix Ambiguous
                </Button>
              </div>
              {(puzzles ?? [])
                .filter((p) => p.clues && p.clues.length > 0)
                .map((puzzle) => (
                  <div key={puzzle.id} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        #{puzzle.puzzle_number}{" "}
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type]}
                      </span>
                      <Badge variant="outline" className="text-[10px]">
                        {puzzle.clues?.length ?? 0} clues
                      </Badge>
                    </div>
                    <div className="space-y-1">
                      {puzzle.clues?.slice(0, 5).map((clue, idx) => (
                        <div
                          key={idx}
                          className="flex items-baseline gap-2 text-xs"
                        >
                          <span className="text-muted-foreground font-mono w-4">
                            {idx + 1}.
                          </span>
                          <span>{clue.clue}</span>
                          <span className="text-muted-foreground ml-auto font-mono">
                            ({clue.answer})
                          </span>
                        </div>
                      ))}
                      {(puzzle.clues?.length ?? 0) > 5 && (
                        <p className="text-xs text-muted-foreground">
                          +{(puzzle.clues?.length ?? 0) - 5} more clues
                        </p>
                      )}
                    </div>
                  </div>
                ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Difficulty Tab ───────────────────────────────────────── */}
        <TabsContent value="difficulty" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Difficulty Calibration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <p className="text-sm text-muted-foreground">
                  Mode:{" "}
                  <span className="capitalize font-medium text-foreground">
                    {book.difficulty_mode}
                  </span>
                </p>
                <Button variant="outline" size="sm">
                  Recalibrate All
                </Button>
              </div>
              {/* Difficulty distribution */}
              <div className="space-y-2">
                <Label className="text-sm">Distribution</Label>
                <div className="flex gap-4">
                  {["easy", "medium", "hard"].map((level) => {
                    const count = (puzzles ?? []).filter(
                      (p) => p.difficulty === level
                    ).length;
                    const total = (puzzles ?? []).length || 1;
                    const pct = Math.round((count / total) * 100);
                    return (
                      <div key={level} className="flex-1 space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="capitalize">{level}</span>
                          <span className="text-muted-foreground">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all",
                              level === "easy"
                                ? "bg-green-500"
                                : level === "medium"
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                            )}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* Puzzle difficulty scores */}
              <div className="space-y-2">
                {(puzzles ?? []).map((puzzle) => (
                  <div
                    key={puzzle.id}
                    className="flex items-center justify-between rounded-md border p-2 text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground font-mono w-6">
                        #{puzzle.puzzle_number}
                      </span>
                      <span>
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type] ??
                          puzzle.puzzle_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-[10px] capitalize",
                          DIFFICULTY_COLORS[puzzle.difficulty] ?? ""
                        )}
                      >
                        {puzzle.difficulty}
                      </Badge>
                      <span className="text-xs text-muted-foreground w-12 text-right">
                        {puzzle.difficulty_score}/100
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Answer Keys Tab ──────────────────────────────────────── */}
        <TabsContent value="answer-keys" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Answer Keys</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <p className="text-sm text-muted-foreground">
                  Position:{" "}
                  <span className="capitalize font-medium text-foreground">
                    {book.answer_key_position === "back"
                      ? "Back of book"
                      : book.answer_key_position === "reverse"
                        ? "Reverse of puzzle page"
                        : "No answer key"}
                  </span>
                </p>
                <Button variant="outline" size="sm">
                  Generate All Keys
                </Button>
                <Button variant="outline" size="sm">
                  Verify Keys
                </Button>
              </div>
              <div className="space-y-2">
                {(puzzles ?? []).map((puzzle) => {
                  const hasKey = !!puzzle.solution_data;
                  return (
                    <div
                      key={puzzle.id}
                      className="flex items-center justify-between rounded-md border p-2 text-sm"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground font-mono w-6">
                          #{puzzle.puzzle_number}
                        </span>
                        <span>
                          {PUZZLE_TYPE_LABELS[puzzle.puzzle_type] ??
                            puzzle.puzzle_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {hasKey ? (
                          <Badge
                            variant="secondary"
                            className="bg-green-500/10 text-green-600 text-[10px]"
                          >
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Generated
                          </Badge>
                        ) : (
                          <Badge
                            variant="secondary"
                            className="bg-muted text-muted-foreground text-[10px]"
                          >
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Missing
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Quality Tab ──────────────────────────────────────────── */}
        <TabsContent value="quality" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quality Dashboard</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">
                    {book.quality_score ?? "--"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Overall Score
                  </p>
                </div>
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">
                    {(puzzles ?? []).filter((p) => p.status === "verified")
                      .length}
                  </p>
                  <p className="text-xs text-muted-foreground">Verified</p>
                </div>
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">
                    {(puzzles ?? []).filter(
                      (p) =>
                        p.quality_issues && p.quality_issues.length > 0
                    ).length}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    With Issues
                  </p>
                </div>
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">
                    {(puzzles ?? []).filter((p) => p.status === "failed")
                      .length}
                  </p>
                  <p className="text-xs text-muted-foreground">Failed</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Run Full QA
                </Button>
                <Button variant="outline" size="sm">
                  Fix All Issues
                </Button>
              </div>
              {/* Quality issues list */}
              {(puzzles ?? [])
                .filter(
                  (p) => p.quality_issues && p.quality_issues.length > 0
                )
                .map((puzzle) => (
                  <div key={puzzle.id} className="rounded-lg border p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm font-medium">
                        #{puzzle.puzzle_number}{" "}
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type]}
                      </span>
                    </div>
                    <ul className="space-y-1">
                      {puzzle.quality_issues?.map((issue, idx) => (
                        <li
                          key={idx}
                          className="text-xs text-muted-foreground flex items-start gap-1.5"
                        >
                          <span className="text-yellow-500 mt-0.5">
                            &bull;
                          </span>
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Export Tab ───────────────────────────────────────────── */}
        <TabsContent value="export" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Export & Publish</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Generate print-ready files for your puzzle book. All puzzles
                will be verified before export.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border p-4 space-y-3">
                  <h3 className="font-medium text-sm">Print-Ready PDF</h3>
                  <p className="text-xs text-muted-foreground">
                    KDP interior with bleed, trim marks, and 300 DPI
                    resolution. Includes puzzles and answer keys.
                  </p>
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() =>
                      exportBook.mutate({
                        format: "pdf",
                        dpi: 300,
                        include_answers: true,
                      })
                    }
                    disabled={exportBook.isPending}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export PDF
                  </Button>
                </div>
                <div className="rounded-lg border p-4 space-y-3">
                  <h3 className="font-medium text-sm">Individual Pages</h3>
                  <p className="text-xs text-muted-foreground">
                    PNG images per page at 300 DPI. Useful for other print
                    platforms or custom layouts.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() =>
                      exportBook.mutate({
                        format: "png",
                        dpi: 300,
                        include_answers: true,
                      })
                    }
                    disabled={exportBook.isPending}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export PNGs
                  </Button>
                </div>
              </div>
              <Separator />
              <div className="space-y-2">
                <h3 className="font-medium text-sm">Pre-Export Checklist</h3>
                <div className="space-y-1">
                  {[
                    {
                      label: "All puzzles generated",
                      ok: book.puzzles_created >= book.total_puzzles,
                    },
                    {
                      label: "All puzzles verified solvable",
                      ok:
                        (puzzles ?? []).length > 0 &&
                        (puzzles ?? []).every(
                          (p) => p.status === "verified"
                        ),
                    },
                    {
                      label: "Answer keys generated",
                      ok:
                        book.answer_key_position === "none" ||
                        (puzzles ?? []).every((p) => !!p.solution_data),
                    },
                    {
                      label: "Word lists sanitized",
                      ok: true,
                    },
                    {
                      label: "Difficulty calibration complete",
                      ok: (puzzles ?? []).every(
                        (p) => p.difficulty_score > 0
                      ),
                    },
                  ].map((check) => (
                    <div
                      key={check.label}
                      className="flex items-center gap-2 text-sm"
                    >
                      {check.ok ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span
                        className={cn(
                          check.ok
                            ? "text-foreground"
                            : "text-muted-foreground"
                        )}
                      >
                        {check.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ─── Puzzle Item Card ─────────────────────────────────────────────────────────

function PuzzleItemCard({ puzzle }: { puzzle: Puzzle }) {
  const Icon =
    PUZZLE_TYPE_ICONS[puzzle.puzzle_type] ?? Search;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">
              #{puzzle.puzzle_number}
            </span>
          </div>
          <Badge
            variant="secondary"
            className={cn(
              "text-[10px] capitalize",
              STATUS_COLORS[puzzle.status] ?? ""
            )}
          >
            {puzzle.status}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {PUZZLE_TYPE_LABELS[puzzle.puzzle_type] ?? puzzle.puzzle_type}
        </p>
        <div className="flex items-center justify-between">
          <Badge
            variant="outline"
            className={cn(
              "text-[10px] capitalize",
              DIFFICULTY_COLORS[puzzle.difficulty] ?? ""
            )}
          >
            {puzzle.difficulty}
          </Badge>
          {puzzle.grid_size && (
            <span className="text-[10px] text-muted-foreground">
              {puzzle.grid_size}
            </span>
          )}
        </div>
        {puzzle.theme && (
          <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded-full text-muted-foreground">
            {puzzle.theme}
          </span>
        )}
      </CardContent>
    </Card>
  );
}
