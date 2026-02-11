"use client";

import { NotificationPreferences } from "@/modules/notifications/components/NotificationPreferences";

export default function NotificationSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 id="notification-settings-heading" className="text-lg font-semibold">
          Notifications
        </h2>
        <p className="text-sm text-gray-500">
          Manage how and when you receive notifications.
        </p>
      </div>

      <section
        aria-labelledby="notification-settings-heading"
        className="rounded-lg border bg-white p-6"
      >
        <NotificationPreferences />
      </section>
    </div>
  );
}
