"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Puzzle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PuzzleEditor } from "@/modules/specialty-books/puzzles/components/PuzzleEditor";
import { usePuzzleBook } from "@/modules/specialty-books/puzzles/hooks";

export default function PuzzleBookEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data: book } = usePuzzleBook(id);

  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/specialty-books/puzzles")}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <Puzzle className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-xl font-bold">
              {book?.title ?? "Loading..."}
            </h1>
            {book?.subtitle && (
              <p className="text-sm text-muted-foreground">
                {book.subtitle}
              </p>
            )}
          </div>
          {book?.status && (
            <Badge variant="outline" className="text-xs capitalize">
              {book.status.replace(/_/g, " ")}
            </Badge>
          )}
        </div>
      </div>

      {/* Editor */}
      <PuzzleEditor bookId={id} />
    </div>
  );
}
