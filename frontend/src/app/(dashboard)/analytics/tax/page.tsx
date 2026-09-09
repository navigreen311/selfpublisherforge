"use client";

import { TaxDashboard } from "@/modules/royalties_tax/components/TaxDashboard";

export default function TaxPage() {
  return (
    <div className="space-y-4 px-4 sm:px-6 lg:px-0">
      <div className="flex items-center justify-between">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Tax</h1>
        <a
          href="/analytics"
          aria-label="Back to analytics dashboard"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Analytics
        </a>
      </div>
      <TaxDashboard />
    </div>
  );
}
