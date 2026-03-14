"use client";

import Link from "next/link";
import {
  Palette,
  FileText,
  Pencil,
  MoreHorizontal,
  Trash2,
  Copy,
  Download,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ColoringBook } from "../hooks";

// ---------------------------------------------------------------------------
// Status styling with required hex colors
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string }
> = {
  draft: { label: "Draft", bg: "#F3F4F6", text: "#6B7280" },
  in_progress: { label: "In Progress", bg: "#FEF3C7", text: "#D97706" },
  published: { label: "Published", bg: "#D1FAE5", text: "#059669" },
};

// ---------------------------------------------------------------------------
// Audience labels
// ---------------------------------------------------------------------------

const AUDIENCE_LABEL: Record<string, string> = {
  kids: "Kids 3-8",
  teens: "Teens 9-14",
  adults: "Adults 15+",
};

// ---------------------------------------------------------------------------
// Line style display labels
// ---------------------------------------------------------------------------

const LINE_STYLE_LABEL: Record<string, string> = {
  clean_outlines: "Clean Outlines",
  sketchy_hand_drawn: "Sketchy / Hand-drawn",
  whimsical_decorative: "Whimsical / Decorative",
  realistic_detailed: "Realistic / Detailed",
  zentangle: "Zentangle",
  bold_simple: "Bold & Simple",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface BookCardProps {
  book: ColoringBook;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onExport?: (id: string) => void;
}

export function BookCard({ book, onDelete, onDuplicate, onExport }: BookCardProps) {
  const statusCfg = STATUS_CONFIG[book.status] ?? STATUS_CONFIG.draft;

  return (
    <Card className="hover:shadow-md transition-shadow h-full flex flex-col">
      {/* ── Cover thumbnail / placeholder ────────────────────────────── */}
      {book.cover_url ? (
        <div className="aspect-[3/4] rounded-t-lg overflow-hidden bg-muted">
          <img
            src={book.cover_url}
            alt={book.title}
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <div className="aspect-[3/4] rounded-t-lg bg-muted flex items-center justify-center">
          <Palette className="h-10 w-10 text-muted-foreground/40" />
        </div>
      )}

      <CardHeader className="pb-2 pt-3">
        <div className="flex items-start justify-between gap-2">
          {/* ── Title ─────────────────────────────────────────────────── */}
          <CardTitle className="text-base line-clamp-2">{book.title}</CardTitle>

          {/* ── Status badge ──────────────────────────────────────────── */}
          <span
            className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
            style={{ backgroundColor: statusCfg.bg, color: statusCfg.text }}
          >
            {statusCfg.label}
          </span>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-3">
        {/* ── Meta info ───────────────────────────────────────────────── */}
        <div className="space-y-1 text-sm text-muted-foreground">
          {/* Audience badge */}
          <div>
            <Badge variant="secondary" className="text-xs">
              {AUDIENCE_LABEL[book.audience] ?? book.audience}
            </Badge>
          </div>

          {/* Page count */}
          <div className="flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            <span>
              {book.pages_created} / {book.page_count} pages
            </span>
          </div>

          {/* Line art style indicator */}
          <div className="flex items-center gap-1.5">
            <Pencil className="h-3.5 w-3.5" />
            <span className="truncate">
              {LINE_STYLE_LABEL[book.line_style] ?? book.line_style}
            </span>
          </div>
        </div>

        {/* ── Actions row ─────────────────────────────────────────────── */}
        <div className="mt-auto flex items-center gap-2 pt-2 border-t">
          {/* Edit button */}
          <Button variant="outline" size="sm" className="flex-1" asChild>
            <Link href={`/specialty/coloring-books/${book.id}`}>Edit</Link>
          </Button>

          {/* More menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">More actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onDuplicate?.(book.id)}
              >
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onExport?.(book.id)}
              >
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
      </CardContent>
    </Card>
  );
}
