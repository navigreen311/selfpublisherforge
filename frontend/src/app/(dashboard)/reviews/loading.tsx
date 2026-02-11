import { Skeleton } from "@/components/ui/skeleton";

export default function ReviewsLoading() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading review intelligence">
      <h1 className="text-2xl font-bold text-foreground">Review Intelligence</h1>

      {/* KPI Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" role="status">
        <span className="sr-only">Loading key performance indicators...</span>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card rounded-lg border p-6">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-3 w-20 mt-1" />
          </div>
        ))}
      </div>

      {/* Alerts Panel Skeleton */}
      <div className="bg-card rounded-lg border p-6">
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>

      {/* Charts Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-80 w-full" aria-label="Loading sentiment chart" />
        <Skeleton className="h-80 w-full" aria-label="Loading velocity tracker" />
      </div>

      {/* Reviews List Skeleton */}
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    </div>
  );
}
