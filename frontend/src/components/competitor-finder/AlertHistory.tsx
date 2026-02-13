"use client";

import type { AlertEvent } from "@/modules/competitors/hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Mail } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return a human-readable relative time string for a given ISO date. */
function relativeTime(
  iso: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  t: (key: string, values?: any) => string,
): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffMs = now - then;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return t("alerts.timeAgo.hoursAgo", { count: 0 });
  if (diffHours < 24) return t("alerts.timeAgo.hoursAgo", { count: diffHours });
  if (diffDays === 1) return t("alerts.timeAgo.yesterday");
  return t("alerts.timeAgo.daysAgo", { count: diffDays });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface AlertHistoryProps {
  events: AlertEvent[];
}

export function AlertHistory({ events }: AlertHistoryProps) {
  const t = useTranslations("competitors");

  if (events.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
        {t("alerts.noHistory")}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{t("alerts.alertHistory")}</h3>

      <div className="space-y-1.5">
        {events.map((event) => (
          <div
            key={event.id}
            className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
              event.read
                ? "bg-card"
                : "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950"
            }`}
          >
            <Mail className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />

            <div className="flex-1 min-w-0">
              <p className="text-sm leading-snug">
                {event.message ?? JSON.stringify(event.event_data)}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {relativeTime(event.created_at, t)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
