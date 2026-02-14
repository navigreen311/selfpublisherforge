"use client";

import { useListings } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import {
  PUBLISHING_PLATFORM_LABELS,
} from "@/lib/constants";

export function PricingTab() {
  const { data: listings = [], isLoading, error } = useListings();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load pricing data. Please try again.
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <h3 className="text-lg font-medium text-gray-900">No pricing data</h3>
        <p className="mt-2 text-sm text-gray-500">
          Publish your book to a platform to start tracking prices.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Pricing Overview</h2>
        <p className="mt-1 text-sm text-gray-500">
          View and compare pricing across all your published listings.
        </p>
      </div>
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
                Current Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {listings.map((listing) => (
              <tr key={listing.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                  {listing.title || "Untitled"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                  {PUBLISHING_PLATFORM_LABELS[listing.platform] || listing.platform}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                  {listing.current_price != null
                    ? `$${listing.current_price.toFixed(2)}`
                    : "-"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                  {listing.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
