"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, AlertTriangle, FileCheck } from "lucide-react";
import type { FullValidationResponse, ValidationStatus } from "../hooks";

interface ValidationDashboardProps {
  validation: FullValidationResponse | null;
  onRunValidation: () => void;
  isRunning: boolean;
}

export function ValidationDashboard({
  validation,
  onRunValidation,
  isRunning,
}: ValidationDashboardProps) {
  const getStatusIcon = (status: ValidationStatus) => {
    switch (status) {
      case "passed":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-600" />;
      case "warnings":
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      default:
        return <FileCheck className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: ValidationStatus) => {
    switch (status) {
      case "passed":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Passed</Badge>;
      case "failed":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Failed</Badge>;
      case "warnings":
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">Warnings</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">Pending</Badge>;
    }
  };

  const readinessScore = validation
    ? Math.round(
        ((validation.results.filter((r) => r.status === "passed").length +
          validation.results.filter((r) => r.status === "warnings").length * 0.5) /
          validation.results.length) *
          100
      )
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">KDP Pre-Flight Validation</h2>
          <p className="mt-1 text-sm text-gray-600">
            Check your manuscript against KDP requirements before publishing
          </p>
        </div>
        <button
          onClick={onRunValidation}
          disabled={isRunning}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isRunning ? "Running..." : "Run Validation"}
        </button>
      </div>

      {/* Overall Status Card */}
      {validation && (
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(validation.overall_status)}
              <div>
                <h3 className="font-semibold text-gray-900">Overall Status</h3>
                <p className="text-sm text-gray-600">
                  Last checked: {new Date(validation.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            {getStatusBadge(validation.overall_status)}
          </div>

          {/* Readiness Score */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Readiness Score</span>
              <span className="text-2xl font-bold text-indigo-600">{readinessScore}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className={`h-2 rounded-full transition-all ${
                  readinessScore >= 80
                    ? "bg-green-600"
                    : readinessScore >= 50
                    ? "bg-yellow-600"
                    : "bg-red-600"
                }`}
                style={{ width: `${readinessScore}%` }}
              />
            </div>
          </div>

          {/* Issue Summary */}
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm font-medium text-red-900">Errors</span>
              </div>
              <p className="mt-1 text-2xl font-bold text-red-600">{validation.total_errors}</p>
            </div>
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Warnings</span>
              </div>
              <p className="mt-1 text-2xl font-bold text-yellow-600">{validation.total_warnings}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!validation && !isRunning && (
        <Card className="p-12 text-center">
          <FileCheck className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 font-semibold text-gray-900">No Validation Results</h3>
          <p className="mt-2 text-sm text-gray-600">
            Run a validation check to see if your book meets KDP requirements
          </p>
          <button
            onClick={onRunValidation}
            className="mt-6 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Run First Validation
          </button>
        </Card>
      )}

      {/* Loading State */}
      {isRunning && (
        <Card className="p-12 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
          <h3 className="mt-4 font-semibold text-gray-900">Running Validation...</h3>
          <p className="mt-2 text-sm text-gray-600">
            Checking print specs, ebook format, cover, and compliance
          </p>
        </Card>
      )}
    </div>
  );
}
