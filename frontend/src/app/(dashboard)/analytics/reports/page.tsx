"use client";

import { useState, useEffect, useCallback } from "react";
import { useReports, useDownloadReport } from "@/modules/analytics/hooks";
import type { ReportResponse } from "@/modules/analytics/hooks";
import { ReportBuilder } from "@/modules/analytics/components/ReportBuilder";
import { useTranslations } from "@/hooks/use-translations";

export default function ReportsPage() {
  const t = useTranslations("analytics");
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [allItems, setAllItems] = useState<ReportResponse[]>([]);
  const { data: reports, isLoading, isFetching } = useReports(cursor);
  const downloadReport = useDownloadReport();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Accumulate items as new pages are loaded
  useEffect(() => {
    if (reports?.items) {
      if (!cursor) {
        // First page — replace all items
        setAllItems(reports.items);
      } else {
        // Subsequent pages — append new items, deduplicating by id
        setAllItems((prev) => {
          const existingIds = new Set(prev.map((item) => item.id));
          const newItems = reports.items.filter(
            (item) => !existingIds.has(item.id)
          );
          return [...prev, ...newItems];
        });
      }
    }
  }, [reports, cursor]);

  const handleLoadMore = useCallback(() => {
    if (reports?.next_cursor) {
      setCursor(reports.next_cursor);
    }
  }, [reports?.next_cursor]);

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

  const displayItems = allItems.length > 0 ? allItems : reports?.items ?? [];
  const isLoadingMore = isFetching && !!cursor;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">{t("reports.title")}</h1>
        <a
          href="/analytics"
          aria-label={t("reports.backToDashboard")}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {t("reports.backToDashboard")}
        </a>
      </div>

      {downloadError && (
        <div
          className="rounded-md bg-red-50 border border-red-200 p-4"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex">
            <div className="flex-1">
              <p className="text-sm text-red-800">{downloadError}</p>
            </div>
            <button
              type="button"
              aria-label={t("reports.errorDismiss")}
              className="ml-3 text-red-500 hover:text-red-700"
              onClick={() => setDownloadError(null)}
            >
              <span className="sr-only">{t("reports.errorDismissSr")}</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
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
        <div className="lg:col-span-1" role="region" aria-label={t("reports.reportBuilder")}>
          <ReportBuilder />
        </div>

        {/* Reports List */}
        <div className="lg:col-span-2" role="region" aria-label={t("reports.generatedReports")}>
          <div className="bg-card rounded-lg border border-border shadow-sm">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-foreground" id="reports-table-heading">
                {t("reports.generatedReports")}
              </h3>
            </div>

            <div aria-live="polite" aria-atomic="true">
              {isLoading && !cursor ? (
                <div className="p-6" role="status" aria-label={t("reports.loadingReports")}>
                  <span className="sr-only">{t("reports.loadingReports")}</span>
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="animate-pulse flex items-center space-x-4">
                        <div className="h-10 bg-muted rounded flex-1" />
                        <div className="h-10 bg-muted rounded w-24" />
                      </div>
                    ))}
                  </div>
                </div>
              ) : displayItems.length > 0 ? (
                <>
                  <p id="reports-table-desc" className="sr-only">
                    {t("reports.tableDescription", { count: displayItems.length })}
                  </p>
                  <table
                    className="w-full"
                    aria-describedby="reports-table-desc"
                    aria-labelledby="reports-table-heading"
                  >
                    <caption className="sr-only">
                      {t("reports.tableCaption")}
                    </caption>
                    <thead className="sr-only">
                      <tr>
                        <th scope="col">{t("reports.reportDetails")}</th>
                        <th scope="col">{t("reports.actions")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {displayItems.map((report) => (
                        <tr key={report.id} className="hover:bg-muted/50">
                          <td className="p-4">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground truncate">{report.title}</p>
                              <div className="flex items-center space-x-4 mt-1">
                                <span className="text-xs text-muted-foreground capitalize">
                                  {report.report_type.replace("_", " ")}
                                </span>
                                <span className="text-xs text-muted-foreground uppercase">{report.output_format}</span>
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                    report.status === "completed"
                                      ? "bg-green-100 text-green-800"
                                      : report.status === "failed"
                                        ? "bg-red-100 text-red-800"
                                        : report.status === "processing"
                                          ? "bg-yellow-100 text-yellow-800"
                                          : "bg-muted text-muted-foreground"
                                  }`}
                                  role="status"
                                  aria-label={t("reports.status", { status: report.status })}
                                >
                                  {report.status}
                                </span>
                                {report.file_size && (
                                  <span className="text-xs text-muted-foreground">
                                    {(report.file_size / 1024).toFixed(1)} KB
                                  </span>
                                )}
                              </div>
                              {report.generated_at && (
                                <p className="text-xs text-muted-foreground/70 mt-1">
                                  {t("reports.generated", { date: new Date(report.generated_at).toLocaleString() })}
                                </p>
                              )}
                            </div>
                          </td>
                          <td className="p-4 text-right">
                            {report.status === "completed" && (
                              <button
                                onClick={() =>
                                  handleDownload(report.id, `${report.title}.${report.output_format}`)
                                }
                                disabled={downloadReport.isPending}
                                aria-label={t("reports.downloadLabel", { title: report.title })}
                                className="px-3 py-1.5 text-sm font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50"
                              >
                                {t("reports.download")}
                              </button>
                            )}
                            {report.status === "failed" && report.error_message && (
                              <span
                                className="text-xs text-red-600"
                                title={report.error_message}
                                role="alert"
                                aria-label={t("reports.errorLabel", { title: report.title, message: report.error_message })}
                              >
                                {t("reports.error")}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <div className="p-6 text-center">
                  <p className="text-muted-foreground">{t("reports.noReports")}</p>
                </div>
              )}
            </div>

            {reports?.has_more && (
              <div className="p-4 border-t border-border text-center">
                <button
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  aria-label={t("reports.loadMore")}
                  className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
                >
                  {isLoadingMore ? t("reports.loading") : t("reports.loadMore")}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
