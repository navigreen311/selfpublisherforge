"use client";

import { ProfileForm } from "@/modules/users/components/ProfileForm";
import { DangerZone } from "@/modules/users/components/DangerZone";
import { Separator } from "@/components/ui/separator";

export default function ProfileSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 id="profile-settings-heading" className="text-lg font-semibold">
          Profile
        </h2>
        <p className="text-sm text-muted-foreground">
          Update your personal information and display preferences.
        </p>
      </div>

      <section
        aria-labelledby="profile-settings-heading"
        className="rounded-lg border bg-card p-6"
      >
        <ProfileForm />
      </section>

      <Separator />

      <DangerZone />
    </div>
  );
}
