"use client";

import { useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info } from "lucide-react";
import { ValidationFix } from "./ValidationFix";
import type { ValidationResult, ValidationIssue } from "../hooks";

interface ValidationChecklistProps {
  result: ValidationResult;
}

export function ValidationChecklist({ result }: ValidationChecklistProps) {
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);

  const getIssueIcon = (severity: ValidationIssue["severity"]) => {
    switch (severity) {
      case "error":
        return <XCircle className="h-5 w-5 text-red-600" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case "info":
        return <Info className="h-5 w-5 text-blue-600" />;
    }
  };

  const getIssueColor = (severity: ValidationIssue["severity"]) => {
    switch (severity) {
      case "error":
        return "border-red-200 bg-red-50";
      case "warning":
        return "border-yellow-200 bg-yellow-50";
      case "info":
        return "border-blue-200 bg-blue-50";
    }
  };

  const getTextColor = (severity: ValidationIssue["severity"]) => {
    switch (severity) {
      case "error":
        return "text-red-900";
      case "warning":
        return "text-yellow-900";
      case "info":
        return "text-blue-900";
    }
  };

  // If no issues, show success
  if (result.issues.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
        <CheckCircle className="h-6 w-6 text-green-600" />
        <div>
          <h5 className="font-semibold text-green-900">All Checks Passed</h5>
          <p className="text-sm text-green-700">
            No issues found in {result.validation_type} validation
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {result.issues.map((issue, index) => {
        const issueKey = `${result.validation_type}-${index}`;
        const isExpanded = expandedIssue === issueKey;

        return (
          <div key={issueKey} className={`rounded-lg border ${getIssueColor(issue.severity)}`}>
            <button
              onClick={() => setExpandedIssue(isExpanded ? null : issueKey)}
              className="flex w-full items-start gap-3 p-3 text-left hover:opacity-80"
            >
              {getIssueIcon(issue.severity)}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h5 className={`font-semibold ${getTextColor(issue.severity)}`}>
                      {issue.rule}
                    </h5>
                    <p className={`mt-1 text-sm ${getTextColor(issue.severity)}`}>
                      {issue.message}
                    </p>
                    {issue.location && (
                      <p className={`mt-1 text-xs ${getTextColor(issue.severity)} opacity-75`}>
                        Location: {issue.location}
                      </p>
                    )}
                  </div>
                  <svg
                    className={`h-4 w-4 flex-shrink-0 transition-transform ${
                      isExpanded ? "rotate-180" : ""
                    } ${getTextColor(issue.severity)}`}
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
                </div>
              </div>
            </button>

            {isExpanded && (
              <div className="border-t px-3 pb-3 pt-2">
                <ValidationFix issue={issue} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
