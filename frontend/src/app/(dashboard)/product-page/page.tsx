"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAnalyzeListing } from "@/modules/product-page/hooks";
import { ListingScoreCard } from "@/modules/product-page/components/ListingScoreCard";
import { MobilePreview } from "@/modules/product-page/components/MobilePreview";

export default function ProductPageLab() {
  const [asinInput, setAsinInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [activeTab, setActiveTab] = useState<"analyze" | "mobile">("analyze");

  const analyzeMutation = useAnalyzeListing();

  const handleAnalyze = () => {
    const asinMatch = asinInput.match(/^[A-Z0-9]{10}$/i);
    analyzeMutation.mutate({
      asin: asinMatch ? asinInput.toUpperCase() : undefined,
      url: !asinMatch && urlInput ? urlInput : undefined,
    });
  };

  const tabs = [
    { key: "analyze" as const, label: "Listing Analysis" },
    { key: "mobile" as const, label: "Mobile Check" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Product Page Conversion Lab</h1>
        <p className="text-muted-foreground mt-1">
          Analyze and optimize your Amazon book listings for maximum conversion.
        </p>
      </div>

      {/* Tab navigation */}
      <div className="border-b border">
        <nav className="flex gap-4" role="tablist" aria-label="Product page tools">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              id={`tab-${tab.key}`}
              aria-selected={activeTab === tab.key}
              aria-controls={`tabpanel-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "pb-2 text-sm font-medium border-b-2 -mb-px",
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Listing analysis tab */}
      {activeTab === "analyze" && (
        <div
          role="tabpanel"
          id="tabpanel-analyze"
          aria-labelledby="tab-analyze"
          className="space-y-6"
        >
          {/* Input */}
          <div className="rounded-lg border bg-card p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Analyze a Listing</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="asin-input" className="block text-sm font-medium text-foreground mb-1">
                  ASIN
                </label>
                <input
                  id="asin-input"
                  type="text"
                  value={asinInput}
                  onChange={(e) => setAsinInput(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  placeholder="e.g., B09V2KKG1D"
                  maxLength={10}
                />
              </div>
              <div>
                <label htmlFor="url-input" className="block text-sm font-medium text-foreground mb-1">
                  or Amazon URL
                </label>
                <input
                  id="url-input"
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  placeholder="https://www.amazon.com/dp/..."
                />
              </div>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={(!asinInput && !urlInput) || analyzeMutation.isPending}
              aria-label={analyzeMutation.isPending ? "Analyzing listing" : "Analyze listing"}
              className={cn(
                "mt-4 rounded-md px-4 py-2 text-sm font-medium text-white",
                !asinInput && !urlInput
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-700"
              )}
            >
              {analyzeMutation.isPending ? "Analyzing..." : "Analyze Listing"}
            </button>
          </div>

          {/* Results */}
          {analyzeMutation.data && (
            <ListingScoreCard analysis={analyzeMutation.data} />
          )}

          {analyzeMutation.isError && (
            <div role="alert" className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
              Failed to analyze listing. Please check your ASIN or URL and try again.
            </div>
          )}
        </div>
      )}

      {/* Mobile check tab */}
      {activeTab === "mobile" && (
        <div
          role="tabpanel"
          id="tabpanel-mobile"
          aria-labelledby="tab-mobile"
        >
          <MobilePreview />
        </div>
      )}
    </div>
  );
}
