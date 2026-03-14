"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { BookOpen, Image as ImageIcon } from "lucide-react";
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

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  draft: "secondary",
  "in-progress": "default",
  published: "outline",
};

// ---------------------------------------------------------------------------
// BookCard
// ---------------------------------------------------------------------------

interface BookCardProps {
  book: ChildrensBook;
}

export function BookCard({ book }: BookCardProps) {
  return (
    <Link href={`/specialty/childrens-books/${book.id}`}>
      <Card className="group overflow-hidden hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer">
        {/* Cover thumbnail placeholder */}
        <div className="aspect-[3/4] bg-muted flex items-center justify-center relative">
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
          <Badge
            variant={STATUS_VARIANT[book.status] ?? "secondary"}
            className="absolute top-2 right-2 capitalize text-[10px]"
          >
            {book.status}
          </Badge>
        </div>

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
        </div>
      </Card>
    </Link>
  );
}
