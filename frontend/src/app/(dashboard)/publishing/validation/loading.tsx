import { Skeleton } from "@/components/ui/skeleton";

export default function ValidationLoading() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="mt-2 h-4 w-96" />
      </div>

      {/* Book Selector */}
      <div className="rounded-lg border bg-card p-4">
        <Skeleton className="h-5 w-40 mb-2" />
        <Skeleton className="h-10 w-full max-w-md" />
      </div>

      {/* Dashboard Card */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="mt-2 h-4 w-64" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <Skeleton className="h-32 w-full" />
      </div>

      {/* Runner Card */}
      <div className="rounded-lg border bg-card p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-5 w-full" />
          ))}
        </div>
        <Skeleton className="mt-6 h-10 w-full" />
      </div>
    </div>
  );
}
