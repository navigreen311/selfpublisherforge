"use client";

import { useMemo } from "react";
import { useListings, type ListingDetail } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  PUBLISHING_PLATFORM_LABELS,
} from "@/lib/constants";

/* ------------------------------------------------------------------ */
/*  Status dot color mapping                                          */
/* ------------------------------------------------------------------ */

const STATUS_DOT_COLORS: Record<string, string> = {
  live: "bg-green-500",
  pending: "bg-yellow-400",
  draft: "bg-gray-400",
  paused: "bg-orange-400",
  rejected: "bg-red-500",
  archived: "bg-gray-300",
};

function StatusDot({ status }: { status: string }) {
  const color = STATUS_DOT_COLORS[status] ?? STATUS_DOT_COLORS.draft;
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${color}`}
      title={status}
      aria-label={status}
    />
  );
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

interface BookGroup {
  book_id: string;
  title: string;
  listings: ListingDetail[];
}

function groupByBook(listings: ListingDetail[]): BookGroup[] {
  const map = new Map<string, BookGroup>();

  for (const listing of listings) {
    const key = listing.book_id;
    let group = map.get(key);
    if (!group) {
      group = {
        book_id: key,
        title: listing.title || "Untitled",
        listings: [],
      };
      map.set(key, group);
    }
    group.listings.push(listing);
  }

  return Array.from(map.values());
}

/* ------------------------------------------------------------------ */
/*  Skeleton loader                                                    */
/* ------------------------------------------------------------------ */

function ListingsTabSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" role="status" aria-label="Loading listings">
      {[1, 2].map((i) => (
        <div
          key={i}
          className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
        >
          <Skeleton className="mb-4 h-6 w-48" />
          <div className="space-y-3">
            {[1, 2, 3].map((j) => (
              <div key={j} className="flex items-center gap-4">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-2.5 w-2.5 rounded-full" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-4 w-14" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Platform row inside a book card                                    */
/* ------------------------------------------------------------------ */

function PlatformRow({ listing }: { listing: ListingDetail }) {
  const platformLabel =
    PUBLISHING_PLATFORM_LABELS[listing.platform] || listing.platform;

  return (
    <tr className="border-t border-gray-100 first:border-t-0">
      {/* Platform name */}
      <td className="py-2 pr-4 text-sm font-medium text-gray-900">
        {platformLabel}
      </td>

      {/* Status dot */}
      <td className="py-2 pr-4">
        <div className="flex items-center gap-2">
          <StatusDot status={listing.status} />
          <span className="text-xs capitalize text-gray-600">
            {listing.status}
          </span>
        </div>
      </td>

      {/* Platform listing ID (ASIN / ISBN) */}
      <td className="py-2 pr-4 text-sm text-gray-600">
        {listing.platform_listing_id ? (
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">
            {listing.platform_listing_id}
          </code>
        ) : (
          <span className="text-gray-400">-</span>
        )}
      </td>

      {/* Price */}
      <td className="py-2 pr-4 text-sm text-gray-700">
        {listing.current_price != null
          ? `$${listing.current_price.toFixed(2)}`
          : "-"}
      </td>

      {/* Reviews count */}
      <td className="py-2 pr-4 text-sm text-gray-700">
        {listing.reviews_count != null ? listing.reviews_count : "-"}
      </td>

      {/* BSR (Best Seller Rank) */}
      <td className="py-2 text-sm text-gray-700">
        {listing.current_rank != null
          ? `#${listing.current_rank.toLocaleString()}`
          : "-"}
      </td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/*  Book card                                                          */
/* ------------------------------------------------------------------ */

function BookCard({ group }: { group: BookGroup }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{group.title}</CardTitle>
      </CardHeader>

      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs font-medium uppercase tracking-wider text-gray-500">
                <th className="pb-2 pr-4">Platform</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">ID</th>
                <th className="pb-2 pr-4">Price</th>
                <th className="pb-2 pr-4">Reviews</th>
                <th className="pb-2">BSR</th>
              </tr>
            </thead>
            <tbody>
              {group.listings.map((listing) => (
                <PlatformRow key={listing.id} listing={listing} />
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>

      <CardFooter className="gap-2 border-t pt-4">
        <Button variant="outline" size="sm" onClick={() => {}}>
          View All Platforms
        </Button>
        <Button variant="outline" size="sm" onClick={() => {}}>
          Update Pricing
        </Button>
        <Button variant="outline" size="sm" onClick={() => {}}>
          View Analytics
        </Button>
      </CardFooter>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export function ListingsTab() {
  const { data: listings = [], isLoading, error } = useListings();

  const bookGroups = useMemo(() => groupByBook(listings), [listings]);

  if (isLoading) {
    return <ListingsTabSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load listings. Please try again.
      </div>
    );
  }

  if (bookGroups.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <h3 className="text-lg font-medium text-gray-900">No listings yet</h3>
        <p className="mt-2 text-sm text-gray-500">
          No listings yet. Publish your first book to see it here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {bookGroups.map((group) => (
        <BookCard key={group.book_id} group={group} />
      ))}
    </div>
  );
}
