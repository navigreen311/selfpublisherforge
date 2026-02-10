"use client";

import { useState } from "react";
import {
  useCompetitors,
  useTrackCompetitor,
  useCompetitorDetail,
} from "@/modules/market/hooks";
import { CompetitorChart } from "@/modules/market/components";

export default function CompetitorsPage() {
  const [asinInput, setAsinInput] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: competitors = [], isLoading } = useCompetitors();
  const trackMutation = useTrackCompetitor();
  const { data: selectedCompetitor } = useCompetitorDetail(selectedId ?? "");

  const handleTrack = () => {
    const asin = asinInput.trim().toUpperCase();
    if (!/^B[0-9A-Z]{9}$/.test(asin)) return;
    trackMutation.mutate({ asin });
    setAsinInput("");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div role="region" aria-label="Page header">
        <h1 className="text-2xl font-bold">Competitor Tracking</h1>
        <p className="text-muted-foreground mt-1">
          Track competitor books and monitor their BSR, pricing, and review trends
        </p>
      </div>

      {/* Add competitor */}
      <div role="region" aria-label="Add competitor" className="flex gap-3">
        <label htmlFor="asin-input" className="sr-only">
          Amazon ASIN
        </label>
        <input
          id="asin-input"
          type="text"
          placeholder="Enter Amazon ASIN (e.g., B0XXXXXXXXX)..."
          value={asinInput}
          onChange={(e) => setAsinInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleTrack()}
          aria-label="Enter Amazon ASIN to track a competitor book"
          className="flex-1 max-w-md px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <button
          onClick={handleTrack}
          disabled={trackMutation.isPending || !asinInput.trim()}
          aria-label={trackMutation.isPending ? "Tracking competitor in progress" : "Track competitor by ASIN"}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {trackMutation.isPending ? "Tracking..." : "Track Competitor"}
        </button>
      </div>

      {/* Status messages - live region for dynamic updates */}
      <div aria-live="polite" aria-atomic="true">
        {trackMutation.isError && (
          <div role="alert" className="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
            Failed to track competitor. Please check the ASIN and try again.
          </div>
        )}

        {trackMutation.isSuccess && (
          <div role="status" className="border border-green-200 rounded-lg bg-green-50 p-4 text-sm text-green-700">
            Successfully started tracking {trackMutation.data.title}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Competitor list */}
        <div className="lg:col-span-1" role="region" aria-label="Tracked competitors list">
          <div className="border rounded-lg bg-card">
            <div className="p-4 border-b">
              <h3 className="font-semibold text-sm" id="tracked-books-heading">
                Tracked Books ({competitors.length})
              </h3>
            </div>
            <div
              className="max-h-[600px] overflow-y-auto"
              role="list"
              aria-labelledby="tracked-books-heading"
              aria-live="polite"
            >
              {isLoading ? (
                <div className="p-4 text-center text-muted-foreground text-sm" role="status">
                  Loading...
                </div>
              ) : competitors.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground text-sm" role="listitem">
                  No competitors tracked yet. Add an ASIN above to start.
                </div>
              ) : (
                competitors.map((comp) => (
                  <button
                    key={comp.id}
                    onClick={() => setSelectedId(comp.id)}
                    role="listitem"
                    aria-label={`View details for ${comp.title} by ${comp.author}`}
                    aria-pressed={selectedId === comp.id}
                    className={`w-full text-left p-4 border-b last:border-b-0 hover:bg-muted/50 transition-colors ${
                      selectedId === comp.id ? "bg-primary/5" : ""
                    }`}
                  >
                    <div className="font-medium text-sm truncate">{comp.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {comp.author} | ASIN: {comp.asin}
                    </div>
                    <div className="flex gap-4 mt-2 text-xs">
                      <span>
                        BSR: <strong>{comp.bsr?.toLocaleString() ?? "N/A"}</strong>
                      </span>
                      <span>
                        Price: <strong>${comp.price?.toFixed(2) ?? "N/A"}</strong>
                      </span>
                      <span>
                        Reviews: <strong>{comp.reviews_count.toLocaleString()}</strong>
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Competitor detail / chart */}
        <div className="lg:col-span-2" role="region" aria-label="Competitor details" aria-live="polite">
          {selectedCompetitor ? (
            <div className="space-y-4">
              {/* Stats */}
              <div className="border rounded-lg bg-card p-6" role="region" aria-label={`Statistics for ${selectedCompetitor.title}`}>
                <h3 className="font-semibold text-lg mb-1">
                  {selectedCompetitor.title}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  By {selectedCompetitor.author} | ASIN: {selectedCompetitor.asin}
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" role="list" aria-label="Competitor metrics">
                  <div className="p-3 rounded-md bg-muted/50 text-center" role="listitem">
                    <div className="text-lg font-semibold" aria-label={`Current BSR: ${selectedCompetitor.bsr?.toLocaleString() ?? "N/A"}`}>
                      {selectedCompetitor.bsr?.toLocaleString() ?? "N/A"}
                    </div>
                    <div className="text-xs text-muted-foreground">Current BSR</div>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50 text-center" role="listitem">
                    <div className="text-lg font-semibold" aria-label={`Price: $${selectedCompetitor.price?.toFixed(2) ?? "N/A"}`}>
                      ${selectedCompetitor.price?.toFixed(2) ?? "N/A"}
                    </div>
                    <div className="text-xs text-muted-foreground">Price</div>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50 text-center" role="listitem">
                    <div className="text-lg font-semibold" aria-label={`Reviews: ${selectedCompetitor.reviews_count.toLocaleString()}`}>
                      {selectedCompetitor.reviews_count.toLocaleString()}
                    </div>
                    <div className="text-xs text-muted-foreground">Reviews</div>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50 text-center" role="listitem">
                    <div className="text-lg font-semibold" aria-label={`Rating: ${selectedCompetitor.rating?.toFixed(1) ?? "N/A"} out of 5`}>
                      {selectedCompetitor.rating?.toFixed(1) ?? "N/A"}
                    </div>
                    <div className="text-xs text-muted-foreground">Rating</div>
                  </div>
                </div>
              </div>

              {/* BSR Chart */}
              <div role="region" aria-label={`BSR history chart for ${selectedCompetitor.title}`}>
                <CompetitorChart competitor={selectedCompetitor} />
              </div>

              {/* Tracking info */}
              <div className="text-xs text-muted-foreground" aria-label="Tracking information">
                Tracked since{" "}
                {new Date(selectedCompetitor.tracked_since).toLocaleDateString()} |{" "}
                {selectedCompetitor.bsr_history.length} data points
              </div>
            </div>
          ) : (
            <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground" role="status">
              Select a competitor from the list to view details and BSR history
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
