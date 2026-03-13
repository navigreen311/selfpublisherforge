"use client";

import { useParams, useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, ArrowLeft, ChevronLeft, BookOpen, Users, BarChart3, Eye, Download } from "lucide-react";
import Link from "next/link";
import { useChildrensBook } from "@/modules/specialty-books/childrens/hooks";
import { PageSpreadEditor } from "@/modules/specialty-books/childrens/components/PageSpreadEditor";
import { CharacterPanel } from "@/modules/specialty-books/childrens/components/CharacterPanel";
import { TextAnalysisPanel } from "@/modules/specialty-books/childrens/components/TextAnalysisPanel";
import { PreviewPanel } from "@/modules/specialty-books/childrens/components/PreviewPanel";
import { ExportPanel } from "@/modules/specialty-books/childrens/components/ExportPanel";

export default function ChildrensBookEditorPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.id as string;
  const { data: book, isLoading, error } = useChildrensBook(bookId);

  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex-1 flex">
          <Skeleton className="w-48 h-full shrink-0" />
          <Skeleton className="flex-1" />
          <Skeleton className="w-72 h-full shrink-0" />
        </div>
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push("/specialty-books/childrens")}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Book not found</h2>
          <p className="text-muted-foreground max-w-md">
            The book could not be loaded. It may have been deleted or you may not have permission.
          </p>
          <Button asChild variant="outline">
            <Link href="/specialty-books/childrens">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Books
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    generating: "default",
    illustrating: "default",
    reviewing: "outline",
    published: "secondary",
    archived: "secondary",
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => router.push("/specialty-books/childrens")}
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-base font-semibold truncate">{book.title}</h1>
          <Badge variant={statusVariant[book.status] || "secondary"} className="shrink-0">
            {book.status}
          </Badge>
        </div>
        <div className="flex-1" />
        <div className="text-sm text-muted-foreground">{book.page_count} pages</div>
      </div>

      {/* Tabs + Content */}
      <Tabs defaultValue="editor" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-4 mt-2 w-fit">
          <TabsTrigger value="editor" className="gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Editor
          </TabsTrigger>
          <TabsTrigger value="characters" className="gap-1.5">
            <Users className="h-3.5 w-3.5" />
            Characters
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-1.5">
            <BarChart3 className="h-3.5 w-3.5" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="preview" className="gap-1.5">
            <Eye className="h-3.5 w-3.5" />
            Preview
          </TabsTrigger>
          <TabsTrigger value="export" className="gap-1.5">
            <Download className="h-3.5 w-3.5" />
            Export
          </TabsTrigger>
        </TabsList>

        <TabsContent value="editor" className="flex-1 mt-0 overflow-hidden">
          <PageSpreadEditor bookId={bookId} ageRange={book.age_range} />
        </TabsContent>
        <TabsContent value="characters" className="flex-1 mt-0 overflow-hidden">
          <CharacterPanel bookId={bookId} />
        </TabsContent>
        <TabsContent value="analysis" className="flex-1 mt-0 overflow-hidden">
          <TextAnalysisPanel bookId={bookId} ageRange={book.age_range} />
        </TabsContent>
        <TabsContent value="preview" className="flex-1 mt-0 overflow-hidden">
          <PreviewPanel bookId={bookId} />
        </TabsContent>
        <TabsContent value="export" className="flex-1 mt-0 overflow-hidden">
          <ExportPanel bookId={bookId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
