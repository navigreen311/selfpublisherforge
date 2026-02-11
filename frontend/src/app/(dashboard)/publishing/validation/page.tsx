"use client";

import { useState } from "react";
import { ValidationDashboard } from "@/modules/publishing/components/ValidationDashboard";
import { ValidationRunner } from "@/modules/publishing/components/ValidationRunner";
import { ValidationResults } from "@/modules/publishing/components/ValidationResults";
import {
  useRunFullValidation,
  type FullValidationRequest,
  type FullValidationResponse,
} from "@/modules/publishing/hooks";
import { toast } from "sonner";

export default function ValidationPage() {
  const [selectedBookId, setSelectedBookId] = useState("sample-book-id");
  const [validationResult, setValidationResult] = useState<FullValidationResponse | null>(null);

  const runValidation = useRunFullValidation();

  const handleRunValidation = (request: FullValidationRequest) => {
    runValidation.mutate(request, {
      onSuccess: (data) => {
        setValidationResult(data);
        toast.success("Validation complete");
      },
      onError: () => {
        toast.error("Validation failed");
      },
    });
  };

  const handleExportPdf = () => {
    toast.info("PDF export functionality coming soon");
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">KDP Validation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pre-flight validation for Amazon KDP print and ebook requirements
        </p>
      </div>

      {/* Book Selector */}
      <div className="rounded-lg border bg-card p-4">
        <label htmlFor="book-selector" className="block text-sm font-medium text-foreground mb-2">
          Select Book to Validate
        </label>
        <select
          id="book-selector"
          value={selectedBookId}
          onChange={(e) => setSelectedBookId(e.target.value)}
          className="w-full max-w-md rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="sample-book-id">Sample Book - The Great Adventure</option>
          <option value="book-2">Mystery Novel - Dark Secrets</option>
          <option value="book-3">Non-Fiction - How to Self-Publish</option>
        </select>
      </div>

      {/* Dashboard */}
      <ValidationDashboard
        validation={validationResult}
        onRunValidation={() =>
          handleRunValidation({
            print_validation: {
              trim_size: "6x9",
              page_count: 200,
              inside_margin: 0.75,
              outside_margin: 0.5,
              top_margin: 0.75,
              bottom_margin: 0.75,
            },
            ebook_validation: {
              has_ncx_toc: true,
              has_html_toc: true,
              file_size_bytes: 5000000,
            },
            cover_validation: {
              width_inches: 6,
              height_inches: 9,
              dpi: 300,
              file_format: "JPEG",
            },
            compliance_scan: {
              title: "Sample Book",
              description: "A sample description",
              keywords: ["fiction", "adventure"],
            },
          })
        }
        isRunning={runValidation.isPending}
      />

      {/* Runner */}
      <ValidationRunner
        bookId={selectedBookId}
        onRun={handleRunValidation}
        isRunning={runValidation.isPending}
      />

      {/* Results */}
      {validationResult && (
        <ValidationResults validation={validationResult} onExportPdf={handleExportPdf} />
      )}
    </div>
  );
}
