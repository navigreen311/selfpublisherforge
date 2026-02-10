"use client";

import { useListings, useSyncListing, type ListingDetail } from "../hooks";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import {
  PUBLISHING_PLATFORM_LABELS,
  LISTING_STATUS_STYLES,
} from "@/lib/constants";

const SKELETON_ROWS = 5;

interface ListingTableProps {
  /** Optional filter predicate applied client-side after data is fetched. */
  filter?: (listing: ListingDetail) => boolean;
}

export function ListingTable({ filter }: ListingTableProps = {}) {
  const { data: listings = [], isLoading, error } = useListings();
  const syncListing = useSyncListing();

  const handleSync = (listingId: string) => {
    syncListing.mutate(listingId, {
      onSuccess: () => toast.success("Sync started"),
      onError: () => toast.error("Failed to start sync"),
    });
  };

  if (isLoading) {
    return (
      <div
        className="overflow-hidden rounded-lg border border-gray-200 shadow-sm"
        aria-busy="true"
      >
        <div role="status" aria-label="Loading listings">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Book
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Platform
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Rank
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Reviews
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Last Synced
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {[...Array(SKELETON_ROWS)].map((_, rowIdx) => (
                <tr key={rowIdx}>
                  {/* Book */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-32" />
                  </td>
                  {/* Platform */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-24" />
                  </td>
                  {/* Status */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-6 w-16 rounded-full" />
                  </td>
                  {/* Price */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-14" />
                  </td>
                  {/* Rank */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-16" />
                  </td>
                  {/* Reviews */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-20" />
                  </td>
                  {/* Last Synced */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <Skeleton className="h-4 w-20" />
                  </td>
                  {/* Actions */}
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <Skeleton className="ml-auto h-4 w-12" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load listings. Please try again.
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <h3 className="text-lg font-medium text-gray-900">No listings yet</h3>
        <p className="mt-2 text-sm text-gray-500">
          Export your book and publish to a platform to see listings here.
        </p>
      </div>
    );
  }

  const filteredListings = filter ? listings.filter(filter) : listings;

  if (filteredListings.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 p-12 text-center">
        <p className="text-sm text-gray-500">No listings match your filters</p>
      </div>
    );
  }

  return (
    <div
      className="overflow-hidden rounded-lg border border-gray-200 shadow-sm"
      aria-busy="false"
    >
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Book
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Platform
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Price
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Rank
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Reviews
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Last Synced
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {filteredListings.map((listing: ListingDetail) => (
            <tr key={listing.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                {listing.title || "Untitled"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {PUBLISHING_PLATFORM_LABELS[listing.platform] || listing.platform}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                    LISTING_STATUS_STYLES[listing.status] || LISTING_STATUS_STYLES.draft
                  }`}
                >
                  {listing.status}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {listing.current_price != null ? `$${listing.current_price.toFixed(2)}` : "-"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {listing.current_rank != null ? `#${listing.current_rank.toLocaleString()}` : "-"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {listing.reviews_count != null ? (
                  <span>
                    {listing.reviews_count}
                    {listing.rating != null && (
                      <span className="ml-1 text-yellow-500">
                        ({listing.rating.toFixed(1)})
                      </span>
                    )}
                  </span>
                ) : (
                  "-"
                )}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {listing.last_synced_at
                  ? new Date(listing.last_synced_at).toLocaleDateString()
                  : "Never"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right">
                <button
                  onClick={() => handleSync(listing.id)}
                  disabled={syncListing.isPending}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
                >
                  Sync
                </button>
                {listing.listing_url && (
                  <a
                    href={listing.listing_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-3 text-sm font-medium text-gray-600 hover:text-gray-800"
                  >
                    View
                  </a>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
