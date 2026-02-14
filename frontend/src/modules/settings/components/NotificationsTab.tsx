"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useNotificationPrefs, useUpdateNotificationPrefs } from "../hooks";

const NOTIFICATION_EVENTS = [
  { id: "book_published", label: "Book published successfully" },
  { id: "export_completed", label: "Export completed" },
  { id: "ai_task_completed", label: "AI Agent task completed" },
  { id: "new_review", label: "New review received" },
  { id: "bsr_change", label: "BSR change (significant)" },
  { id: "price_change", label: "Price change executed" },
  { id: "arc_review_posted", label: "ARC reviewer posted review" },
  { id: "team_member_joined", label: "Team member joined" },
  { id: "weekly_digest", label: "Weekly performance digest" },
  { id: "monthly_analytics", label: "Monthly analytics report" },
  { id: "budget_warning", label: "Budget/usage warnings" },
] as const;

export function NotificationsTab() {
  const { data: notificationPrefs, isLoading } = useNotificationPrefs();
  const updatePrefs = useUpdateNotificationPrefs();

  // Local state for form values
  const [preferences, setPreferences] = useState<
    Record<string, { email: boolean; in_app: boolean }>
  >({});
  const [quietHoursStart, setQuietHoursStart] = useState("");
  const [quietHoursEnd, setQuietHoursEnd] = useState("");
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize form values from API data
  useEffect(() => {
    if (notificationPrefs) {
      setPreferences(notificationPrefs.preferences || {});
      setQuietHoursStart(notificationPrefs.quiet_hours_start || "");
      setQuietHoursEnd(notificationPrefs.quiet_hours_end || "");
    }
  }, [notificationPrefs]);

  // Handle checkbox changes
  const handleToggle = (eventId: string, channel: "email" | "in_app") => {
    setPreferences((prev) => ({
      ...prev,
      [eventId]: {
        email: prev[eventId]?.email || false,
        in_app: prev[eventId]?.in_app || false,
        [channel]: !(prev[eventId]?.[channel] || false),
      },
    }));
    setHasChanges(true);
  };

  // Handle save
  const handleSave = async () => {
    try {
      await updatePrefs.mutateAsync({
        preferences,
        quiet_hours_start: quietHoursStart || undefined,
        quiet_hours_end: quietHoursEnd || undefined,
      });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save notification preferences:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-200 rounded w-1/3" />
        <div className="h-96 bg-gray-100 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold">Notification Preferences</h2>
        <p className="text-sm text-gray-500">
          Configure how you want to receive notifications about your publishing activities.
        </p>
      </div>

      {/* Notification Events Table */}
      <Card>
        <CardHeader>
          <CardTitle>Event Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Event
                  </th>
                  <th className="text-center py-3 px-4 font-medium text-gray-700">
                    Email
                  </th>
                  <th className="text-center py-3 px-4 font-medium text-gray-700">
                    In-App
                  </th>
                </tr>
              </thead>
              <tbody>
                {NOTIFICATION_EVENTS.map((event) => {
                  const pref = preferences[event.id] || {
                    email: false,
                    in_app: false,
                  };
                  return (
                    <tr key={event.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {event.label}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                          <Checkbox
                            checked={pref.email}
                            onCheckedChange={() =>
                              handleToggle(event.id, "email")
                            }
                            aria-label={`Email notification for ${event.label}`}
                          />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                          <Checkbox
                            checked={pref.in_app}
                            onCheckedChange={() =>
                              handleToggle(event.id, "in_app")
                            }
                            aria-label={`In-app notification for ${event.label}`}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quiet Hours */}
      <Card>
        <CardHeader>
          <CardTitle>Quiet Hours</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-600">
            Don't send email notifications during these hours (times in your local timezone).
          </p>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Label htmlFor="quiet-hours-start" className="whitespace-nowrap">
                Start time:
              </Label>
              <Input
                id="quiet-hours-start"
                type="time"
                value={quietHoursStart}
                onChange={(e) => {
                  setQuietHoursStart(e.target.value);
                  setHasChanges(true);
                }}
                className="w-40"
              />
            </div>
            <div className="flex items-center gap-2 flex-1">
              <Label htmlFor="quiet-hours-end" className="whitespace-nowrap">
                End time:
              </Label>
              <Input
                id="quiet-hours-end"
                type="time"
                value={quietHoursEnd}
                onChange={(e) => {
                  setQuietHoursEnd(e.target.value);
                  setHasChanges(true);
                }}
                className="w-40"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={!hasChanges || updatePrefs.isPending}
        >
          {updatePrefs.isPending ? "Saving..." : "Save Preferences"}
        </Button>
      </div>
    </div>
  );
}
