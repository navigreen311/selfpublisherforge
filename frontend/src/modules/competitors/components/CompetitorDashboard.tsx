"use client";

import { useState } from "react";
import { CompetitorTable } from "./CompetitorTable";
import { GapAnalysisComponent } from "./GapAnalysis";
import { OpportunityCard } from "./OpportunityCard";
import { CompetitorCompare } from "./CompetitorCompare";
import {
  useCompetitorAnalyses,
  useGapAnalysis,
  useAnalyzeCompetitor,
  useCompetitorAlerts,
} from "../hooks";
import type { CompetitorAnalysisDetail, GapAnalysis } from "../types";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";

export function CompetitorDashboard() {
  const [selectedTab, setSelectedTab] = useState<"analyses" | "gaps" | "compare" | "alerts">(
    "analyses"
  );
  const [selectedAnalyses, setSelectedAnalyses] = useState<CompetitorAnalysisDetail[]>([]);
  const [gapNiche, setGapNiche] = useState("");
  const [gapInput, setGapInput] = useState("");
  const [currentGapAnalysis, setCurrentGapAnalysis] = useState<GapAnalysis | null>(null);

  const { data: analyses = [], isLoading: analysesLoading } = useCompetitorAnalyses();
  const { data: alerts = [], isLoading: alertsLoading } = useCompetitorAlerts(false, 20);
  const gapAnalysisMutation = useGapAnalysis();
  const analyzeCompetitorMutation = useAnalyzeCompetitor();

  const handleRunGapAnalysis = () => {
    if (!gapInput.trim()) return;
    setGapNiche(gapInput.trim());
    gapAnalysisMutation.mutate(
      {
        request: {
          niche: gapInput.trim(),
          max_books: 20,
        },
      },
      {
        onSuccess: (data) => {
          setCurrentGapAnalysis(data);
        },
      }
    );
  };

  const handleToggleSelection = (analysis: CompetitorAnalysisDetail) => {
    setSelectedAnalyses((prev) => {
      const exists = prev.find((a) => a.id === analysis.id);
      if (exists) {
        return prev.filter((a) => a.id !== analysis.id);
      }
      if (prev.length >= 3) {
        return [...prev.slice(1), analysis];
      }
      return [...prev, analysis];
    });
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold">Competitor Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Analyze competitors, discover gaps, and identify opportunities
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as typeof selectedTab)}>
        <TabsList>
          <TabsTrigger value="analyses">
            Analyses
            {analyses.length > 0 && (
              <Badge variant="outline" className="ml-2 bg-blue-50 text-blue-700">
                {analyses.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="gaps">Gap Analysis</TabsTrigger>
          <TabsTrigger value="compare">
            Compare
            {selectedAnalyses.length > 0 && (
              <Badge variant="outline" className="ml-2 bg-purple-50 text-purple-700">
                {selectedAnalyses.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts
            {alerts.filter((a) => !a.read).length > 0 && (
              <Badge variant="outline" className="ml-2 bg-red-50 text-red-700">
                {alerts.filter((a) => !a.read).length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Analyses Tab */}
        <TabsContent value="analyses" className="space-y-4">
          {analysesLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : (
            <>
              <CompetitorTable
                analyses={analyses as CompetitorAnalysisDetail[]}
                isLoading={analysesLoading}
                onSelectCompetitor={handleToggleSelection}
              />

              {/* Selected analysis details */}
              {selectedAnalyses.length === 1 && selectedAnalyses[0].opportunity && (
                <OpportunityCard opportunity={selectedAnalyses[0].opportunity} />
              )}
            </>
          )}
        </TabsContent>

        {/* Gap Analysis Tab */}
        <TabsContent value="gaps" className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter a niche to analyze gaps (e.g., 'productivity for remote workers')..."
              value={gapInput}
              onChange={(e) => setGapInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRunGapAnalysis()}
              className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleRunGapAnalysis}
              disabled={gapAnalysisMutation.isPending || !gapInput.trim()}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {gapAnalysisMutation.isPending ? "Analyzing..." : "Analyze Gaps"}
            </button>
          </div>

          {gapAnalysisMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to run gap analysis. Please try again.
              </AlertDescription>
            </Alert>
          )}

          {currentGapAnalysis && <GapAnalysisComponent analysis={currentGapAnalysis} />}
        </TabsContent>

        {/* Compare Tab */}
        <TabsContent value="compare" className="space-y-4">
          <div className="text-sm text-muted-foreground mb-4">
            Click on competitors in the Analyses tab to select them for comparison (max 3)
          </div>
          <CompetitorCompare analyses={selectedAnalyses} maxCompare={3} />
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          {alertsLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
              No competitor alerts yet
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`border rounded-lg p-4 ${
                    alert.read ? "bg-card" : "bg-blue-50 border-blue-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{alert.title}</span>
                        <AlertSeverityBadge severity={alert.severity} />
                        <AlertTypeBadge type={alert.alert_type} />
                      </div>
                      {alert.description && (
                        <p className="text-sm text-muted-foreground">{alert.description}</p>
                      )}
                      <div className="text-xs text-muted-foreground mt-2">
                        {new Date(alert.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

function AlertSeverityBadge({ severity }: { severity: string }) {
  const config: Record<string, { label: string; className: string }> = {
    info: { label: "Info", className: "bg-blue-100 text-blue-700" },
    warning: { label: "Warning", className: "bg-yellow-100 text-yellow-700" },
    critical: { label: "Critical", className: "bg-red-100 text-red-700" },
  };

  const { label, className } = config[severity] ?? config.info;
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  );
}

function AlertTypeBadge({ type }: { type: string }) {
  const config: Record<string, string> = {
    price_change: "Price Change",
    bsr_shift: "BSR Shift",
    new_book: "New Book",
    review_spike: "Review Spike",
  };

  return (
    <Badge variant="outline" className="bg-gray-100 text-gray-700">
      {config[type] ?? type}
    </Badge>
  );
}
