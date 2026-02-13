# FIX16: Wire Audiobook Studio Detail Page

## Task
Replace the placeholder `/audiobook-studio/[id]` page with a real implementation that renders the AudiobookStudio component.

## File to Modify: `frontend/src/app/(dashboard)/audiobook-studio/[id]/page.tsx`

### Implementation
Read the existing file first, then replace with:

```tsx
"use client";

import { useParams } from "next/navigation";
import { AudiobookStudio } from "@/modules/audiobook/components/AudiobookStudio";
import { useAudiobookProject } from "@/modules/audiobook/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function AudiobookStudioDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: project, isLoading, error } = useAudiobookProject(projectId);

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          <Skeleton className="h-[600px] col-span-1" />
          <Skeleton className="h-[600px] col-span-2" />
          <Skeleton className="h-[600px] col-span-1" />
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container mx-auto py-12 flex flex-col items-center gap-4 text-center">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <h2 className="text-xl font-semibold">Project not found</h2>
        <p className="text-muted-foreground">
          The audiobook project could not be loaded. It may have been deleted.
        </p>
        <Button asChild variant="outline">
          <Link href="/audiobook-studio">Back to Studio</Link>
        </Button>
      </div>
    );
  }

  return <AudiobookStudio projectId={projectId} />;
}
```

## Conventions
- Use "use client" for client-side rendering
- Use existing hooks for data fetching
- Show loading skeleton matching the 4-panel layout
- Show error state with back link
