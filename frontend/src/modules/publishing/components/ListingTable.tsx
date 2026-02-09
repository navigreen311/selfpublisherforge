"use client";

import { useListings, useSyncListing, type ListingDetail } from "../hooks";
import { toast } from "sonner";

const platformLabels: Record<string, string> = {
  kdp: "Amazon KDP",
  ingram_spark: "IngramSpark",
  draft2digital: "Draft2Digital",
  smashwords: "Smashwords",
  apple_books: "Apple Books",
  barnes_noble: "Barnes & Noble",
  kobo: "Kobo",
  google_play: "Google Play",
};

const statusStyles: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  pending: "bg-yellow-100 text-yellow-700",
  live: "bg-green-100 text-green-700",
  paused: "bg-orange-100 text-orange-700",
  rejected: "bg-red-100 text-red-700",
  archived: "bg-gray-200 text-gray-500",
};

export function ListingTable() {
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
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading listings...</div>
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

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
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
          {listings.map((listing: ListingDetail) => (
            <tr key={listing.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                {listing.title || "Untitled"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {platformLabels[listing.platform] || listing.platform}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                    statusStyles[listing.status] || statusStyles.draft
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
