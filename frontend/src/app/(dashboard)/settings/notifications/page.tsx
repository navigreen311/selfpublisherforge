"use client";

import { NotificationsTab } from "@/modules/settings/components/NotificationsTab";

export default function SettingsNotificationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 id="notification-settings-heading" className="text-lg font-semibold">
          Notifications
        </h2>
        <p className="text-sm text-muted-foreground">
          Manage how and when you receive notifications.
        </p>
      </div>

      <section aria-labelledby="notification-settings-heading">
        <NotificationsTab />
      </section>
    </div>
  );
}
