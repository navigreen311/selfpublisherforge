"use client";

import { RoyaltyDashboard } from "@/modules/royalties/components/RoyaltyDashboard";

export default function RoyaltiesPage() {
  return (
    <div className="space-y-4 px-4 sm:px-6 lg:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
          Royalties
        </h1>
        <p className="text-muted-foreground">
          Track distributor-level royalty earnings, import reports, and
          export monthly statements.
        </p>
      </div>
      <RoyaltyDashboard />
    </div>
  );
}
