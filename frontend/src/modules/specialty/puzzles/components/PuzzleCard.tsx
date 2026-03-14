"use client";

import Link from "next/link";
import Image from "next/image";
import {
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  Lock,
  Binary,
  Link2,
  HelpCircle,
  MoreHorizontal,
  Pencil,
  Copy,
  Trash2,
  Download,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { PuzzleBook, PuzzleType, Audience } from "../hooks";

// ─── Puzzle type icon map ─────────────────────────────────────────────────────

const PUZZLE_TYPE_ICONS: Record<PuzzleType, LucideIcon> = {
  word_search: Search,
  crossword: Grid3X3,
  maze: Route,
  sudoku: Hash,
  word_scramble: Shuffle,
  cryptogram: Lock,
  number_search: Binary,
  word_connect: Link2,
  trivia: HelpCircle,
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
  trivia: "Trivia",
};

const AUDIENCE_LABELS: Record<Audience, string> = {
  kids: "Kids 5-10",
  teens: "Teens",
  adults: "Adults",
  large_print: "Large Print",
};

const STATUS_STYLES: Record<
  string,
  { bg: string; text: string }
> = {
  draft: { bg: "bg-[#F3F4F6]", text: "text-[#6B7280]" },
  in_progress: { bg: "bg-[#FEF3C7]", text: "text-[#D97706]" },
  published: { bg: "bg-[#D1FAE5]", text: "text-[#059669]" },
};

// ─── Component ────────────────────────────────────────────────────────────────

export interface PuzzleCardProps {
  book: PuzzleBook;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onExport?: (id: string) => void;
}

export function PuzzleCard({
  book,
  onDelete,
  onDuplicate,
  onExport,
}: PuzzleCardProps) {
  const primaryType = book.puzzle_config[0]?.type ?? "word_search";
  const Icon = PUZZLE_TYPE_ICONS[primaryType] ?? Search;

  const puzzleTypeLabels = book.puzzle_config
    .map((c) => PUZZLE_TYPE_LABELS[c.type])
    .filter(Boolean);

  const statusLabel = book.status.replace("_", " ");
  const statusStyle = STATUS_STYLES[book.status] ?? STATUS_STYLES.draft;

  // Build difficulty range from puzzle_config entries
  const difficulties = book.puzzle_config
    .map((c) => c.difficulty)
    .filter(Boolean);
  const uniqueDifficulties = Array.from(new Set(difficulties));
  const difficultyRange =
    uniqueDifficulties.length > 1
      ? `${uniqueDifficulties[0]} - ${uniqueDifficulties[uniqueDifficulties.length - 1]}`
      : uniqueDifficulties[0] ?? book.difficulty_mode;

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow group">
      {/* Cover / Icon header */}
      <div className="aspect-[4/3] bg-muted/50 flex items-center justify-center relative">
        {book.cover_url ? (
          <Image
            src={book.cover_url}
            alt={book.title}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, 20vw"
          />
        ) : (
          <Icon className="h-12 w-12 text-muted-foreground/40 group-hover:text-primary/60 transition-colors" />
        )}

        {/* Status badge */}
        <Badge
          className={cn(
            "absolute top-2 right-2 text-[10px] capitalize border-0",
            statusStyle.bg,
            statusStyle.text
          )}
          variant="secondary"
        >
          {statusLabel}
        </Badge>

        {/* Audience badge */}
        <Badge
          className="absolute top-2 left-2 text-[10px] bg-white/90 text-gray-700 border-0"
          variant="secondary"
        >
          {AUDIENCE_LABELS[book.audience] ?? book.audience}
        </Badge>
      </div>

      <CardContent className="p-3 space-y-1.5">
        {/* Title */}
        <p className="font-medium text-sm truncate">{book.title}</p>

        {/* Puzzle type tag badges */}
        <div className="flex flex-wrap gap-1">
          {puzzleTypeLabels.slice(0, 3).map((label) => (
            <span
              key={label}
              className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full"
            >
              {label}
            </span>
          ))}
          {puzzleTypeLabels.length > 3 && (
            <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded-full text-muted-foreground">
              +{puzzleTypeLabels.length - 3}
            </span>
          )}
        </div>

        {/* Puzzle count & difficulty range */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {book.puzzles_created}/{book.total_puzzles} puzzles
          </span>
          <Badge variant="outline" className="text-[10px] capitalize">
            {difficultyRange}
          </Badge>
        </div>

        {/* Edit button & more menu */}
        <div className="flex items-center gap-1 pt-1">
          <Button variant="outline" size="sm" className="flex-1 h-7 text-xs" asChild>
            <Link href={`/specialty/puzzle-books/${book.id}`}>
              <Pencil className="h-3 w-3 mr-1" />
              Edit
            </Link>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 w-7 p-0">
                <MoreHorizontal className="h-3.5 w-3.5" />
                <span className="sr-only">More actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onDuplicate?.(book.id)}>
                <Copy className="h-4 w-4 mr-2" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExport?.(book.id)}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => onDelete?.(book.id)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardContent>
    </Card>
  );
}
