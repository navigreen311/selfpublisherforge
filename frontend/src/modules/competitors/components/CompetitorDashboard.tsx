"use client";

import { useState, useCallback } from "react";
import { AddCompetitor } from "@/components/competitor-finder/AddCompetitor";
import { CompetitorGrid } from "@/components/competitor-finder/CompetitorGrid";
import { CompetitorDetailPanel } from "@/components/competitor-finder/CompetitorDetailPanel";
import { GapAnalysisTab } from "@/components/competitor-finder/GapAnalysisTab";
import { CompareBooks } from "@/components/competitor-finder/CompareBooks";
import { AlertsPanel } from "@/components/competitor-finder/AlertsPanel";
import { useTrackedCompetitors, useCompetitorAlerts, useRemoveCompetitor } from "../hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TabValue = "tracked" | "gap-analysis" | "compare" | "alerts";
type ViewMode = "grid" | "table";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompetitorDashboard() {
  const t = useTranslations("competitors");

  // ---- State ----
  const [activeTab, setActiveTab] = useState<TabValue>("tracked");
  const [selectedCompetitorId, setSelectedCompetitorId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  // ---- Data ----
  const {
    data: trackedResponse,
    isLoading: isTrackedLoading,
  } = useTrackedCompetitors();

  const {
    data: alerts = [],
    isLoading: isAlertsLoading,
  } = useCompetitorAlerts(false, 50);

  const removeCompetitorMutation = useRemoveCompetitor();

  const competitors = trackedResponse?.competitors ?? [];
  const trackedCount = trackedResponse?.total ?? competitors.length;
  const unreadAlertCount = alerts.filter((a) => !a.read).length;

  // ---- Handlers ----

  const handleViewDetails = useCallback((id: string) => {
    setSelectedCompetitorId(id);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedCompetitorId(null);
  }, []);

  const handleRemoveCompetitor = useCallback(
    (id: string) => {
      removeCompetitorMutation.mutate(id);
    },
    [removeCompetitorMutation],
  );

  // ---- Render ----

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      {/* Add competitor */}
      <AddCompetitor trackedCount={trackedCount} />

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as TabValue)}
      >
        <TabsList>
          {/* Tab 1: Tracked Books */}
          <TabsTrigger value="tracked">
            {t("tabs.analyses")}
            {trackedCount > 0 && (
              <Badge variant="outline" className="ml-2 bg-blue-50 text-blue-700">
                {trackedCount}
              </Badge>
            )}
          </TabsTrigger>

          {/* Tab 2: Gap Analysis */}
          <TabsTrigger value="gap-analysis">
            {t("tabs.gapAnalysis")}
          </TabsTrigger>

          {/* Tab 3: Compare */}
          <TabsTrigger value="compare">
            {t("tabs.compare")}
          </TabsTrigger>

          {/* Tab 4: Alerts */}
          <TabsTrigger value="alerts">
            {t("tabs.alerts")}
            {unreadAlertCount > 0 && (
              <Badge variant="outline" className="ml-2 bg-red-50 text-red-700">
                {unreadAlertCount}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* ---- Tracked Books tab ---- */}
        <TabsContent value="tracked" className="space-y-4">
          {isTrackedLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : (
            <CompetitorGrid
              competitors={competitors}
              onViewDetails={handleViewDetails}
              onRemove={handleRemoveCompetitor}
              view={viewMode}
            />
          )}
        </TabsContent>

        {/* ---- Gap Analysis tab ---- */}
        <TabsContent value="gap-analysis" className="space-y-4">
          <GapAnalysisTab trackedCompetitors={competitors} />
        </TabsContent>

        {/* ---- Compare tab ---- */}
        <TabsContent value="compare" className="space-y-4">
          <CompareBooks trackedCompetitors={competitors} />
        </TabsContent>

        {/* ---- Alerts tab ---- */}
        <TabsContent value="alerts" className="space-y-4">
          {isAlertsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : (
            <AlertsPanel />
          )}
        </TabsContent>
      </Tabs>

      {/* Detail panel overlay */}
      {selectedCompetitorId && (
        <CompetitorDetailPanel
          competitorId={selectedCompetitorId}
          onClose={handleCloseDetail}
        />
      )}
    </div>
  );
}
