"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { ValidationChecklist } from "./ValidationChecklist";
import type { FullValidationResponse } from "../hooks";

interface ValidationResultsProps {
  validation: FullValidationResponse;
  onExportPdf?: () => void;
}

export function ValidationResults({ validation, onExportPdf }: ValidationResultsProps) {
  const [expandedType, setExpandedType] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {/* Header with Export */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Validation Results</h3>
        {onExportPdf && (
          <button
            onClick={onExportPdf}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Export Report as PDF
          </button>
        )}
      </div>

      {/* Results by Type */}
      <div className="space-y-4">
        {validation.results.map((result) => (
          <Card key={result.validation_type} className="overflow-hidden">
            <button
              onClick={() =>
                setExpandedType(
                  expandedType === result.validation_type ? null : result.validation_type
                )
              }
              className="flex w-full items-center justify-between p-4 text-left hover:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`h-3 w-3 rounded-full ${
                    result.status === "passed"
                      ? "bg-green-600"
                      : result.status === "warnings"
                      ? "bg-yellow-600"
                      : result.status === "failed"
                      ? "bg-red-600"
                      : "bg-gray-400"
                  }`}
                />
                <div>
                  <h4 className="font-semibold text-gray-900 capitalize">
                    {result.validation_type} Validation
                  </h4>
                  <p className="text-sm text-gray-600">
                    {result.issues.length === 0
                      ? "No issues found"
                      : `${result.issues.filter((i) => i.severity === "error").length} errors, ${
                          result.issues.filter((i) => i.severity === "warning").length
                        } warnings`}
                  </p>
                </div>
              </div>
              <svg
                className={`h-5 w-5 text-gray-400 transition-transform ${
                  expandedType === result.validation_type ? "rotate-180" : ""
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {expandedType === result.validation_type && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <ValidationChecklist result={result} />
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Summary */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Summary</h4>
        <p className="text-sm text-blue-800">
          {validation.total_errors === 0 && validation.total_warnings === 0
            ? "All validation checks passed! Your book is ready to publish on KDP."
            : validation.total_errors === 0
            ? `All critical checks passed. Review ${validation.total_warnings} warning${
                validation.total_warnings !== 1 ? "s" : ""
              } before publishing.`
            : `Found ${validation.total_errors} critical error${
                validation.total_errors !== 1 ? "s" : ""
              } that must be fixed before publishing.`}
        </p>
      </Card>
    </div>
  );
}
