"use client";

import { usePortfolioOverview } from "@/modules/analytics/hooks";
import { PortfolioOverview } from "@/modules/analytics/components/PortfolioOverview";
import { BacklistTable } from "@/modules/analytics/components/BacklistTable";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

export default function PortfolioPage() {
  const { data: overview, isLoading, error } = usePortfolioOverview();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Portfolio Economics</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card rounded-lg border p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </div>
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Portfolio Economics</h1>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">Failed to load portfolio data. Please try again.</p>
        </div>
      </div>
    );
  }

  if (!overview) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Portfolio Economics</h1>
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <p className="text-gray-600">No portfolio data available.</p>
        </div>
      </div>
    );
  }

  // Combine top performers and underperformers for backlist table
  const allBooks = [
    ...overview.top_performers,
    ...overview.underperformers,
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Portfolio Economics</h1>
        <nav className="flex space-x-2">
          <Link
            href="/analytics/portfolio/audience"
            className="px-4 py-2 text-sm font-medium text-foreground bg-card border rounded-md hover:bg-muted"
          >
            Audience DNA
          </Link>
          <Link
            href="/analytics/portfolio/greenlight"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Greenlight Gate
          </Link>
        </nav>
      </div>

      {/* Portfolio Overview */}
      <PortfolioOverview overview={overview} />

      {/* Backlist Table */}
      {allBooks.length > 0 && <BacklistTable books={allBooks} />}

      {/* Empty State */}
      {allBooks.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Books Yet</h3>
          <p className="text-gray-600 mb-6">
            Start building your portfolio by adding books to your projects.
          </p>
          <Link
            href="/projects"
            className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            Go to Projects
          </Link>
        </div>
      )}
    </div>
  );
}
