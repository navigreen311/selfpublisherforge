"use client";

import { usePublishingAccounts } from "../hooks";
import { AccountCard } from "./AccountCard";
import { Skeleton } from "@/components/ui/skeleton";

export function AccountsTab() {
  const { data: accounts = [], isLoading, error } = usePublishingAccounts();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-40 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load accounts. Please try again.
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <h3 className="text-lg font-medium text-gray-900">No accounts connected</h3>
        <p className="mt-2 text-sm text-gray-500">
          Connect a publishing platform account to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {accounts.map((account) => (
        <AccountCard key={account.id} account={account} />
      ))}
    </div>
  );
}
