"use client";

import Link from "next/link";
import { Book, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ColoringBook } from "../hooks";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  draft: "outline",
  in_progress: "secondary",
  published: "default",
};

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  in_progress: "In Progress",
  published: "Published",
};

export interface BookCardProps {
  book: ColoringBook;
}

export function BookCard({ book }: BookCardProps) {
  return (
    <Link href={`/specialty/coloring-books/${book.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base line-clamp-2">
              {book.title}
            </CardTitle>
            <Badge variant={STATUS_VARIANT[book.status] ?? "outline"}>
              {STATUS_LABEL[book.status] ?? book.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {book.cover_url ? (
            <div className="aspect-[3/4] rounded-md overflow-hidden bg-muted mb-3">
              <img
                src={book.cover_url}
                alt={book.title}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="aspect-[3/4] rounded-md bg-muted flex items-center justify-center mb-3">
              <Book className="h-10 w-10 text-muted-foreground/40" />
            </div>
          )}

          <div className="space-y-1 text-sm text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              <span>
                {book.pages_created} / {book.page_count} pages
              </span>
            </div>
            {book.audience && (
              <p className="capitalize">{book.audience} audience</p>
            )}
            {book.quality_score != null && (
              <p>Quality: {book.quality_score}/100</p>
            )}
            {book.series_name && (
              <p className="truncate">
                {book.series_name}
                {book.volume_number != null && ` Vol. ${book.volume_number}`}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
