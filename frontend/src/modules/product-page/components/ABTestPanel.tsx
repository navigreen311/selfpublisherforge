"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useCreateABTest, useABTestResults } from "../hooks";
import type { ABTestResponse } from "../hooks";

interface ABTestPanelProps {
  bookId?: string;
  variantA?: string;
  variantB?: string;
  className?: string;
}

function TestResultDisplay({ test }: { test: ABTestResponse }) {
  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-green-100 text-green-700",
  };

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-md font-semibold">{test.name}</h4>
        <span
          className={cn(
            "px-2 py-1 rounded text-xs font-medium",
            statusColors[test.status] || "bg-gray-100 text-gray-700"
          )}
        >
          {test.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Variant A */}
        <div
          className={cn(
            "rounded-md border p-4",
            test.winner === "A" ? "border-green-400 bg-green-50" : "border-gray-200"
          )}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">Variant A</span>
            {test.winner === "A" && (
              <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded">
                Winner
              </span>
            )}
          </div>
          <p className="text-xs text-gray-600 whitespace-pre-wrap line-clamp-4 mb-3">
            {test.variant_a.content}
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Impressions:</span>{" "}
              <span className="font-medium">{test.variant_a.impressions}</span>
            </div>
            <div>
              <span className="text-gray-500">Clicks:</span>{" "}
              <span className="font-medium">{test.variant_a.clicks}</span>
            </div>
            <div>
              <span className="text-gray-500">CTR:</span>{" "}
              <span className="font-medium">{test.variant_a.click_through_rate}%</span>
            </div>
          </div>
        </div>

        {/* Variant B */}
        <div
          className={cn(
            "rounded-md border p-4",
            test.winner === "B" ? "border-green-400 bg-green-50" : "border-gray-200"
          )}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">Variant B</span>
            {test.winner === "B" && (
              <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded">
                Winner
              </span>
            )}
          </div>
          <p className="text-xs text-gray-600 whitespace-pre-wrap line-clamp-4 mb-3">
            {test.variant_b.content}
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Impressions:</span>{" "}
              <span className="font-medium">{test.variant_b.impressions}</span>
            </div>
            <div>
              <span className="text-gray-500">Clicks:</span>{" "}
              <span className="font-medium">{test.variant_b.clicks}</span>
            </div>
            <div>
              <span className="text-gray-500">CTR:</span>{" "}
              <span className="font-medium">{test.variant_b.click_through_rate}%</span>
            </div>
          </div>
        </div>
      </div>

      {test.confidence && (
        <p className="text-xs text-gray-500 mt-3 text-center">
          Statistical confidence: {test.confidence}%
        </p>
      )}
    </div>
  );
}

export function ABTestPanel({
  bookId,
  variantA = "",
  variantB = "",
  className,
}: ABTestPanelProps) {
  const [name, setName] = useState("");
  const [blurbA, setBlurbA] = useState(variantA);
  const [blurbB, setBlurbB] = useState(variantB);
  const [durationDays, setDurationDays] = useState(7);
  const [activeTestId, setActiveTestId] = useState<string>();

  const createMutation = useCreateABTest();
  const testQuery = useABTestResults(activeTestId);

  const handleCreate = () => {
    if (!bookId || !name || blurbA.length < 10 || blurbB.length < 10) return;

    createMutation.mutate(
      {
        book_id: bookId,
        name,
        variant_a: blurbA,
        variant_b: blurbB,
        duration_days: durationDays,
      },
      {
        onSuccess: (data) => {
          setActiveTestId(data.id);
        },
      }
    );
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Create form */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">A/B Test Setup</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Test Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="e.g., Blurb Test Q1 2025"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Variant A
              </label>
              <textarea
                value={blurbA}
                onChange={(e) => setBlurbA(e.target.value)}
                rows={6}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder="First blurb version..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Variant B
              </label>
              <textarea
                value={blurbB}
                onChange={(e) => setBlurbB(e.target.value)}
                rows={6}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder="Second blurb version..."
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duration (days)
              </label>
              <select
                value={durationDays}
                onChange={(e) => setDurationDays(Number(e.target.value))}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {[3, 7, 14, 30, 60, 90].map((d) => (
                  <option key={d} value={d}>
                    {d} days
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1" />

            <button
              onClick={handleCreate}
              disabled={!bookId || !name || blurbA.length < 10 || blurbB.length < 10 || createMutation.isPending}
              className={cn(
                "rounded-md px-4 py-2 text-sm font-medium text-white mt-6",
                !bookId || !name || blurbA.length < 10 || blurbB.length < 10
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-700"
              )}
            >
              {createMutation.isPending ? "Creating..." : "Create A/B Test"}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {testQuery.data && <TestResultDisplay test={testQuery.data} />}

      {createMutation.isError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Failed to create A/B test. Please check your inputs.
        </div>
      )}
    </div>
  );
}
