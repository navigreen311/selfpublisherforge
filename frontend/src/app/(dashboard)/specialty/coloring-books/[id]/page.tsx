"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  ShieldCheck,
  Layers,
  Library,
  Download,
  Loader2,
  Play,
  RefreshCw,
  Wrench,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  MessageSquareWarning,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ColoringEditor } from "@/modules/specialty/coloring/components/ColoringEditor";
import {
  useColoringBook,
  useColoringPages,
  useBatchGenerate,
  useQualityCheck,
  useExport,
} from "@/modules/specialty/coloring/hooks";
import type { ExportOptions } from "@/modules/specialty/coloring/hooks";
import { ReviewFeedbackPanel } from "@/modules/specialty/shared/components/ReviewFeedbackPanel";

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ColoringBookEditorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const bookId = params.id;

  const { data: book, isLoading: bookLoading } = useColoringBook(bookId);
  const { data: pages, isLoading: pagesLoading } = useColoringPages(bookId);
  const batchGenerate = useBatchGenerate(bookId);
  const qualityCheck = useQualityCheck(bookId);
  const exportBook = useExport(bookId);

  const [activeTab, setActiveTab] = useState("pages");
  const [exportFormat, setExportFormat] =
    useState<ExportOptions["format"]>("pdf");

  const handlePageAction = (pageId: string, action: string) => {
    // Page actions will dispatch to the appropriate API endpoints
    // This is a placeholder for the action dispatch logic
    console.log(`Action: ${action} on page: ${pageId}`);
  };

  const handleExport = () => {
    exportBook.mutate({ format: exportFormat });
  };

  if (bookLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!book) {
    return (
      <div className="space-y-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/specialty/coloring-books")}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
        <div className="border rounded-lg p-8 text-center text-muted-foreground">
          Book not found.
        </div>
      </div>
    );
  }

  const pagesArray = pages ?? [];
  const completedPages = pagesArray.filter(
    (p) => p.status === "generated" || p.status === "cleaned" || p.status === "approved"
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/specialty/coloring-books")}
            className="mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <h1 className="text-2xl font-bold">{book.title}</h1>
          {book.subtitle && (
            <p className="text-muted-foreground mt-0.5">{book.subtitle}</p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary" className="capitalize">
              {book.audience}
            </Badge>
            <Badge variant="outline">{book.line_style.replace(/_/g, " ")}</Badge>
            <Badge variant="outline">{book.trim_size}</Badge>
            {book.series_name && (
              <Badge variant="outline">
                {book.series_name} Vol. {book.volume_number}
              </Badge>
            )}
          </div>
        </div>
        <div className="text-right text-sm text-muted-foreground">
          <p>
            {completedPages} / {book.page_count} pages
          </p>
          <Progress
            value={(completedPages / book.page_count) * 100}
            className="h-2 w-40 mt-1"
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="pages" className="gap-1.5">
            <FileText className="h-4 w-4" />
            Pages
          </TabsTrigger>
          <TabsTrigger value="quality" className="gap-1.5">
            <ShieldCheck className="h-4 w-4" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="batch" className="gap-1.5">
            <Layers className="h-4 w-4" />
            Batch
          </TabsTrigger>
          <TabsTrigger value="series" className="gap-1.5">
            <Library className="h-4 w-4" />
            Series
          </TabsTrigger>
          <TabsTrigger value="export" className="gap-1.5">
            <Download className="h-4 w-4" />
            Export
          </TabsTrigger>
          <TabsTrigger value="reviews" className="gap-1.5">
            <MessageSquareWarning className="h-4 w-4" />
            Reviews
          </TabsTrigger>
        </TabsList>

        {/* Pages Tab */}
        <TabsContent value="pages" className="mt-6">
          {pagesLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="aspect-[3/4] rounded-lg" />
              ))}
            </div>
          ) : pagesArray.length === 0 ? (
            <div className="border rounded-lg p-12 text-center">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
              <h3 className="text-lg font-medium mb-2">No pages yet</h3>
              <p className="text-muted-foreground mb-4">
                Generate pages using the Batch tab or add pages individually.
              </p>
              <Button onClick={() => setActiveTab("batch")}>
                <Play className="h-4 w-4 mr-2" />
                Go to Batch Generation
              </Button>
            </div>
          ) : (
            <ColoringEditor
              pages={pagesArray}
              onPageAction={handlePageAction}
            />
          )}
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="mt-6">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Quality Dashboard</h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => qualityCheck.mutate()}
                  disabled={qualityCheck.isPending}
                >
                  {qualityCheck.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Re-run Full QA
                </Button>
                <Button
                  variant="outline"
                  disabled={qualityCheck.isPending}
                >
                  <Wrench className="h-4 w-4 mr-2" />
                  Fix All Issues
                </Button>
              </div>
            </div>

            {qualityCheck.data ? (
              <>
                {/* Overall Score */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Overall Quality Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <span className="text-4xl font-bold">
                        {qualityCheck.data.overall_score}
                      </span>
                      <span className="text-muted-foreground">/ 100</span>
                      <Progress
                        value={qualityCheck.data.overall_score}
                        className="flex-1 h-3"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Print Quality Breakdown */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                  {[
                    { label: "Line Quality", value: qualityCheck.data.print_quality.line_quality },
                    { label: "Closed Shapes", value: qualityCheck.data.print_quality.closed_shapes },
                    { label: "Stroke Uniformity", value: qualityCheck.data.print_quality.stroke_uniformity },
                    { label: "Ink Density", value: qualityCheck.data.print_quality.ink_density },
                    { label: "Small Areas", value: qualityCheck.data.print_quality.small_areas },
                  ].map((metric) => (
                    <Card key={metric.label}>
                      <CardContent className="p-4 text-center">
                        <p className="text-sm text-muted-foreground">
                          {metric.label}
                        </p>
                        <p className="text-2xl font-bold mt-1">
                          {metric.value}%
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Theme Cohesion & Complexity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Theme Cohesion</CardTitle>
                      <CardDescription>
                        How well pages match the overall theme
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-3">
                        <span className="text-3xl font-bold">
                          {qualityCheck.data.theme_cohesion_score}
                        </span>
                        <span className="text-muted-foreground">/ 100</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">
                        Complexity Distribution
                      </CardTitle>
                      <CardDescription>
                        Page difficulty spread across the book
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-end gap-1 h-24">
                        {qualityCheck.data.complexity_distribution.map((d) => (
                          <div
                            key={d.level}
                            className="flex-1 bg-primary/20 rounded-t relative group"
                            style={{
                              height: `${Math.max(
                                8,
                                (d.count /
                                  Math.max(
                                    ...qualityCheck.data!.complexity_distribution.map(
                                      (x) => x.count
                                    ),
                                    1
                                  )) *
                                  100
                              )}%`,
                            }}
                          >
                            <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100">
                              {d.count}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="flex gap-1 mt-1">
                        {qualityCheck.data.complexity_distribution.map((d) => (
                          <div
                            key={d.level}
                            className="flex-1 text-center text-[10px] text-muted-foreground"
                          >
                            {d.level}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Issues */}
                {qualityCheck.data.issues.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        Issues ({qualityCheck.data.issues.length} pages)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {qualityCheck.data.issues.map((issue) => (
                          <div
                            key={issue.page_id}
                            className="flex items-start gap-3 border rounded-md p-3"
                          >
                            <span className="text-sm font-medium min-w-[60px]">
                              Page {issue.page_number}
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {issue.issues.map((text, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {text}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <div className="border rounded-lg p-12 text-center">
                <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="text-lg font-medium mb-2">
                  No quality data yet
                </h3>
                <p className="text-muted-foreground mb-4">
                  Run a quality check to see your book&apos;s quality dashboard.
                </p>
                <Button
                  onClick={() => qualityCheck.mutate()}
                  disabled={qualityCheck.isPending}
                >
                  {qualityCheck.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <ShieldCheck className="h-4 w-4 mr-2" />
                  )}
                  Run Quality Check
                </Button>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Batch Tab */}
        <TabsContent value="batch" className="mt-6">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Batch Generation</h2>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Generate all {book.page_count} pages at once with auto-QA
                </p>
              </div>
              <Button
                onClick={() => batchGenerate.mutate()}
                disabled={batchGenerate.isPending}
              >
                {batchGenerate.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {batchGenerate.isPending
                  ? "Generating..."
                  : "Start Batch Generation"}
              </Button>
            </div>

            {batchGenerate.data && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Batch Progress</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Progress
                    value={
                      (batchGenerate.data.completed_pages /
                        batchGenerate.data.total_pages) *
                      100
                    }
                    className="h-3"
                  />
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <p className="text-muted-foreground">Total</p>
                      <p className="text-lg font-bold">
                        {batchGenerate.data.total_pages}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-muted-foreground">Completed</p>
                      <p className="text-lg font-bold text-green-600">
                        {batchGenerate.data.completed_pages}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-muted-foreground">Failed</p>
                      <p className="text-lg font-bold text-red-600">
                        {batchGenerate.data.failed_pages}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        batchGenerate.data.status === "completed"
                          ? "default"
                          : "secondary"
                      }
                      className="capitalize"
                    >
                      {batchGenerate.data.status}
                    </Badge>
                    {batchGenerate.data.status === "completed" && (
                      <span className="flex items-center gap-1 text-sm text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        All pages generated with auto-QA
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-base">How It Works</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
                  <li>
                    All {book.page_count} pages are queued for generation based
                    on your theme: &quot;{book.theme_description}&quot;
                  </li>
                  <li>
                    Each page goes through the 7-step quality pipeline
                    automatically
                  </li>
                  <li>
                    Variation mode prevents similar compositions across pages
                  </li>
                  <li>
                    Auto-QA runs on each page after generation
                  </li>
                  <li>
                    Review and manually adjust any pages that need attention
                  </li>
                </ol>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Series Tab */}
        <TabsContent value="series" className="mt-6">
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Series & Volume Planning</h2>

            {book.series_name ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    {book.series_name}
                  </CardTitle>
                  <CardDescription>
                    Volume {book.volume_number} of the series
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Series Name</p>
                      <p className="font-medium">{book.series_name}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Volume</p>
                      <p className="font-medium">{book.volume_number}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Style</p>
                      <p className="font-medium capitalize">
                        {book.line_style.replace(/_/g, " ")}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Format</p>
                      <p className="font-medium">{book.trim_size}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button variant="outline" size="sm">
                      <Layers className="h-4 w-4 mr-2" />
                      Auto-Generate Next Volume
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Batch Export All Volumes
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="border rounded-lg p-12 text-center">
                <Library className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="text-lg font-medium mb-2">
                  Not part of a series
                </h3>
                <p className="text-muted-foreground mb-4">
                  This book is standalone. You can plan a multi-volume series to
                  create consistent branding across volumes.
                </p>
                <Button variant="outline">
                  <Library className="h-4 w-4 mr-2" />
                  Create Series Plan
                </Button>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="mt-6">
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Export & Publish</h2>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Export Format</CardTitle>
                <CardDescription>
                  B&W interior, single-sided with blank backs enforced.
                  Coloring-safe inner margin applied.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select
                  value={exportFormat}
                  onValueChange={(v) =>
                    setExportFormat(v as ExportOptions["format"])
                  }
                >
                  <SelectTrigger className="w-64">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">
                      Print-Ready PDF (KDP)
                    </SelectItem>
                    <SelectItem value="png">Individual PNGs</SelectItem>
                    <SelectItem value="svg">SVG Vector Package</SelectItem>
                    <SelectItem value="digital_pdf">Digital PDF</SelectItem>
                  </SelectContent>
                </Select>

                <div className="text-sm text-muted-foreground space-y-1">
                  <p>
                    Total pages: {book.page_count} coloring +{" "}
                    {book.page_count} blank backs +{" "}
                    {book.bonus_pages?.length ?? 0} bonus ={" "}
                    {book.page_count * 2 + (book.bonus_pages?.length ?? 0)}{" "}
                    pages
                  </p>
                  <p>DPI: 300 | Format: B&W | Trim: {book.trim_size}</p>
                </div>

                <Button
                  onClick={handleExport}
                  disabled={exportBook.isPending}
                  className="mt-2"
                >
                  {exportBook.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4 mr-2" />
                  )}
                  {exportBook.isPending ? "Exporting..." : "Export"}
                </Button>

                {exportBook.data && (
                  <div className="border rounded-md p-3 mt-3 flex items-center justify-between">
                    <div className="text-sm">
                      <p className="font-medium">
                        {exportBook.data.format.toUpperCase()} Ready
                      </p>
                      <p className="text-muted-foreground">
                        {exportBook.data.page_count} pages &bull;{" "}
                        {(exportBook.data.file_size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href={exportBook.data.download_url}
                        download
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Preflight checklist */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Preflight Checklist</CardTitle>
                <CardDescription>
                  Checks that run before export
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {[
                    "Pure B&W verified (no accidental color)",
                    "300 DPI resolution",
                    "Stroke uniformity passed",
                    "All shapes closed",
                    "No specks or artifacts",
                    "Ink density within limits",
                    "No duplicate pages",
                    "Grayscale verified",
                    "Font licensing cleared",
                    "Coloring-safe margin applied",
                  ].map((check) => (
                    <li key={check} className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-muted-foreground/40" />
                      <span className="text-muted-foreground">{check}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Reviews Tab */}
        <TabsContent value="reviews" className="mt-6">
          <ReviewFeedbackPanel bookType="coloring-books" bookId={bookId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
