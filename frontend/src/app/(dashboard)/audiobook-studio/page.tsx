"use client";

import { useState, useMemo } from "react";
import { Plus, Headphones, BookOpen, Clock, DollarSign, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/shared/stat-card";
import { useAudiobookProjects } from "@/modules/audiobook/hooks";
import { AudiobookProjectList } from "@/modules/audiobook/components/AudiobookProjectList";
import { NewProjectDialog } from "@/modules/audiobook/components/NewProjectDialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

function formatDuration(seconds: number): string {
  if (seconds <= 0) return "0h 0m";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

// ---------------------------------------------------------------------------
// Skeleton components
// ---------------------------------------------------------------------------

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
          </div>
          <Skeleton className="h-12 w-12 rounded-full" />
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function AudiobookStudioPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data, isLoading, isError } = useAudiobookProjects(1, 100);
  const projects = data?.items ?? [];

  // Calculate stats
  const stats = useMemo(() => {
    if (!projects.length) {
      return {
        totalProjects: 0,
        completedProjects: 0,
        totalDuration: 0,
        totalCost: 0,
      };
    }

    return {
      totalProjects: projects.length,
      completedProjects: projects.filter((p) => p.status === "complete" || p.status === "published").length,
      totalDuration: projects.reduce((sum, p) => sum + (p.total_duration_seconds ?? 0), 0),
      totalCost: projects.reduce((sum, p) => sum + (p.total_cost_usd ?? 0), 0),
    };
  }, [projects]);

  const handleCreateNew = () => {
    setDialogOpen(true);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Headphones className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Audiobook Studio</h1>
            <p className="text-muted-foreground">AI-powered audiobook production</p>
          </div>
        </div>
        <Button onClick={handleCreateNew}>
          <Plus className="h-4 w-4 mr-2" /> New Audiobook
        </Button>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : projects.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Projects"
            value={stats.totalProjects}
            icon={BookOpen}
          />
          <StatCard
            label="Completed"
            value={stats.completedProjects}
            icon={CheckCircle2}
          />
          <StatCard
            label="Total Duration"
            value={formatDuration(stats.totalDuration)}
            icon={Clock}
          />
          <StatCard
            label="Total Cost"
            value={`$${stats.totalCost.toFixed(2)}`}
            icon={DollarSign}
          />
        </div>
      ) : null}

      {/* Projects List */}
      {isError ? (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center gap-4 text-center">
            <p className="text-muted-foreground">Failed to load audiobook projects</p>
            <p className="text-sm text-muted-foreground/70">Please try again later</p>
          </CardContent>
        </Card>
      ) : (
        <AudiobookProjectList onCreateNew={handleCreateNew} />
      )}

      {/* Create Dialog */}
      <NewProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
