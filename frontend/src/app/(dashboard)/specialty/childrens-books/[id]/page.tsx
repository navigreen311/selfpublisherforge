"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Users,
  FileText,
  Shield,
  Eye,
  Download,
  Image as ImageIcon,
  Plus,
  Wand2,
  Layers,
  MessageSquareWarning,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useChildrensBook,
  useBookCharacters,
} from "@/modules/specialty/childrens/hooks";
import { SpreadEditor } from "@/modules/specialty/childrens/components/SpreadEditor";
import { ReviewFeedbackPanel } from "@/modules/specialty/shared/components/ReviewFeedbackPanel";
import { Breadcrumb } from "@/components/ui/breadcrumb";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  draft: "secondary",
  "in-progress": "default",
  published: "outline",
};

const AGE_LABELS: Record<string, string> = {
  board: "Board (0-3)",
  picture: "Picture (3-5)",
  early_reader: "Early Reader (5-8)",
  chapter: "Chapter (8-12)",
};

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function ChildrensBookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.id as string;

  const { data: book, isLoading, error } = useChildrensBook(bookId);
  const { data: characters } = useBookCharacters(bookId);

  const [activeTab, setActiveTab] = useState("editor");

  // Loading state
  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex-1 flex">
          <Skeleton className="w-48 h-full shrink-0" />
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-[400px] w-full" />
          </div>
          <Skeleton className="w-72 h-full shrink-0" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !book) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push("/specialty/childrens-books")}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Book not found</h2>
          <p className="text-muted-foreground max-w-md">
            This book could not be loaded. It may have been deleted or you may
            not have permission to view it.
          </p>
          <Button asChild variant="outline">
            <Link href="/specialty/childrens-books">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Return to Books
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  // Map API age_range (underscore) to SpreadEditor AgeRange (hyphenated)
  const ageRangeMap: Record<string, "board" | "picture" | "early-reader" | "chapter"> = {
    board: "board",
    picture: "picture",
    early_reader: "early-reader",
    chapter: "chapter",
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="px-4 pt-3">
        <Breadcrumb items={[
          { label: "Specialty", href: "/specialty" },
          { label: "Children's Books", href: "/specialty/childrens-books" },
          { label: book.title },
        ]} />
      </div>
      {/* Header */}
      <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => router.push("/specialty/childrens-books")}
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-base font-semibold truncate">{book.title}</h1>
          <Badge
            variant={STATUS_VARIANT[book.status] ?? "secondary"}
            className="shrink-0 capitalize"
          >
            {book.status}
          </Badge>
          <Badge variant="outline" className="shrink-0">
            {AGE_LABELS[book.age_range] ?? book.age_range}
          </Badge>
        </div>
        <div className="flex-1" />
        <span className="text-sm text-muted-foreground mr-2">
          {book.page_count} pages
        </span>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => setActiveTab("preview")}
        >
          <Eye className="h-3.5 w-3.5" />
          Preview
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => setActiveTab("export")}
        >
          <Download className="h-3.5 w-3.5" />
          Export
        </Button>
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
        <div className="border-b px-4">
          <TabsList className="h-10">
            <TabsTrigger value="editor" className="gap-1.5">
              <Layers className="h-3.5 w-3.5" />
              Editor
            </TabsTrigger>
            <TabsTrigger value="characters" className="gap-1.5">
              <Users className="h-3.5 w-3.5" />
              Characters
            </TabsTrigger>
            <TabsTrigger value="text-analysis" className="gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              Text Analysis
            </TabsTrigger>
            <TabsTrigger value="safety" className="gap-1.5">
              <Shield className="h-3.5 w-3.5" />
              Safety
            </TabsTrigger>
            <TabsTrigger value="preview" className="gap-1.5">
              <Eye className="h-3.5 w-3.5" />
              Preview
            </TabsTrigger>
            <TabsTrigger value="export" className="gap-1.5">
              <Download className="h-3.5 w-3.5" />
              Export
            </TabsTrigger>
            <TabsTrigger value="reviews" className="gap-1.5">
              <MessageSquareWarning className="h-3.5 w-3.5" />
              Reviews
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Editor Tab - Three panel layout via SpreadEditor */}
        <TabsContent value="editor" className="flex-1 overflow-hidden m-0">
          <SpreadEditor
            bookId={bookId}
            ageRange={ageRangeMap[book.age_range] ?? "picture"}
            initialPageCount={book.page_count}
          />
        </TabsContent>

        {/* Characters Tab */}
        <TabsContent value="characters" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Characters</h2>
                <p className="text-sm text-muted-foreground">
                  Manage character consistency across all pages.
                </p>
              </div>
              <Button size="sm" className="gap-1.5">
                <Plus className="h-4 w-4" /> Add Character
              </Button>
            </div>

            {characters && characters.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {characters.map((char) => (
                  <Card key={char.id}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">{char.name}</CardTitle>
                      {char.species && (
                        <Badge variant="outline" className="w-fit">
                          {char.species}
                        </Badge>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        {char.description}
                      </p>
                      {/* Reference images grid */}
                      <div className="grid grid-cols-4 gap-1.5">
                        {["Front", "Side", "Happy", "Scared"].map(
                          (view, idx) => (
                            <div
                              key={view}
                              className="aspect-square bg-muted rounded flex items-center justify-center"
                            >
                              {char.reference_images?.[idx] ? (
                                <img
                                  src={char.reference_images[idx]}
                                  alt={`${char.name} ${view}`}
                                  className="h-full w-full object-cover rounded"
                                />
                              ) : (
                                <span className="text-[9px] text-muted-foreground">
                                  {view}
                                </span>
                              )}
                            </div>
                          ),
                        )}
                      </div>
                      <div className="flex gap-1.5">
                        <Button size="sm" variant="outline" className="text-xs h-7">
                          Edit
                        </Button>
                        <Button size="sm" variant="outline" className="text-xs h-7 gap-1">
                          <Wand2 className="h-3 w-3" /> Generate Refs
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-8 text-center">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <h3 className="font-medium">No characters yet</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Add characters to ensure visual consistency across your book.
                </p>
                <Button size="sm" className="mt-4 gap-1.5">
                  <Plus className="h-4 w-4" /> Add First Character
                </Button>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Text Analysis Tab */}
        <TabsContent value="text-analysis" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-lg font-semibold">Text Analysis</h2>
              <p className="text-sm text-muted-foreground">
                Reading level, rhythm scoring, and pacing analysis.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-3xl font-bold text-primary">--</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Read-Aloud Rhythm Score
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-3xl font-bold">--</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Total Word Count
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-3xl font-bold">--</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Avg Words/Page
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-3xl font-bold text-green-500">--</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Look Inside Hook Score
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Page-Turn Surprise Map</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-32 bg-muted rounded flex items-center justify-center text-sm text-muted-foreground">
                  Run text analysis to see pacing visualization
                </div>
                <Button size="sm" className="mt-3 gap-1.5">
                  <Wand2 className="h-3.5 w-3.5" /> Analyze Text
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Safety Tab */}
        <TabsContent value="safety" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-lg font-semibold">Safety & Provenance</h2>
              <p className="text-sm text-muted-foreground">
                Trademark checks, content sensitivity, and provenance tracking.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Card>
                <CardContent className="p-4 text-center">
                  <Shield className="h-8 w-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">Trademark Check</p>
                  <p className="text-xs text-muted-foreground">Not yet run</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Shield className="h-8 w-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">Content Sensitivity</p>
                  <p className="text-xs text-muted-foreground">Not yet run</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Shield className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">Provenance Ledger</p>
                  <p className="text-xs text-muted-foreground">
                    {book.page_count ?? 0} assets tracked
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="flex gap-2">
              <Button size="sm" className="gap-1.5">
                <Shield className="h-3.5 w-3.5" /> Run Safety Check
              </Button>
              <Button size="sm" variant="outline" className="gap-1.5">
                <Download className="h-3.5 w-3.5" /> Export Compliance Report
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-lg font-semibold">Preview</h2>
              <p className="text-sm text-muted-foreground">
                Spread view, single page, and Look Inside simulator.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Card className="cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
                <CardContent className="p-6 text-center">
                  <BookOpen className="h-10 w-10 text-primary mx-auto mb-2" />
                  <p className="font-medium text-sm">Spread View</p>
                  <p className="text-xs text-muted-foreground">
                    Two-page as printed
                  </p>
                </CardContent>
              </Card>
              <Card className="cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
                <CardContent className="p-6 text-center">
                  <FileText className="h-10 w-10 text-primary mx-auto mb-2" />
                  <p className="font-medium text-sm">Single Page</p>
                  <p className="text-xs text-muted-foreground">
                    Individual page view
                  </p>
                </CardContent>
              </Card>
              <Card className="cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
                <CardContent className="p-6 text-center">
                  <Eye className="h-10 w-10 text-primary mx-auto mb-2" />
                  <p className="font-medium text-sm">Look Inside</p>
                  <p className="text-xs text-muted-foreground">
                    Amazon preview simulator
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardContent className="p-8">
                <div className="h-64 bg-muted rounded flex items-center justify-center text-muted-foreground">
                  Select a preview mode above to view your book
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-lg font-semibold">Export & Publish</h2>
              <p className="text-sm text-muted-foreground">
                Generate print-ready files and run preflight checks.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {[
                {
                  title: "Print-Ready PDF",
                  desc: "KDP interior with bleed, trim, 300 DPI",
                  icon: Download,
                },
                {
                  title: "Fixed-Layout KPF",
                  desc: "Kindle Package Format for tablets",
                  icon: Download,
                },
                {
                  title: "Fixed-Layout EPUB 3",
                  desc: "Standard fixed-layout ebook",
                  icon: Download,
                },
                {
                  title: "Individual Pages",
                  desc: "PNG/JPG per page at 300 DPI",
                  icon: ImageIcon,
                },
              ].map((format) => (
                <Card key={format.title}>
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <format.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{format.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {format.desc}
                      </p>
                    </div>
                    <Button size="sm" variant="outline">
                      Export
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Separator />

            <div>
              <h3 className="font-semibold text-sm mb-3">Preflight Check</h3>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground mb-3">
                    Run a full preflight to verify your book is ready for
                    publishing.
                  </div>
                  <Button className="gap-1.5">
                    <Shield className="h-4 w-4" /> Run Preflight
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Reviews Tab */}
        <TabsContent value="reviews" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto">
            <ReviewFeedbackPanel bookType="childrens-books" bookId={bookId} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
