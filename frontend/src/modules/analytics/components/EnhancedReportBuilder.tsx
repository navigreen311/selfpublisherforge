"use client";

import { useState } from "react";
import {
  FileText,
  FileSpreadsheet,
  FileDown,
  Eye,
  Loader2,
  ClipboardList,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/modules/projects/hooks";
import {
  useGenerateEnhancedReport,
  useReports,
  useDownloadReport,
} from "../hooks";
import type { ReportResponse, EnhancedReportRequest } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REPORT_TYPES = [
  { value: "revenue_summary", label: "Revenue Summary" },
  { value: "book_performance", label: "Book Performance" },
  { value: "advertising_roi", label: "Advertising ROI" },
  { value: "royalty_statement", label: "Royalty Statement" },
  { value: "full_business_report", label: "Full Business Report" },
] as const;

const OUTPUT_FORMATS = [
  { value: "pdf", label: "PDF" },
  { value: "xlsx", label: "Excel (XLSX)" },
  { value: "csv", label: "CSV" },
] as const;

const INCLUDE_SECTIONS = [
  { id: "revenue_breakdown", label: "Revenue breakdown" },
  { id: "sales_by_format", label: "Sales by format" },
  { id: "sales_by_marketplace", label: "Sales by marketplace" },
  { id: "advertising_summary", label: "Advertising summary" },
  { id: "bsr_tracking", label: "BSR tracking" },
  { id: "ai_insights", label: "AI insights & recommendations" },
] as const;

type ReportType = (typeof REPORT_TYPES)[number]["value"];
type OutputFormat = (typeof OUTPUT_FORMATS)[number]["value"];
type SectionId = (typeof INCLUDE_SECTIONS)[number]["id"];

// ---------------------------------------------------------------------------
// Helper: format file size
// ---------------------------------------------------------------------------

function formatFileSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Helper: format icon based on output format
// ---------------------------------------------------------------------------

function FormatIcon({ format }: { format: string }) {
  if (format === "pdf") {
    return <FileText className="h-5 w-5 text-red-500 shrink-0" />;
  }
  if (format === "xlsx") {
    return <FileSpreadsheet className="h-5 w-5 text-green-600 shrink-0" />;
  }
  return <FileDown className="h-5 w-5 text-blue-500 shrink-0" />;
}

// ---------------------------------------------------------------------------
// Helper: format badge variant by output format
// ---------------------------------------------------------------------------

function formatBadgeClass(format: string): string {
  switch (format) {
    case "pdf":
      return "bg-red-100 text-red-800 border-red-200";
    case "xlsx":
      return "bg-green-100 text-green-800 border-green-200";
    case "csv":
      return "bg-blue-100 text-blue-800 border-blue-200";
    default:
      return "";
  }
}

// ---------------------------------------------------------------------------
// Left Panel: Generate Report Form
// ---------------------------------------------------------------------------

function GenerateReportForm() {
  const [title, setTitle] = useState("");
  const [reportType, setReportType] = useState<ReportType>("revenue_summary");
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("pdf");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [allBooks, setAllBooks] = useState(true);
  const [selectedBookIds, setSelectedBookIds] = useState<string[]>([]);
  const [selectedSections, setSelectedSections] = useState<SectionId[]>([
    "revenue_breakdown",
    "sales_by_format",
    "sales_by_marketplace",
  ]);

  const { data: projects, isLoading: projectsLoading } = useProjects();
  const generateReport = useGenerateEnhancedReport();

  const toggleBook = (bookId: string) => {
    setSelectedBookIds((prev) =>
      prev.includes(bookId)
        ? prev.filter((id) => id !== bookId)
        : [...prev, bookId]
    );
  };

  const toggleSection = (sectionId: SectionId) => {
    setSelectedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((id) => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const request: EnhancedReportRequest = {
      title: title.trim(),
      report_type: reportType,
      format: outputFormat,
      ...(periodStart && { period_start: periodStart }),
      ...(periodEnd && { period_end: periodEnd }),
      ...(!allBooks &&
        selectedBookIds.length > 0 && { book_ids: selectedBookIds }),
      ...(selectedSections.length > 0 && { sections: selectedSections }),
    };

    generateReport.mutate(request, {
      onSuccess: () => {
        setTitle("");
        setPeriodStart("");
        setPeriodEnd("");
        setSelectedBookIds([]);
        setAllBooks(true);
        setSelectedSections([
          "revenue_breakdown",
          "sales_by_format",
          "sales_by_marketplace",
        ]);
      },
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <ClipboardList className="h-5 w-5" />
          Generate Report
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Report Title */}
          <Input
            label="Report Title"
            id="enhanced-report-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Q1 2026 Revenue Summary"
            required
          />

          {/* Report Type */}
          <div className="space-y-1.5">
            <Label htmlFor="enhanced-report-type">Report Type</Label>
            <Select
              value={reportType}
              onValueChange={(v) => setReportType(v as ReportType)}
            >
              <SelectTrigger id="enhanced-report-type">
                <SelectValue placeholder="Select report type" />
              </SelectTrigger>
              <SelectContent>
                {REPORT_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Period (Date Range) */}
          <div className="space-y-1.5">
            <Label>Period</Label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="period-start"
                  className="text-xs text-muted-foreground mb-1 block"
                >
                  Start Date
                </label>
                <input
                  id="period-start"
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <div>
                <label
                  htmlFor="period-end"
                  className="text-xs text-muted-foreground mb-1 block"
                >
                  End Date
                </label>
                <input
                  id="period-end"
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
            </div>
          </div>

          {/* Books Selection */}
          <div className="space-y-2">
            <Label>Books</Label>
            <div className="flex items-center gap-2">
              <Checkbox
                id="all-books"
                checked={allBooks}
                onCheckedChange={(checked) => {
                  setAllBooks(checked === true);
                  if (checked) setSelectedBookIds([]);
                }}
              />
              <label
                htmlFor="all-books"
                className="text-sm font-medium leading-none cursor-pointer"
              >
                All books
              </label>
            </div>

            {!allBooks && (
              <div className="mt-2 max-h-40 overflow-y-auto rounded-md border border-input p-3 space-y-2">
                {projectsLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-full" />
                    <Skeleton className="h-5 w-full" />
                    <Skeleton className="h-5 w-3/4" />
                  </div>
                ) : projects && projects.length > 0 ? (
                  projects.map((project) => (
                    <div key={project.id} className="flex items-center gap-2">
                      <Checkbox
                        id={`book-${project.id}`}
                        checked={selectedBookIds.includes(project.id)}
                        onCheckedChange={() => toggleBook(project.id)}
                      />
                      <label
                        htmlFor={`book-${project.id}`}
                        className="text-sm leading-none cursor-pointer truncate"
                      >
                        {project.title}
                      </label>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No books found. Create a project first.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Output Format */}
          <div className="space-y-1.5">
            <Label htmlFor="enhanced-output-format">Format</Label>
            <Select
              value={outputFormat}
              onValueChange={(v) => setOutputFormat(v as OutputFormat)}
            >
              <SelectTrigger id="enhanced-output-format">
                <SelectValue placeholder="Select format" />
              </SelectTrigger>
              <SelectContent>
                {OUTPUT_FORMATS.map((fmt) => (
                  <SelectItem key={fmt.value} value={fmt.value}>
                    {fmt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Include Sections */}
          <div className="space-y-2">
            <Label>Include Sections</Label>
            <div className="space-y-2 rounded-md border border-input p-3">
              {INCLUDE_SECTIONS.map((section) => (
                <div key={section.id} className="flex items-center gap-2">
                  <Checkbox
                    id={`section-${section.id}`}
                    checked={selectedSections.includes(section.id)}
                    onCheckedChange={() => toggleSection(section.id)}
                  />
                  <label
                    htmlFor={`section-${section.id}`}
                    className="text-sm leading-none cursor-pointer"
                  >
                    {section.label}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            className="w-full"
            disabled={generateReport.isPending || !title.trim()}
          >
            {generateReport.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              "Generate Report"
            )}
          </Button>

          {/* Success feedback */}
          {generateReport.isSuccess && (
            <div className="rounded-md bg-green-50 border border-green-200 p-3">
              <p className="text-sm text-green-800">
                Report generation started. It will appear in the list once
                complete.
              </p>
            </div>
          )}

          {/* Error feedback */}
          {generateReport.isError && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-800">
                Failed to generate report:{" "}
                {generateReport.error?.message ?? "Unknown error"}
              </p>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Right Panel: Generated Reports List
// ---------------------------------------------------------------------------

function GeneratedReportsList() {
  const { data: reports, isLoading } = useReports();
  const downloadReport = useDownloadReport();

  const handleDownload = (report: ReportResponse) => {
    downloadReport.mutate(report.id, {
      onSuccess: (blob) => {
        if (!blob || blob.size === 0) return;
        let url: string | undefined;
        try {
          url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${report.title}.${report.output_format}`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        } finally {
          if (url) window.URL.revokeObjectURL(url);
        }
      },
    });
  };

  const handleView = (report: ReportResponse) => {
    // For PDF, open in a new tab via blob URL; for other formats, trigger download
    downloadReport.mutate(report.id, {
      onSuccess: (blob) => {
        if (!blob || blob.size === 0) return;
        const url = window.URL.createObjectURL(blob);
        window.open(url, "_blank");
        // Revoke after a delay so the browser has time to open
        setTimeout(() => window.URL.revokeObjectURL(url), 10000);
      },
    });
  };

  const items = reports?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Generated Reports
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/40 mb-4" />
            <p className="text-muted-foreground font-medium">
              No reports generated yet
            </p>
            <p className="text-sm text-muted-foreground/70 mt-1">
              Use the form to generate your first report.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((report) => (
              <ReportRow
                key={report.id}
                report={report}
                onDownload={handleDownload}
                onView={handleView}
                isDownloading={downloadReport.isPending}
              />
            ))}

            {reports?.has_more && (
              <p className="text-xs text-center text-muted-foreground pt-2">
                Showing {items.length} of {reports.total_count ?? "many"}{" "}
                reports
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Single Report Row
// ---------------------------------------------------------------------------

function ReportRow({
  report,
  onDownload,
  onView,
  isDownloading,
}: {
  report: ReportResponse;
  onDownload: (report: ReportResponse) => void;
  onView: (report: ReportResponse) => void;
  isDownloading: boolean;
}) {
  const isCompleted = report.status === "completed";
  const isFailed = report.status === "failed";
  const isProcessing = report.status === "processing";

  return (
    <div className="flex items-start gap-3 rounded-lg border border-border p-3 hover:bg-muted/50 transition-colors">
      {/* Icon */}
      <div className="mt-0.5">
        <FormatIcon format={report.output_format} />
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {report.title}
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-1">
          <Badge
            variant="outline"
            className={formatBadgeClass(report.output_format)}
          >
            {report.output_format.toUpperCase()}
          </Badge>
          {isProcessing && (
            <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-200">
              Processing
            </Badge>
          )}
          {isFailed && (
            <Badge variant="destructive">Failed</Badge>
          )}
          {isCompleted && (
            <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
              Ready
            </Badge>
          )}
          {report.file_size != null && report.file_size > 0 && (
            <span className="text-xs text-muted-foreground">
              {formatFileSize(report.file_size)}
            </span>
          )}
        </div>
        {report.generated_at && (
          <p className="text-xs text-muted-foreground/70 mt-1">
            {new Date(report.generated_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
        {isFailed && report.error_message && (
          <p className="text-xs text-destructive mt-1 truncate" title={report.error_message}>
            {report.error_message}
          </p>
        )}
      </div>

      {/* Actions */}
      {isCompleted && (
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onView(report)}
            disabled={isDownloading}
            aria-label={`View ${report.title}`}
            title="View"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDownload(report)}
            disabled={isDownloading}
            aria-label={`Download ${report.title}`}
            title="Download"
          >
            <FileDown className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function EnhancedReportBuilder() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Panel - Generate Report Form */}
      <div role="region" aria-label="Generate Report">
        <GenerateReportForm />
      </div>

      {/* Right Panel - Generated Reports List */}
      <div role="region" aria-label="Generated Reports" aria-live="polite" aria-atomic="false">
        <GeneratedReportsList />
      </div>
    </div>
  );
}
