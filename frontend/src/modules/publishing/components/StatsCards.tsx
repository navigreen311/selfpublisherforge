"use client";

import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PublishingAccount, ListingDetail } from "../types";

interface StatsCardsProps {
  accounts: PublishingAccount[];
  listings: ListingDetail[];
  listingsLoading: boolean;
  listingsError: boolean;
}

export function StatsCards({
  accounts,
  listings,
  listingsLoading,
  listingsError,
}: StatsCardsProps) {
  const activeListings = listings.filter((l) => l.status === "active" || l.status === "live").length;
  const platforms = new Set(accounts.map((a) => a.platform)).size;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* Connected Accounts */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Connected Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-foreground">{accounts.length}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {platforms} {platforms === 1 ? "platform" : "platforms"}
          </p>
        </CardContent>
      </Card>

      {/* Active Listings */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Active Listings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {listingsLoading ? (
            <Skeleton className="h-8 w-16" />
          ) : listingsError ? (
            <p className="text-sm text-red-500">Failed to load</p>
          ) : (
            <>
              <p className="text-2xl font-bold text-green-600">{activeListings}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {listings.length} total
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* Export Manuscript */}
      <Card className="hover:shadow-md transition-shadow">
        <Link href="/publishing/export" className="block h-full">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Export Manuscript
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground">
              Generate EPUB or print-ready PDF
            </p>
            <p className="mt-1 text-xs text-indigo-600 font-medium">
              Start export →
            </p>
          </CardContent>
        </Link>
      </Card>

      {/* Validation */}
      <Card className="hover:shadow-md transition-shadow">
        <Link href="/publishing/validation" className="block h-full">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              KDP Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground">
              Pre-flight checks for publishing
            </p>
            <p className="mt-1 text-xs text-indigo-600 font-medium">
              Run validation →
            </p>
          </CardContent>
        </Link>
      </Card>
    </div>
  );
}
