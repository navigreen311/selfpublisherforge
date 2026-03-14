"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Clock,
  Globe,
  Puzzle,
  Plus,
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  ZoomIn,
  CalendarDays,
  Baby,
  ArrowUpDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  usePuzzleBooks,
  usePuzzleBookStats,
} from "@/modules/specialty/puzzles/hooks";
import type { PuzzleBook } from "@/modules/specialty/puzzles/hooks";
import { PuzzleCard } from "@/modules/specialty/puzzles/components/PuzzleCard";
import { TemplateCard } from "@/modules/specialty/puzzles/components/TemplateCard";

// ─── Quick-Start Templates ────────────────────────────────────────────────────

const TEMPLATES = [
  {
    id: "word-search-collection",
    name: "Word Search Collection",
    description:
      "Classic word search puzzles across multiple themes with progressive difficulty.",
    icon: Search,
    puzzleTypes: ["Word Search"],
  },
  {
    id: "crossword-compendium",
    name: "Crossword Compendium",
    description:
      "Themed crossword puzzles with quality-checked clues and varied grid sizes.",
    icon: Grid3X3,
    puzzleTypes: ["Crossword"],
  },
  {
    id: "maze-adventure",
    name: "Maze Adventure",
    description:
      "Engaging maze puzzles from simple paths to complex labyrinths.",
    icon: Route,
    puzzleTypes: ["Maze"],
  },
  {
    id: "sudoku-challenge",
    name: "Sudoku Challenge",
    description:
      "Number puzzles from beginner-friendly 4x4 to expert 9x9 grids.",
    icon: Hash,
    puzzleTypes: ["Sudoku"],
  },
  {
    id: "mixed-puzzle-fun",
    name: "Mixed Puzzle Fun",
    description:
      "A variety of puzzle types in one book for maximum entertainment.",
    icon: Shuffle,
    puzzleTypes: ["Word Search", "Crossword", "Maze", "Sudoku"],
  },
  {
    id: "large-print-word-search",
    name: "Large Print Word Search",
    description:
      "Oversized grids at 150% scale, perfect for seniors and low-vision readers.",
    icon: ZoomIn,
    puzzleTypes: ["Word Search"],
  },
  {
    id: "holiday-puzzles",
    name: "Holiday Puzzles",
    description:
      "Seasonal themed puzzles for Christmas, Halloween, Easter, and more.",
    icon: CalendarDays,
    puzzleTypes: ["Word Search", "Crossword", "Maze"],
  },
  {
    id: "kids-activity-book",
    name: "Kids Activity Book",
    description:
      "Age-appropriate puzzles with fun themes, simple grids, and kid-friendly clues.",
    icon: Baby,
    puzzleTypes: ["Word Search", "Maze", "Word Scramble"],
  },
];

// ─── Page Component ───────────────────────────────────────────────────────────

export default function PuzzleBooksPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [audienceFilter, setAudienceFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  const filters = {
    ...(search && { search }),
    ...(statusFilter !== "all" && { status: statusFilter }),
    ...(audienceFilter !== "all" && { audience: audienceFilter }),
  };

  const { data: stats } = usePuzzleBookStats();
  const { data: booksData, isLoading } = usePuzzleBooks(filters);

  const books = useMemo(() => {
    const items = booksData?.items ?? [];
    return sortBooks(items, sortBy);
  }, [booksData?.items, sortBy]);

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Puzzle className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Puzzle Books</h1>
            <p className="text-muted-foreground">
              Create word search, crossword, maze, sudoku, and more puzzle books
            </p>
          </div>
        </div>
        <Button asChild>
          <Link href="/specialty/puzzle-books/new">
            <Plus className="h-4 w-4 mr-2" /> Create New Book
          </Link>
        </Button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.total_books ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Total Books</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.in_progress ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">In Progress</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <Globe className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.published ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Published</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Puzzle className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.puzzles_created ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Puzzles Created</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick-Start Templates */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Quick-Start Templates</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {TEMPLATES.map((template) => (
            <TemplateCard
              key={template.id}
              icon={template.icon}
              name={template.name}
              description={template.description}
              puzzleTypes={template.puzzleTypes}
              onUseTemplate={() =>
                router.push(
                  `/specialty/puzzle-books/new?template=${template.id}`
                )
              }
            />
          ))}
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search puzzle books..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        <Select value={audienceFilter} onValueChange={setAudienceFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Audience" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Audiences</SelectItem>
            <SelectItem value="kids">Kids</SelectItem>
            <SelectItem value="teens">Teens</SelectItem>
            <SelectItem value="adults">Adults</SelectItem>
            <SelectItem value="large_print">Large Print</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={sortBy}
          onValueChange={(v) => setSortBy(v as SortOption)}
        >
          <SelectTrigger className="w-[160px]">
            <ArrowUpDown className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Sort" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest First</SelectItem>
            <SelectItem value="oldest">Oldest First</SelectItem>
            <SelectItem value="title_asc">Title A-Z</SelectItem>
            <SelectItem value="title_desc">Title Z-A</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Book Grid or Empty State */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="overflow-hidden animate-pulse">
              <div className="aspect-[4/3] bg-muted" />
              <div className="p-3 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : books.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {books.map((book) => (
            <PuzzleCard key={book.id} book={book} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <Puzzle className="h-12 w-12 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">
            No puzzle books yet
          </h3>
          <p className="text-muted-foreground max-w-md mb-6">
            Create your first puzzle book. Choose from word search, crossword,
            maze, sudoku, and more puzzle types with auto-generated answer keys.
          </p>
          <Button asChild>
            <Link href="/specialty/puzzle-books/new">
              <Plus className="h-4 w-4 mr-2" /> Create Your First Book
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}
