"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import {
  BookOpen,
  Copy,
  Download,
  Image as ImageIcon,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import type { ChildrensBook } from "../hooks";

// ---------------------------------------------------------------------------
// QA Score Ring
// ---------------------------------------------------------------------------

function QAScoreRing({ score }: { score?: number }) {
  const value = score ?? 0;
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const color =
    value >= 80
      ? "text-green-500"
      : value >= 50
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="relative h-10 w-10 shrink-0">
      <svg className="h-10 w-10 -rotate-90" viewBox="0 0 36 36">
        <circle
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          className="stroke-muted"
          strokeWidth="3"
        />
        <circle
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          className={cn("stroke-current", color)}
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold">
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Age range helpers
// ---------------------------------------------------------------------------

const AGE_LABELS: Record<string, string> = {
  board: "0-3",
  picture: "3-5",
  early_reader: "5-8",
  chapter: "8-12",
};

// ---------------------------------------------------------------------------
// Status badge styles (inline colors per spec)
// ---------------------------------------------------------------------------

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  draft: { bg: "#F3F4F6", text: "#6B7280", label: "Draft" },
  "in-progress": { bg: "#FEF3C7", text: "#D97706", label: "In Progress" },
  in_progress: { bg: "#FEF3C7", text: "#D97706", label: "In Progress" },
  published: { bg: "#D1FAE5", text: "#059669", label: "Published" },
};

// ---------------------------------------------------------------------------
// BookCard
// ---------------------------------------------------------------------------

interface BookCardProps {
  book: ChildrensBook;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onExport?: (id: string) => void;
}

export function BookCard({ book, onDelete, onDuplicate, onExport }: BookCardProps) {
  const statusStyle = STATUS_STYLES[book.status] ?? STATUS_STYLES.draft;

  return (
    <Card className="group overflow-hidden hover:ring-2 hover:ring-primary/50 transition-all">
      {/* Cover thumbnail placeholder */}
      <Link href={`/specialty/childrens-books/${book.id}`}>
        <div className="aspect-[3/4] bg-muted flex items-center justify-center relative cursor-pointer">
          {book.cover_image_url ? (
            <img
              src={book.cover_image_url}
              alt={book.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <ImageIcon className="h-10 w-10" />
              <span className="text-xs">No Cover</span>
            </div>
          )}

          {/* Status badge overlay */}
          <span
            className="absolute top-2 right-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold"
            style={{ backgroundColor: statusStyle.bg, color: statusStyle.text }}
          >
            {statusStyle.label}
          </span>
        </div>
      </Link>

      {/* Card body */}
      <div className="p-3 space-y-2">
        <h3 className="font-semibold text-sm truncate group-hover:text-primary transition-colors">
          {book.title}
        </h3>

        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
              Ages {AGE_LABELS[book.age_range] ?? book.age_range}
            </Badge>
            <span className="flex items-center gap-0.5">
              <BookOpen className="h-3 w-3" />
              {book.page_count}p
            </span>
          </div>

          <QAScoreRing score={book.qa_score} />
        </div>

        {/* Action row: Edit button + More menu */}
        <div className="flex items-center justify-between gap-2 pt-1">
          <Button variant="outline" size="sm" className="h-7 text-xs" asChild>
            <Link href={`/specialty/childrens-books/${book.id}`}>
              <Pencil className="mr-1 h-3 w-3" />
              Edit
            </Link>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">More actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onDuplicate?.(book.id)}>
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExport?.(book.id)}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => onDelete?.(book.id)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </Card>
  );
}
