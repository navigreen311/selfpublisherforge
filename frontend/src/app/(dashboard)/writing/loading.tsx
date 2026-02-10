import { Skeleton } from "@/components/ui/skeleton";

export default function WritingLoading() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Page header */}
      <div>
        <Skeleton className="h-8 w-44" />
        <Skeleton className="h-4 w-80 mt-2" />
      </div>

      {/* Quick actions skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-4">
            <Skeleton className="h-4 w-32 mb-2" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4 mt-1" />
          </div>
        ))}
      </div>

      {/* Search skeleton */}
      <div>
        <Skeleton className="h-10 w-full max-w-md" />
      </div>

      {/* Manuscripts list skeleton */}
      <div>
        <Skeleton className="h-6 w-40 mb-3" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-5 w-16 rounded-full" />
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                </div>
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent sessions skeleton */}
      <div>
        <Skeleton className="h-6 w-48 mb-3" />
        <div className="rounded-lg border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-muted-foreground">Book</th>
                <th className="text-left px-4 py-2 font-medium text-muted-foreground">Words Written</th>
                <th className="text-left px-4 py-2 font-medium text-muted-foreground">Duration</th>
                <th className="text-left px-4 py-2 font-medium text-muted-foreground">Date</th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-t">
                  <td className="px-4 py-2"><Skeleton className="h-4 w-36" /></td>
                  <td className="px-4 py-2"><Skeleton className="h-4 w-16" /></td>
                  <td className="px-4 py-2"><Skeleton className="h-4 w-16" /></td>
                  <td className="px-4 py-2"><Skeleton className="h-4 w-20" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
