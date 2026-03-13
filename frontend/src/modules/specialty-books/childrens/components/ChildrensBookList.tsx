"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  Search,
  Plus,
  BookOpen,
  ArrowUpDown,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileEdit,
  Image,
  Eye,
} from "lucide-react";
import { useChildrensBooks } from "../hooks";
import type { BookStatus, AgeRange } from "../types";

// ---------------------------------------------------------------------------
// Status config
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  BookStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ElementType }
> = {
  draft: { label: "Draft", variant: "secondary", icon: FileEdit },
  generating: { label: "Generating", variant: "default", icon: Loader2 },
  illustrating: { label: "Illustrating", variant: "default", icon: Image },
  reviewing: { label: "Reviewing", variant: "outline", icon: Eye },
  published: { label: "Published", variant: "secondary", icon: CheckCircle2 },
  archived: { label: "Archived", variant: "secondary", icon: AlertCircle },
};

const AGE_LABELS: Record<AgeRange, string> = {
  board: "Board (0-3)",
  picture: "Picture (3-5)",
  early_reader: "Early Reader (5-8)",
  chapter: "Chapter (8-12)",
};

type SortKey = "date-newest" | "date-oldest" | "title" | "qa-score";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ChildrensBookListProps {
  onCreateNew: () => void;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function CardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <Skeleton className="h-32 w-full rounded-md" />
        <Skeleton className="h-5 w-3/4 mt-2" />
        <Skeleton className="h-4 w-20 mt-1" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-4 w-24" />
      </CardContent>
    </Card>
  );
}

function EmptyState({ hasFilters, onCreateNew }: { hasFilters: boolean; onCreateNew: () => void }) {
  return (
    <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
      <Sparkles className="h-12 w-12 text-muted-foreground/40 mb-4" aria-hidden="true" />
      {hasFilters ? (
        <>
          <p className="font-medium text-muted-foreground">No books match your filters</p>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Try adjusting your search or status filter.
          </p>
        </>
      ) : (
        <>
          <p className="font-medium text-muted-foreground">No children&#39;s books yet</p>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Create your first illustrated book to get started.
          </p>
          <Button onClick={onCreateNew} className="mt-4" size="sm">
            <Plus className="h-4 w-4 mr-1" aria-hidden="true" />
            New Book
          </Button>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function ChildrensBookList({ onCreateNew }: ChildrensBookListProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<BookStatus | "all">("all");
  const [sortKey, setSortKey] = useState<SortKey>("date-newest");

  const { data, isLoading } = useChildrensBooks(1, 100);

  const books = useMemo(() => {
    if (!data?.items) return [];
    return data.items;
  }, [data]);

  const filtered = useMemo(() => {
    let result = books;

    if (statusFilter !== "all") {
      result = result.filter((b) => b.status === statusFilter);
    }

    const q = search.trim().toLowerCase();
    if (q) {
      result = result.filter((b) => b.title.toLowerCase().includes(q));
    }

    result = [...result].sort((a, b) => {
      switch (sortKey) {
        case "date-newest":
          return (b.updated_at || b.created_at).localeCompare(a.updated_at || a.created_at);
        case "date-oldest":
          return a.created_at.localeCompare(b.created_at);
        case "title":
          return a.title.localeCompare(b.title);
        case "qa-score":
          return (b.qa_score ?? 0) - (a.qa_score ?? 0);
        default:
          return 0;
      }
    });

    return result;
  }, [books, statusFilter, search, sortKey]);

  const hasFilters = statusFilter !== "all" || search.trim().length > 0;

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            placeholder="Search by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as BookStatus | "all")}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="generating">Generating</SelectItem>
            <SelectItem value="illustrating">Illustrating</SelectItem>
            <SelectItem value="reviewing">Reviewing</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sortKey} onValueChange={(v) => setSortKey(v as SortKey)}>
          <SelectTrigger className="w-full sm:w-44">
            <ArrowUpDown className="h-4 w-4 mr-1 shrink-0" aria-hidden="true" />
            <SelectValue placeholder="Sort" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date-newest">Newest first</SelectItem>
            <SelectItem value="date-oldest">Oldest first</SelectItem>
            <SelectItem value="title">By title</SelectItem>
            <SelectItem value="qa-score">By QA score</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Book grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <>
            {[...Array(6)].map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </>
        ) : filtered.length === 0 ? (
          <EmptyState hasFilters={hasFilters} onCreateNew={onCreateNew} />
        ) : (
          filtered.map((book) => {
            const config = STATUS_CONFIG[book.status] ?? STATUS_CONFIG.draft;
            const StatusIcon = config.icon;
            return (
              <Card
                key={book.id}
                className="overflow-hidden cursor-pointer transition-shadow hover:shadow-md hover:border-primary/30"
                onClick={() => router.push(`/specialty-books/childrens/${book.id}`)}
                role="link"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    router.push(`/specialty-books/childrens/${book.id}`);
                  }
                }}
              >
                <CardHeader className="pb-3">
                  {/* Cover thumbnail */}
                  <div className="aspect-[3/4] w-full rounded-md bg-muted overflow-hidden mb-2">
                    {book.cover_url ? (
                      <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <BookOpen className="h-8 w-8 text-muted-foreground/30" />
                      </div>
                    )}
                  </div>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-sm leading-tight line-clamp-2">{book.title}</h3>
                    <Badge variant={config.variant} className="shrink-0 text-xs">
                      <StatusIcon
                        className={cn("h-3 w-3 mr-1", book.status === "generating" && "animate-spin")}
                        aria-hidden="true"
                      />
                      {config.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{AGE_LABELS[book.age_range] ?? book.age_range}</span>
                    <span className="text-muted-foreground/40">|</span>
                    <span>{book.page_count} pages</span>
                  </div>
                  {book.qa_score != null && (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>QA Score</span>
                        <span>{book.qa_score}%</span>
                      </div>
                      <Progress value={book.qa_score} className="h-1.5" />
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
