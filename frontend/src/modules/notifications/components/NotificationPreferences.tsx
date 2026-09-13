"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useNotificationPreferences, useUpdatePreferences } from "../hooks";
import type { NotificationChannel, PreferenceItem } from "../types";

interface PreferenceRow {
  category: string;
  label: string;
  description: string;
}

/**
 * Notification categories with human-readable labels.
 */
const PREFERENCE_CATEGORIES: PreferenceRow[] = [
  {
    category: "ai_complete",
    label: "AI Task Completion",
    description: "Notify when AI agents complete tasks or workflows",
  },
  {
    category: "publish_status",
    label: "Publishing Updates",
    description: "Notify about book publishing status changes",
  },
  {
    category: "team_invite",
    label: "Team Invitations",
    description: "Notify when you're invited to join a team",
  },
  {
    category: "analytics",
    label: "Analytics Reports",
    description: "Notify when new analytics reports are ready",
  },
  {
    category: "marketing",
    label: "Marketing Campaigns",
    description: "Notify about marketing campaign performance",
  },
  {
    category: "system",
    label: "System Updates",
    description: "Important system announcements and updates",
  },
];

const CHANNELS: { value: NotificationChannel; label: string }[] = [
  { value: "email", label: "Email" },
  { value: "in_app", label: "In-App" },
];

/**
 * Notification preferences component.
 * Toggle email/in-app notifications for each category.
 */
export function NotificationPreferences() {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreferences = useUpdatePreferences();

  // Local state for toggles
  const [localPreferences, setLocalPreferences] = useState<
    Map<string, boolean>
  >(new Map());

  // Initialize local state from API data
  useEffect(() => {
    if (preferences) {
      const map = new Map<string, boolean>();
      preferences.forEach((pref) => {
        const key = `${pref.channel}:${pref.category}`;
        map.set(key, pref.enabled);
      });
      setLocalPreferences(map);
    }
  }, [preferences]);

  const getPreferenceKey = (channel: NotificationChannel, category: string) => {
    return `${channel}:${category}`;
  };

  const isEnabled = (channel: NotificationChannel, category: string) => {
    return localPreferences.get(getPreferenceKey(channel, category)) ?? true;
  };

  const handleToggle = (channel: NotificationChannel, category: string) => {
    const key = getPreferenceKey(channel, category);
    const currentValue = localPreferences.get(key) ?? true;
    const newMap = new Map(localPreferences);
    newMap.set(key, !currentValue);
    setLocalPreferences(newMap);
  };

  const handleSave = () => {
    const updates: PreferenceItem[] = [];

    PREFERENCE_CATEGORIES.forEach((row) => {
      CHANNELS.forEach((channel) => {
        const key = getPreferenceKey(channel.value, row.category);
        const enabled = localPreferences.get(key) ?? true;
        updates.push({
          channel: channel.value,
          category: row.category,
          enabled,
        });
      });
    });

    updatePreferences.mutate({ preferences: updates });
  };

  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center justify-center py-12"
      >
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">Loading notification preferences...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-medium mb-4">Notification Preferences</h3>
        <p className="text-sm text-muted-foreground mb-6">
          Choose how you want to be notified for different types of events.
        </p>
      </div>

      {/* Header Row */}
      <div className="grid grid-cols-[1fr_auto_auto] gap-4 pb-2 border-b">
        <div className="text-sm font-medium">Notification Type</div>
        {CHANNELS.map((channel) => (
          <div key={channel.value} className="text-sm font-medium text-center w-20">
            {channel.label}
          </div>
        ))}
      </div>

      {/* Preference Rows */}
      <div className="space-y-4">
        {PREFERENCE_CATEGORIES.map((row) => (
          <div key={row.category} className="grid grid-cols-[1fr_auto_auto] gap-4 items-center">
            <div>
              <p className="text-sm font-medium">{row.label}</p>
              <p className="text-xs text-muted-foreground">{row.description}</p>
            </div>
            {CHANNELS.map((channel) => (
              <div key={channel.value} className="flex justify-center w-20">
                <Switch
                  checked={isEnabled(channel.value, row.category)}
                  onCheckedChange={() => handleToggle(channel.value, row.category)}
                  aria-label={`${channel.label} notifications for ${row.label}`}
                />
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t">
        <Button
          onClick={handleSave}
          disabled={updatePreferences.isPending}
        >
          {updatePreferences.isPending && (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          )}
          Save Preferences
        </Button>
      </div>

      {/* Success Message */}
      {updatePreferences.isSuccess && (
        <p className="text-sm text-green-600 text-right">
          Preferences saved successfully!
        </p>
      )}
    </div>
  );
}
