"use client";

import { ListingTable } from "./ListingTable";

export function ListingsTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Book Listings</h2>
        <p className="mt-1 text-sm text-gray-500">
          View and manage your book listings across all publishing platforms.
        </p>
      </div>
      <ListingTable />
    </div>
  );
}
