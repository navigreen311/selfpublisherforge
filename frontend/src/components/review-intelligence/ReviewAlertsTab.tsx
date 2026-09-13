"use client";

import { Bell, Mail, AlertTriangle, Plus, Pencil, Trash2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslations } from "@/hooks/use-translations";
import type { ReviewAlert, AlertNotification } from "@/modules/reviews/hooks";

// ---------------------------------------------------------------------------
// Alert type display labels map
// ---------------------------------------------------------------------------

const ALERT_TYPE_KEYS: Record<string, string> = {
  new_review: "alerts.alertTypes.new_review",
  negative_review: "alerts.alertTypes.negative_review",
  rating_drop: "alerts.alertTypes.rating_drop",
  velocity_change: "alerts.alertTypes.velocity_change",
  fake_review: "alerts.alertTypes.fake_review",
  weekly_summary: "alerts.alertTypes.weekly_summary",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return a human-readable relative time string for a given ISO date. */
function relativeTime(
  iso: string,
  t: (key: string, values?: any) => string,
): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffMs = now - then;
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMinutes < 1) return t("feed.justNow");
  if (diffHours < 1) return t("feed.hoursAgo", { count: 0 });
  if (diffHours < 24) return t("feed.hoursAgo", { count: diffHours });
  return t("feed.daysAgo", { count: diffDays });
}

/** Whether the alert type is considered "negative" for visual emphasis. */
function isNegativeAlertType(alertType: string): boolean {
  return ["negative_review", "rating_drop", "fake_review"].includes(alertType);
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ReviewAlertsTabProps {
  alerts: ReviewAlert[];
  notifications: AlertNotification[];
  onCreateAlert: () => void;
  onEditAlert: (alertId: string) => void;
  onDeleteAlert: (alertId: string) => void;
  onAcknowledge: (alertId: string) => void;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function AlertsSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-9 w-32" />
      </div>

      {/* Active Alerts skeleton */}
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-28" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-5 w-14 rounded-full" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-8 w-14" />
                  <Skeleton className="h-8 w-8" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Notifications skeleton */}
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border p-3">
                <Skeleton className="mt-0.5 h-4 w-4 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ReviewAlertsTab({
  alerts,
  notifications,
  onCreateAlert,
  onEditAlert,
  onDeleteAlert,
  onAcknowledge,
  isLoading,
}: ReviewAlertsTabProps) {
  const t = useTranslations("reviews");

  if (isLoading) {
    return <AlertsSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("alerts.title")}</h2>
        <Button size="sm" onClick={onCreateAlert}>
          <Plus className="mr-1.5 h-4 w-4" />
          {t("alerts.createAlert")}
        </Button>
      </div>

      {/* Active Alerts */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">{t("alerts.activeAlerts")}</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              {t("alerts.noAlerts")}
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => {
                const typeKey = ALERT_TYPE_KEYS[alert.alert_type] ?? alert.alert_type;
                const isActive = alert.active !== false;
                const bookScope = alert.book_id
                  ? alert.title
                  : t("alerts.allBooks");

                return (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
                  >
                    {/* Left: icon, name, scope, status */}
                    <div className="flex items-center gap-3 min-w-0">
                      <Bell className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                      <div className="flex flex-wrap items-center gap-2 min-w-0">
                        <span className="text-sm font-medium truncate">
                          {t(typeKey)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {bookScope}
                        </span>
                        <Badge
                          variant={isActive ? "default" : "secondary"}
                          className={
                            isActive
                              ? "bg-green-100 text-green-700 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-gray-100 text-gray-500 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-400"
                          }
                        >
                          {isActive ? t("alerts.active") : t("alerts.paused")}
                        </Badge>
                      </div>
                    </div>

                    {/* Right: edit & delete buttons */}
                    <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditAlert(alert.id)}
                        className="h-8 px-2"
                      >
                        <Pencil className="mr-1 h-3.5 w-3.5" />
                        <span className="text-xs">{t("alerts.edit")}</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onDeleteAlert(alert.id)}
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Notifications */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {t("alerts.recentNotifications")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {notifications.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              {t("alerts.noNotifications")}
            </div>
          ) : (
            <div className="space-y-1.5">
              {notifications.map((notification) => {
                const isNegative = isNegativeAlertType(notification.alert_type);

                return (
                  <div
                    key={notification.id}
                    className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                      notification.read
                        ? "bg-card"
                        : "border-l-2 border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20"
                    }`}
                  >
                    <Mail className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2">
                        <p className="text-sm leading-snug flex-1">
                          {notification.message}
                        </p>
                        {isNegative && (
                          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                        )}
                      </div>
                      {notification.book_title && (
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {notification.book_title}
                        </p>
                      )}
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {relativeTime(notification.created_at, t)}
                      </p>
                    </div>

                    {!notification.read && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onAcknowledge(notification.id)}
                        className="h-7 px-2 text-xs flex-shrink-0"
                      >
                        {t("alerts.acknowledge")}
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
