"use client";

import { useState } from "react";
import { useGenerateReport, type ReportRequest } from "../hooks";

const REPORT_TYPES = [
  { value: "revenue_summary", label: "Revenue Summary" },
  { value: "book_performance", label: "Book Performance" },
  { value: "marketing_roi", label: "Marketing ROI" },
  { value: "portfolio_overview", label: "Portfolio Overview" },
] as const;

const OUTPUT_FORMATS = [
  { value: "pdf", label: "PDF" },
  { value: "xlsx", label: "Excel (XLSX)" },
] as const;

export function ReportBuilder() {
  const [title, setTitle] = useState("");
  const [reportType, setReportType] = useState<ReportRequest["report_type"]>("revenue_summary");
  const [outputFormat, setOutputFormat] = useState<ReportRequest["output_format"]>("pdf");

  const generateReport = useGenerateReport();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    generateReport.mutate({
      title: title.trim(),
      report_type: reportType,
      output_format: outputFormat,
      parameters: {},
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Report</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="report-title" className="block text-sm font-medium text-gray-700 mb-1">
            Report Title
          </label>
          <input
            id="report-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Q1 2024 Revenue Summary"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="report-type" className="block text-sm font-medium text-gray-700 mb-1">
              Report Type
            </label>
            <select
              id="report-type"
              value={reportType}
              onChange={(e) => setReportType(e.target.value as ReportRequest["report_type"])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {REPORT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="output-format" className="block text-sm font-medium text-gray-700 mb-1">
              Format
            </label>
            <select
              id="output-format"
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as ReportRequest["output_format"])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {OUTPUT_FORMATS.map((fmt) => (
                <option key={fmt.value} value={fmt.value}>
                  {fmt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={generateReport.isPending || !title.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generateReport.isPending ? "Generating..." : "Generate Report"}
        </button>

        {generateReport.isSuccess && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">
              Report generated successfully! Check the reports list to download.
            </p>
          </div>
        )}

        {generateReport.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              Failed to generate report: {generateReport.error.message}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
