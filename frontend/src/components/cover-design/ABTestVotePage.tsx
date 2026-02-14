"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import {
  useCompetitorAlerts,
  useAlertHistory,
  useDeleteAlert,
  useUpdateAlert,
} from "@/modules/competitors/hooks";
import type { CompetitorAlert } from "@/modules/competitors/hooks";
import { CreateAlertModal } from "./CreateAlertModal";
import { AlertHistory } from "./AlertHistory";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Bell, Plus, Pencil, X } from "lucide-react";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AlertsPanel() {
  const t = useTranslations("competitors");

  // ---- data hooks ----
  const { data: alerts = [], isLoading: alertsLoading } = useCompetitorAlerts();
  const { data: historyData, isLoading: historyLoading } = useAlertHistory();
  const deleteMutation = useDeleteAlert();
  const updateMutation = useUpdateAlert();

  // ---- local state ----
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState<CompetitorAlert | null>(null);

  // ---- handlers ----
  function handleEdit(alert: CompetitorAlert) {
    setEditingAlert(alert);
    setShowCreateModal(true);
  }

  function handleDelete(alertId: string) {
    deleteMutation.mutate(alertId);
  }

  function handleToggleActive(alert: CompetitorAlert) {
    updateMutation.mutate({
      id: alert.id,
      updates: { active: !alert.active },
    });
  }

  function handleCloseModal() {
    setShowCreateModal(false);
    setEditingAlert(null);
  }

  const activeAlerts = alerts.filter((a) => a.active !== false);
  const historyEvents = historyData?.events ?? [];

  return (
    <div className="space-y-8">
      {/* ---- Header ---- */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">{t("alerts.title")}</h2>
          <p className="text-sm text-muted-foreground">{t("alerts.subtitle")}</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("alerts.createAlert")}
        </Button>
      </div>

      {/* ---- Active Alerts ---- */}
      <section className="space-y-3">
        <h3 className="text-sm font-semibold">
          {t("alerts.activeAlerts")}
          {alerts.length > 0 && (
            <span className="ml-2 text-muted-foreground font-normal">
              {t("alerts.activeCount", { count: activeAlerts.length, total: alerts.length })}
            </span>
          )}
        </h3>

        {alertsLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
            {t("alerts.noAlerts")}
          </div>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="rounded-lg border bg-card p-4 transition-colors hover:bg-accent/50"
              >
                {/* Row 1: icon + name + status badge + actions */}
                <div className="flex items-center gap-3">
                  <Bell className="h-4 w-4 flex-shrink-0 text-muted-foreground" />

                  <span className="font-medium text-sm truncate">
                    {alert.name ?? alert.title}
                  </span>

                  <Badge
                    variant="outline"
                    className={
                      alert.active !== false
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                    }
                    onClick={() => handleToggleActive(alert)}
                    role="button"
                  >
                    {alert.active !== false
                      ? t("alerts.active")
                      : t("alerts.paused")}
                  </Badge>

                  <div className="ml-auto flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(alert)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      <span className="sr-only">{t("alerts.edit")}</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDelete(alert.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <X className="h-3.5 w-3.5" />
                      <span className="sr-only">{t("alerts.delete")}</span>
                    </Button>
                  </div>
                </div>

                {/* Row 2: description */}
                {alert.description && (
                  <p className="mt-1.5 text-sm text-muted-foreground pl-7">
                    {alert.description}
                  </p>
                )}

                {/* Row 3: delivery channels + frequency */}
                <div className="mt-2 flex flex-wrap items-center gap-2 pl-7">
                  {alert.delivery_channels?.map((channel) => (
                    <Badge key={channel} variant="secondary" className="text-xs capitalize">
                      {channel}
                    </Badge>
                  ))}

                  {alert.check_frequency && (
                    <span className="text-xs text-muted-foreground">
                      {t("alerts.checks")}: {alert.check_frequency}
                    </span>
                  )}

                  {alert.last_triggered_at && (
                    <span className="text-xs text-muted-foreground">
                      {t("alerts.triggers")}:{" "}
                      {new Date(alert.last_triggered_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ---- Alert History ---- */}
      <section className="space-y-3">
        {historyLoading ? (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        ) : (
          <AlertHistory events={historyEvents} />
        )}
      </section>

      {/* ---- Create / Edit Modal ---- */}
      <CreateAlertModal
        open={showCreateModal}
        onClose={handleCloseModal}
        editAlert={editingAlert}
      />
    </div>
  );
}
