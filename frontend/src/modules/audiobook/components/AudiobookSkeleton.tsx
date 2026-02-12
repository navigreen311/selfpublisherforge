"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";

// ---------------------------------------------------------------------------
// ChapterListSkeleton — matches the left panel (w-72 border-r)
// ---------------------------------------------------------------------------

export function ChapterListSkeleton() {
  const widths = ["w-3/4", "w-5/6", "w-2/3", "w-4/5", "w-1/2", "w-5/6", "w-3/5", "w-4/5"];

  return (
    <div className="w-72 border-r flex flex-col bg-card shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-3 w-12" />
      </div>

      {/* Chapter rows */}
      <div className="flex-1 overflow-y-auto py-1">
        {widths.map((w, i) => (
          <div key={i} className="px-3 py-2.5 border-l-2 border-l-transparent">
            <div className="flex items-center gap-2">
              <Skeleton className="h-3.5 w-3.5 rounded shrink-0" />
              <Skeleton className="h-3 w-6 shrink-0" />
              <Skeleton className={`h-4 ${w}`} />
              <Skeleton className="h-4 w-4 rounded-full shrink-0" />
            </div>
            <div className="flex items-center justify-between mt-1 pl-7">
              <Skeleton className="h-3 w-14" />
              <Skeleton className="h-3 w-10" />
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="border-t px-4 py-2 bg-muted/30">
        <Skeleton className="h-3 w-40" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AudiobookStudioSkeleton — matches the full 4-panel layout
// ---------------------------------------------------------------------------

export function AudiobookStudioSkeleton() {
  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top bar skeleton */}
      <div className="h-16 border-b flex items-center gap-4 px-4 bg-background shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Skeleton className="h-5 w-5 rounded shrink-0" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex items-center gap-2 min-w-[200px]">
          <Skeleton className="h-2 flex-1 rounded-full" />
          <Skeleton className="h-3 w-20" />
        </div>
        <div className="hidden lg:flex items-center gap-4">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-28 rounded-md" />
          <Skeleton className="h-8 w-32 rounded-md" />
          <Skeleton className="h-8 w-28 rounded-md" />
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel — chapter list */}
        <ChapterListSkeleton />

        {/* Center panel — main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chapter header */}
          <div className="flex items-center justify-between px-6 py-3 border-b bg-muted/20">
            <div className="space-y-1.5">
              <Skeleton className="h-5 w-56" />
              <Skeleton className="h-3 w-32" />
            </div>
            <Skeleton className="h-8 w-32 rounded-md" />
          </div>

          {/* Manuscript text area */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-prose mx-auto space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-11/12" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          </div>

          {/* Waveform area */}
          <div className="h-48 border-t bg-muted/10 flex flex-col">
            <div className="flex items-center justify-between px-4 py-2 border-b">
              <Skeleton className="h-3.5 w-28" />
            </div>
            <div className="flex-1 flex items-end gap-px px-4 py-2">
              {Array.from({ length: 60 }, (_, i) => (
                <Skeleton
                  key={i}
                  className="flex-1 rounded-t"
                  style={{ height: `${20 + (((i * 7 + 13) % 37) / 37) * 80}%` }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right panel — settings */}
        <div className="w-80 border-l flex flex-col bg-card shrink-0">
          <div className="flex items-center gap-2 px-4 py-3 border-b">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* 4 setting sections */}
            {[1, 2, 3, 4].map((section) => (
              <div key={section} className="space-y-2">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-9 w-full rounded-md" />
                {section === 2 && (
                  <>
                    <Skeleton className="h-16 w-full rounded-md" />
                    <Skeleton className="h-16 w-full rounded-md" />
                  </>
                )}
                {section === 3 && (
                  <div className="space-y-2">
                    <Skeleton className="h-1.5 w-full rounded-full" />
                    <Skeleton className="h-1.5 w-full rounded-full" />
                    <Skeleton className="h-1.5 w-full rounded-full" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom bar skeleton */}
      <div className="h-16 border-t flex items-center gap-4 px-4 bg-background shrink-0">
        <div className="flex items-center gap-1">
          <Skeleton className="h-8 w-8 rounded-md" />
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-8 w-8 rounded-md" />
        </div>
        <Skeleton className="h-4 w-32" />
        <div className="flex-1 flex items-center gap-2">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-2 flex-1 rounded-full" />
          <Skeleton className="h-3 w-12" />
        </div>
        <Skeleton className="h-8 w-20 rounded-md" />
        <div className="flex items-center gap-1">
          <Skeleton className="h-8 w-8 rounded-md" />
          <Skeleton className="h-2 w-20 rounded-full" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProjectListSkeleton — grid of 6 project card skeletons
// ---------------------------------------------------------------------------

export function ProjectListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
      {Array.from({ length: 6 }, (_, i) => (
        <Card key={i} className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
          <Skeleton className="h-3 w-3/4" />
          <div className="flex items-center gap-4">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-2 w-full rounded-full" />
          <div className="flex items-center justify-between pt-1">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-8 w-20 rounded-md" />
          </div>
        </Card>
      ))}
    </div>
  );
}
