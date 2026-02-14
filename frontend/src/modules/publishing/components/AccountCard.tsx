"use client";

import { useState } from "react";
import { Settings, Unlink, CalendarDays, Mail, Globe, BookOpen } from "lucide-react";
import { useDeleteAccount, type PublishingAccount } from "../hooks";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";

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

interface AccountMetadata {
  region?: string;
  [key: string]: unknown;
}

interface AccountCardProps {
  account: PublishingAccount;
  /** Optional metadata with region and other platform-specific info. */
  metadata?: AccountMetadata;
  /** Number of listings associated with this account. */
  listingCount?: number;
  /** Called when the user clicks "Manage". */
  onManage?: (accountId: string) => void;
}

export function AccountCard({
  account,
  metadata,
  listingCount,
  onManage,
}: AccountCardProps) {
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
  const colorClass =
    platformColors[account.platform] || "bg-gray-100 text-gray-800";
  const connectedDate = new Date(account.created_at).toLocaleDateString(
    undefined,
    { year: "numeric", month: "short", day: "numeric" }
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header: Platform badge + Status dot */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <span
            className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${colorClass}`}
          >
            {label}
          </span>
          <h3 className="mt-2 text-xl font-bold text-gray-900 truncate">
            {account.account_name}
          </h3>
        </div>

        {/* Status dot */}
        <div className="flex items-center gap-2 shrink-0 pt-1">
          <span
            className={`inline-block h-3 w-3 rounded-full ${
              account.is_active ? "bg-green-500" : "bg-red-500"
            }`}
            title={account.is_active ? "Active" : "Inactive"}
            aria-label={account.is_active ? "Active" : "Inactive"}
          />
          <span className="text-xs font-medium text-gray-500">
            {account.is_active ? "Active" : "Inactive"}
          </span>
        </div>
      </div>

      {/* Account details */}
      <div className="mt-3 space-y-1.5">
        {account.account_email && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Mail className="h-3.5 w-3.5 shrink-0 text-gray-400" />
            <span className="truncate">{account.account_email}</span>
          </div>
        )}

        {metadata?.region && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Globe className="h-3.5 w-3.5 shrink-0 text-gray-400" />
            <span>{metadata.region}</span>
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <CalendarDays className="h-3.5 w-3.5 shrink-0 text-gray-400" />
          <span>Connected {connectedDate}</span>
        </div>

        {listingCount != null && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <BookOpen className="h-3.5 w-3.5 shrink-0 text-gray-400" />
            <span>
              {listingCount} {listingCount === 1 ? "listing" : "listings"}
            </span>
          </div>
        )}
      </div>

      {/* Sync info */}
      <p className="mt-3 text-xs text-gray-400">
        {account.last_synced_at
          ? `Last synced ${new Date(account.last_synced_at).toLocaleDateString()}`
          : "Never synced"}
      </p>

      {/* Actions */}
      <div className="mt-4 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onManage?.(account.id)}
          className="flex-1"
        >
          <Settings className="mr-1.5 h-4 w-4" />
          Manage
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setShowDisconnectConfirm(true)}
          disabled={deleteAccount.isPending}
          className="flex-1"
          aria-label={`Disconnect ${account.account_name}`}
        >
          <Unlink className="mr-1.5 h-4 w-4" />
          {deleteAccount.isPending ? "Disconnecting..." : "Disconnect"}
        </Button>
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
