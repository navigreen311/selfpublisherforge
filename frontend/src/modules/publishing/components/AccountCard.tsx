"use client";

import { useState } from "react";
import { useDeleteAccount, type PublishingAccount } from "../hooks";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";

const platformLabels: Record<string, string> = {
  kdp: "Amazon KDP",
  ingram_spark: "IngramSpark",
  draft2digital: "Draft2Digital",
  smashwords: "Smashwords",
  apple_books: "Apple Books",
  barnes_noble: "Barnes & Noble",
  kobo: "Kobo",
  google_play: "Google Play Books",
};

const platformColors: Record<string, string> = {
  kdp: "bg-orange-100 text-orange-800",
  ingram_spark: "bg-blue-100 text-blue-800",
  draft2digital: "bg-green-100 text-green-800",
  smashwords: "bg-purple-100 text-purple-800",
  apple_books: "bg-gray-100 text-gray-800",
  barnes_noble: "bg-emerald-100 text-emerald-800",
  kobo: "bg-red-100 text-red-800",
  google_play: "bg-sky-100 text-sky-800",
};

interface AccountCardProps {
  account: PublishingAccount;
}

export function AccountCard({ account }: AccountCardProps) {
  const deleteAccount = useDeleteAccount();
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);

  const handleDisconnect = () => {
    deleteAccount.mutate(account.id, {
      onSuccess: () => {
        setShowDisconnectConfirm(false);
        toast.success("Account disconnected");
      },
      onError: () => toast.error("Failed to disconnect account"),
    });
  };

  const label = platformLabels[account.platform] || account.platform;
  const colorClass = platformColors[account.platform] || "bg-gray-100 text-gray-800";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${colorClass}`}>
            {label}
          </span>
          <h3 className="mt-2 text-lg font-semibold text-gray-900">{account.account_name}</h3>
          {account.account_email && (
            <p className="mt-1 text-sm text-gray-500">{account.account_email}</p>
          )}
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
            account.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}
        >
          {account.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <span>
          {account.last_synced_at
            ? `Last synced: ${new Date(account.last_synced_at).toLocaleDateString()}`
            : "Never synced"}
        </span>
        <button
          onClick={() => setShowDisconnectConfirm(true)}
          disabled={deleteAccount.isPending}
          aria-label={`Disconnect ${account.account_name}`}
          className="text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
        >
          {deleteAccount.isPending ? "Disconnecting..." : "Disconnect"}
        </button>
      </div>

      <ConfirmDialog
        open={showDisconnectConfirm}
        onOpenChange={setShowDisconnectConfirm}
        onConfirm={handleDisconnect}
        title="Disconnect Account"
        description={`Are you sure you want to disconnect "${account.account_name}"? This will remove the account connection and stop syncing data from ${label}. You can reconnect it later.`}
        confirmText="Disconnect"
        variant="destructive"
        loading={deleteAccount.isPending}
      />
    </div>
  );
}
