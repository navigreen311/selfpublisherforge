"use client";

import { Users, BookOpen, Clock, DollarSign } from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";
import { Skeleton } from "@/components/ui/skeleton";

interface StatsCardsProps {
  accountCount: number;
  activeListingCount: number;
  pendingExportCount: number;
  totalRevenue: number;
  /** Listings load separately from accounts, so its card can be pending alone. */
  listingsLoading?: boolean;
  listingsError?: boolean;
}

export function StatsCards({
  accountCount,
  activeListingCount,
  pendingExportCount,
  totalRevenue,
  listingsLoading = false,
  listingsError = false,
}: StatsCardsProps) {
  const listingValue = listingsLoading ? (
    <Skeleton className="h-8 w-16" />
  ) : listingsError ? (
    "Failed to load"
  ) : (
    activeListingCount.toLocaleString()
  );

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        label="Accounts"
        value={accountCount.toLocaleString()}
        icon={Users}
      />
      <StatCard label="Active Listings" value={listingValue} icon={BookOpen} />
      <StatCard
        label="Pending Exports"
        value={pendingExportCount.toLocaleString()}
        icon={Clock}
      />
      <StatCard
        label="Total Revenue"
        value={`$${totalRevenue.toLocaleString()}`}
        icon={DollarSign}
      />
    </div>
  );
}
