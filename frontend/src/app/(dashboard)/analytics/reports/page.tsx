"use client";

import { useState } from "react";
import { useReports, useDownloadReport } from "@/modules/analytics/hooks";
import { ReportBuilder } from "@/modules/analytics/components/ReportBuilder";

export default function ReportsPage() {
  const { data: reports, isLoading } = useReports();
  const downloadReport = useDownloadReport();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = (reportId: string, fileName: string) => {
    setDownloadError(null);

    downloadReport.mutate(reportId, {
      onSuccess: (blob) => {
        // Validate the blob before attempting to create a download URL
        if (!blob || blob.size === 0) {
          setDownloadError("Downloaded file is empty. Please try again or regenerate the report.");
          return;
        }

        let url: string | undefined;
        try {
          url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          a.remove();
        } catch (err) {
          setDownloadError(
            err instanceof Error
              ? `Failed to prepare download: ${err.message}`
              : "Failed to prepare download. Please try again."
          );
        } finally {
          if (url) {
            window.URL.revokeObjectURL(url);
          }
        }
      },
      onError: (error) => {
        setDownloadError(
          error.message || "Failed to download report. Please try again."
        );
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <a
          href="/analytics"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Back to Dashboard
        </a>
      </div>

      {downloadError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4">
          <div className="flex">
            <div className="flex-1">
              <p className="text-sm text-red-800">{downloadError}</p>
            </div>
            <button
              type="button"
              className="ml-3 text-red-500 hover:text-red-700"
              onClick={() => setDownloadError(null)}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Builder */}
        <div className="lg:col-span-1">
          <ReportBuilder />
        </div>

        {/* Reports List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Generated Reports</h3>
            </div>

            {isLoading ? (
              <div className="p-6">
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse flex items-center space-x-4">
                      <div className="h-10 bg-gray-200 rounded flex-1" />
                      <div className="h-10 bg-gray-200 rounded w-24" />
                    </div>
                  ))}
                </div>
              </div>
            ) : reports?.items && reports.items.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {reports.items.map((report) => (
                  <div key={report.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{report.title}</p>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className="text-xs text-gray-500 capitalize">
                          {report.report_type.replace("_", " ")}
                        </span>
                        <span className="text-xs text-gray-500 uppercase">{report.output_format}</span>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            report.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : report.status === "failed"
                                ? "bg-red-100 text-red-800"
                                : report.status === "processing"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {report.status}
                        </span>
                        {report.file_size && (
                          <span className="text-xs text-gray-500">
                            {(report.file_size / 1024).toFixed(1)} KB
                          </span>
                        )}
                      </div>
                      {report.generated_at && (
                        <p className="text-xs text-gray-400 mt-1">
                          Generated: {new Date(report.generated_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="ml-4">
                      {report.status === "completed" && (
                        <button
                          onClick={() =>
                            handleDownload(report.id, `${report.title}.${report.output_format}`)
                          }
                          disabled={downloadReport.isPending}
                          className="px-3 py-1.5 text-sm font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50"
                        >
                          Download
                        </button>
                      )}
                      {report.status === "failed" && report.error_message && (
                        <span className="text-xs text-red-600" title={report.error_message}>
                          Error
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center">
                <p className="text-gray-500">No reports generated yet. Use the builder to create one.</p>
              </div>
            )}

            {reports?.has_more && (
              <div className="p-4 border-t border-gray-200 text-center">
                <button className="text-sm text-blue-600 hover:text-blue-800">
                  Load More
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
