"use client";

import { useParams, useRouter } from "next/navigation";
import { AudiobookStudio } from "@/modules/audiobook/components/AudiobookStudio";
import { useAudiobookProject } from "@/modules/audiobook/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, ArrowLeft, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export default function AudiobookStudioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { data: project, isLoading, error } = useAudiobookProject(projectId);

  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        {/* Loading header */}
        <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        {/* Loading content */}
        <div className="flex-1 flex">
          <Skeleton className="w-72 h-full shrink-0" />
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-[400px] w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
          <Skeleton className="w-80 h-full shrink-0" />
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="h-screen flex flex-col bg-background">
        {/* Error header with back button */}
        <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push("/audiobook-studio")}
          >
            <ChevronLeft className="h-4 w-4" />
            Back to Studio
          </Button>
        </div>
        {/* Error content */}
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Project not found</h2>
          <p className="text-muted-foreground max-w-md">
            The audiobook project could not be loaded. It may have been deleted or you may not have permission to view it.
          </p>
          <Button asChild variant="outline">
            <Link href="/audiobook-studio">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Return to Studio
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    generating: "default",
    reviewing: "outline",
    mastering: "default",
    complete: "secondary",
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Navigation header with back button and project info */}
      <div className="h-14 border-b flex items-center gap-3 px-4 bg-background shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => router.push("/audiobook-studio")}
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Studio
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-base font-semibold truncate">{project.title}</h1>
          <Badge variant={statusVariant[project.status] || "secondary"} className="shrink-0">
            {project.status}
          </Badge>
        </div>
        <div className="flex-1" />
        <div className="text-sm text-muted-foreground">
          {project.chapters?.length || 0} chapters
        </div>
      </div>

      {/* AudiobookStudio component */}
      <div className="flex-1 overflow-hidden">
        <AudiobookStudio projectId={projectId} />
      </div>
    </div>
  );
}
