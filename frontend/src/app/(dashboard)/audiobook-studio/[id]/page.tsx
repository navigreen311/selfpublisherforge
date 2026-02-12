"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Headphones } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

// ASSUMPTION: AudiobookStudio component will be provided by the audiobook
// frontend module (VF24). This dynamic route page will render the full studio
// interface for a specific audiobook project once the module lands.

export default function AudiobookProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params?.id as string;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/audiobook-studio")}
          aria-label="Back to Audiobook Studio"
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3">
          <Headphones className="h-6 w-6 text-primary" aria-hidden="true" />
          <div>
            <h1 className="text-2xl font-bold">Audiobook Project</h1>
            <p className="text-sm text-muted-foreground">Project {projectId}</p>
          </div>
        </div>
      </div>

      {/* Placeholder – will be replaced by AudiobookStudio component */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Skeleton className="h-64 w-full rounded-lg" />
          <Skeleton className="h-32 w-full rounded-lg" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
