"use client";

import { Users, BookOpen, Clock, DollarSign } from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";

interface StatsCardsProps {
  accountCount: number;
  activeListingCount: number;
  pendingExportCount: number;
  totalRevenue: number;
}

export function StatsCards({
  accountCount,
  activeListingCount,
  pendingExportCount,
  totalRevenue,
}: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        label="Accounts"
        value={accountCount.toLocaleString()}
        icon={Users}
      />
      <StatCard
        label="Active Listings"
        value={activeListingCount.toLocaleString()}
        icon={BookOpen}
      />
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
