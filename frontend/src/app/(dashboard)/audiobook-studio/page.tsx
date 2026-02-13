"use client";

import { useRouter } from "next/navigation";
import { Plus, Headphones, Music2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAudiobookProjects } from "@/modules/audiobook/hooks";
import type { AudiobookProject } from "@/modules/audiobook/types";

// Status badge colors
const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  configuring: "bg-blue-100 text-blue-800",
  generating: "bg-yellow-100 text-yellow-800",
  reviewing: "bg-purple-100 text-purple-800",
  mastering: "bg-orange-100 text-orange-800",
  complete: "bg-green-100 text-green-800",
  published: "bg-emerald-100 text-emerald-800",
};

function ProjectCard({ project }: { project: AudiobookProject }) {
  const router = useRouter();
  const progress = project.total_chapters > 0
    ? Math.round((project.completed_chapters / project.total_chapters) * 100)
    : 0;

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => router.push(`/audiobook-studio/${project.id}`)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg line-clamp-1">{project.title || "Untitled Audiobook"}</CardTitle>
          <Badge className={statusColors[project.status] || statusColors.draft}>{project.status}</Badge>
        </div>
        <CardDescription>
          {project.total_chapters} chapters · {project.target_platform.toUpperCase()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{project.completed_chapters}/{project.total_chapters} chapters</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
          {project.total_duration_seconds > 0 && (
            <p className="text-xs text-muted-foreground">
              {Math.floor(project.total_duration_seconds / 3600)}h {Math.floor((project.total_duration_seconds % 3600) / 60)}m
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function AudiobookStudioPage() {
  const { data, isLoading } = useAudiobookProjects();
  const projects = data?.items ?? [];

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
        <Button>
          <Plus className="h-4 w-4 mr-2" /> New Audiobook
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}><CardContent className="p-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center gap-4 text-center">
            <Music2 className="h-12 w-12 text-muted-foreground" />
            <div>
              <h3 className="font-semibold text-lg">No audiobooks yet</h3>
              <p className="text-muted-foreground">Create your first audiobook project to get started.</p>
            </div>
            <Button><Plus className="h-4 w-4 mr-2" /> Create Audiobook</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project: AudiobookProject) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
