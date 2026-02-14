"use client";

import { useMemo, useState } from "react";
import { Plus, Headphones, Music2, BookOpen, Clock, CheckCircle2, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StatCard } from "@/components/shared/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAudiobookProjects } from "@/modules/audiobook/hooks";
import { AudiobookProjectList } from "@/modules/audiobook/components/AudiobookProjectList";
import { NewProjectDialog } from "@/modules/audiobook/components/NewProjectDialog";

function StatsCardsLoading() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
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
      ))}
    </div>
  );
}

export default function AudiobookStudioPage() {
  const { data, isLoading } = useAudiobookProjects(1, 100);
  const projects = data?.items ?? [];
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);

  // Calculate stats
  const stats = useMemo(() => {
    if (!projects.length) {
      return {
        totalProjects: 0,
        inProgress: 0,
        completed: 0,
        totalDuration: 0,
      };
    }

    const inProgressStatuses = ["draft", "recording", "reviewing", "mastering", "exporting"];
    const completedStatuses = ["completed", "mastered"];

    return {
      totalProjects: projects.length,
      inProgress: projects.filter((p) => inProgressStatuses.includes(p.status)).length,
      completed: projects.filter((p) => completedStatuses.includes(p.status)).length,
      totalDuration: projects.reduce((acc, p) => acc + (p.total_duration_seconds || 0), 0),
    };
  }, [projects]);

  // Format duration
  const formatDuration = (seconds: number) => {
    if (seconds === 0) return "0h 0m";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Headphones className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Audiobook Studio</h1>
            <p className="text-muted-foreground">AI-powered audiobook production</p>
          </div>
        </div>
        <Button onClick={() => setIsNewProjectOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Audiobook
        </Button>
      </div>

      {isLoading ? (
        <>
          <StatsCardsLoading />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}><CardContent className="p-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
            ))}
          </div>
        </>
      ) : projects.length === 0 ? (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center gap-4 text-center">
            <Music2 className="h-12 w-12 text-muted-foreground" />
            <div>
              <h3 className="font-semibold text-lg">No audiobooks yet</h3>
              <p className="text-muted-foreground">Create your first audiobook project to get started.</p>
            </div>
            <Button onClick={() => setIsNewProjectOpen(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create Audiobook
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total Projects"
              value={stats.totalProjects}
              icon={BookOpen}
            />
            <StatCard
              label="In Progress"
              value={stats.inProgress}
              icon={Clock}
            />
            <StatCard
              label="Completed"
              value={stats.completed}
              icon={CheckCircle2}
            />
            <StatCard
              label="Total Duration"
              value={formatDuration(stats.totalDuration)}
              icon={Headphones}
            />
          </div>

          {/* Project List */}
          <AudiobookProjectList onCreateNew={() => setIsNewProjectOpen(true)} />
        </>
      )}

      {/* New Project Dialog */}
      <NewProjectDialog
        open={isNewProjectOpen}
        onOpenChange={setIsNewProjectOpen}
      />
    </div>
  );
}
