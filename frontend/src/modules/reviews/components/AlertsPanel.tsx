"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertSeverity, AlertType, type ReviewAlert } from "../types";

interface AlertsPanelProps {
  alerts: ReviewAlert[];
  onAcknowledge?: (alertId: string) => void;
  isAcknowledging?: boolean;
}

export function AlertsPanel({
  alerts,
  onAcknowledge,
  isAcknowledging = false,
}: AlertsPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Alerts</h3>
        <div className="text-center py-8">
          <div className="text-5xl mb-2">✓</div>
          <p className="text-gray-500">No active alerts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Review Alerts</h3>
        <Badge variant="destructive">{alerts.length}</Badge>
      </div>

      <div className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 rounded-lg border-l-4 ${getSeverityBorderColor(alert.severity)} bg-gray-50`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={getSeverityColor(alert.severity)}>
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <Badge variant="outline">{getAlertTypeLabel(alert.alert_type)}</Badge>
                </div>
                <h4 className="font-semibold text-gray-900 mb-1">{alert.title}</h4>
                <p className="text-sm text-gray-600">{alert.description}</p>
                {alert.data && Object.keys(alert.data).length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    {Object.entries(alert.data).map(([key, value]) => (
                      <div key={key}>
                        <span className="font-medium">{formatKey(key)}:</span>{" "}
                        {formatValue(value)}
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(alert.created_at).toLocaleString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {!alert.is_acknowledged && onAcknowledge && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onAcknowledge(alert.id)}
                  disabled={isAcknowledging}
                  className="ml-2"
                >
                  Acknowledge
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getSeverityColor(severity: AlertSeverity): string {
  switch (severity) {
    case AlertSeverity.CRITICAL:
      return "bg-red-600 text-white border-red-700";
    case AlertSeverity.HIGH:
      return "bg-orange-500 text-white border-orange-600";
    case AlertSeverity.MEDIUM:
      return "bg-yellow-500 text-white border-yellow-600";
    case AlertSeverity.LOW:
      return "bg-blue-500 text-white border-blue-600";
    default:
      return "bg-gray-500 text-white border-gray-600";
  }
}

function getSeverityBorderColor(severity: AlertSeverity): string {
  switch (severity) {
    case AlertSeverity.CRITICAL:
      return "border-red-600";
    case AlertSeverity.HIGH:
      return "border-orange-500";
    case AlertSeverity.MEDIUM:
      return "border-yellow-500";
    case AlertSeverity.LOW:
      return "border-blue-500";
    default:
      return "border-gray-400";
  }
}

function getAlertTypeLabel(type: AlertType): string {
  switch (type) {
    case AlertType.NEGATIVE_SPIKE:
      return "Negative Spike";
    case AlertType.VELOCITY_DROP:
      return "Velocity Drop";
    case AlertType.RATING_DECLINE:
      return "Rating Decline";
    case AlertType.COMPETITOR_SURGE:
      return "Competitor Surge";
    default:
      return type;
  }
}

function formatKey(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}
