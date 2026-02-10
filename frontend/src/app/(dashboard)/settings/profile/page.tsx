"use client";

import { ProfileForm } from "@/modules/users/components/ProfileForm";

export default function ProfileSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Profile</h2>
        <p className="text-sm text-gray-500">
          Update your personal information and display preferences.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-6">
        <ProfileForm />
      </div>
    </div>
  );
}
