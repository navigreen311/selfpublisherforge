"use client";

import { useCurrentUser } from "@/modules/users/hooks";
import { ApiKeyTable } from "@/modules/users/components/ApiKeyTable";

export default function ApiKeysSettingsPage() {
  const { data: currentUser, isLoading } = useCurrentUser();
  const orgId = currentUser?.org_id ?? "";

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-200 rounded w-1/3" />
        <div className="h-40 bg-gray-100 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">API Keys</h2>
        <p className="text-sm text-gray-500">
          Create and manage API keys for programmatic access to your
          organization's resources.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-6">
        {orgId ? (
          <ApiKeyTable orgId={orgId} />
        ) : (
          <p className="text-sm text-gray-500">
            Unable to load organization. Please try again.
          </p>
        )}
      </div>
    </div>
  );
}
