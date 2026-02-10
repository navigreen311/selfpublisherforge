import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";

export default function MarketLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <Skeleton className="h-8 w-52" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>

      {/* Search bar skeleton */}
      <div className="flex gap-3">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 w-32" />
      </div>

      {/* Main grid: Category tree + Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category tree skeleton */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-6">
              <Skeleton className="h-5 w-28 mb-4" />
              <div className="space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-2" style={{ paddingLeft: `${(i % 3) * 16}px` }}>
                    <Skeleton className="h-4 w-4" />
                    <Skeleton className="h-4" style={{ width: `${120 - (i % 3) * 20}px` }} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Category analysis skeleton */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardContent className="p-6">
              <Skeleton className="h-6 w-40 mb-4" />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Array.from({ length: 7 }).map((_, i) => (
                  <div key={i} className="p-3 rounded-md bg-muted/50 text-center">
                    <Skeleton className="h-6 w-16 mx-auto mb-1" />
                    <Skeleton className="h-3 w-12 mx-auto" />
                  </div>
                ))}
              </div>

              {/* BSR Distribution skeleton */}
              <div className="mt-6">
                <Skeleton className="h-4 w-28 mb-3" />
                <div className="flex gap-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex-1 text-center">
                      <Skeleton className="mx-auto rounded-t-md" style={{ height: `${40 + i * 20}px`, width: "100%" }} />
                      <Skeleton className="h-3 w-12 mx-auto mt-1" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
