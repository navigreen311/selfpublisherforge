"use client";

import Link from "next/link";
import { StatsCards } from "@/modules/publishing/components/StatsCards";
import { PublishingTabs } from "@/modules/publishing/components/PublishingTabs";
import {
  usePublishingAccounts,
  useListings,
} from "@/modules/publishing/hooks";
import { useTranslations } from "@/hooks/use-translations";

export default function PublishingDashboardPage() {
  const t = useTranslations("publishing");
  const { data: accounts = [], isLoading: accountsLoading } = usePublishingAccounts();
  const {
    data: listings = [],
    isLoading: listingsLoading,
    isError: listingsError,
  } = useListings();

  return (
    <div className="space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-foreground">
            {t("title")}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>
        <Link
          href="/publishing/export"
          className="w-full sm:w-auto rounded-md bg-indigo-600 px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-indigo-700 text-center"
        >
          {t("newExport")}
        </Link>
      </div>

      {/* Stats */}
      <StatsCards
        accountCount={accounts.length}
        activeListingCount={listings.length}
        pendingExportCount={0}
        totalRevenue={0}
      />

      {/* Tabs: Listings & Accounts */}
      <PublishingTabs />
    </div>
  );
}
