"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { BlurbEditor } from "@/modules/product-page/components/BlurbEditor";
import { ABTestPanel } from "@/modules/product-page/components/ABTestPanel";

export default function BlurbOptimizationPage() {
  const [activeTab, setActiveTab] = useState<"editor" | "ab-test">("editor");
  const [bookId] = useState<string | undefined>(undefined);

  const tabs = [
    { key: "editor" as const, label: "Blurb Editor" },
    { key: "ab-test" as const, label: "A/B Testing" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Blurb Optimization</h1>
        <p className="text-gray-500 mt-1">
          Generate, test, and optimize your book blurb for maximum conversion.
        </p>
      </div>

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "pb-2 text-sm font-medium border-b-2 -mb-px",
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Blurb editor tab */}
      {activeTab === "editor" && <BlurbEditor />}

      {/* A/B testing tab */}
      {activeTab === "ab-test" && <ABTestPanel bookId={bookId} />}
    </div>
  );
}
