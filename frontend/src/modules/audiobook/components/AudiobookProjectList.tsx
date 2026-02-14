"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  Search,
  Plus,
  Clock,
  BookOpen,
  DollarSign,
  ArrowUpDown,
  Headphones,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Settings,
  Pause,
  ThumbsUp,
  Download,
  FileAudio,
  Play,
} from "lucide-react";
import { useAudiobookProjects } from "../hooks";

// ---------------------------------------------------------------------------
// Types (local  matches the shape returned by the API / useAudiobookProjects)
// ---------------------------------------------------------------------------

type ProjectStatus = "configuring" | "generating" | "reviewing" | "mastering" | "complete";

interface AudiobookProjectItem {
  id: string;
  title: string;
  status: ProjectStatus;
  total_duration: number; // seconds
  estimated_cost: number;
  actual_cost: number;
  budget: number;
  chapter_count: number;
  completed_chapters: number;
  narrator_name?: string;
  voice_name?: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  ProjectStatus,
  { 
    label: string; 
    variant: "default" | "secondary" | "destructive" | "outline"; 
    icon: React.ElementType;
    progressColor: string;
  }
> = {
  configuring: { 
    label: "Configuring", 
    variant: "outline", 
    icon: Settings,
    progressColor: "bg-gray-500",
  },
  generating: { 
    label: "Generating", 
    variant: "default", 
    icon: Loader2,
    progressColor: "bg-blue-500",
  },
  reviewing: { 
    label: "Reviewing", 
    variant: "outline", 
    icon: AlertCircle,
    progressColor: "bg-yellow-500",
  },
  mastering: { 
    label: "Mastering", 
    variant: "default", 
    icon: Play,
    progressColor: "bg-purple-500",
  },
  complete: { 
    label: "Complete", 
    variant: "secondary", 
    icon: CheckCircle2,
    progressColor: "bg-green-500",
  },
};

type SortKey = "date-newest" | "date-oldest" | "progress" | "title";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AudiobookProjectListProps {
  onCreateNew: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDuration(seconds: number): string {
  if (seconds <= 0) return "0m";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`;
}

function getProgress(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

function getStatusProgress(project: AudiobookProjectItem): number {
  const statusOrder: ProjectStatus[] = ["configuring", "generating", "reviewing", "mastering", "complete"];
  const currentIndex = statusOrder.indexOf(project.status);
  
  if (project.status === "generating") {
    // For generating, show actual chapter progress
    return getProgress(project.completed_chapters, project.chapter_count);
  }
  
  if (project.status === "complete") {
    return 100;
  }
  
  // For other statuses, show a base percentage
  const baseProgress = (currentIndex / (statusOrder.length - 1)) * 100;
  return Math.round(baseProgress);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ProjectCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-5 w-20 mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-2 w-full" />
        <div className="grid grid-cols-3 gap-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
        <Skeleton className="h-8 w-full" />
      </CardContent>
    </Card>
  );
}

function EmptyState({ hasFilters, onCreateNew }: { hasFilters: boolean; onCreateNew: () => void }) {
  return (
    <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
      <Headphones className="h-12 w-12 text-muted-foreground/40 mb-4" aria-hidden="true" />
      {hasFilters ? (
        <>
          <p className="font-medium text-muted-foreground">No projects match your filters</p>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Try adjusting your search or status filter.
          </p>
        </>
      ) : (
        <>
          <p className="font-medium text-muted-foreground">No audiobook projects yet</p>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Create your first audiobook to get started.
          </p>
          <Button onClick={onCreateNew} className="mt-4" size="sm">
            <Plus className="h-4 w-4 mr-1" aria-hidden="true" />
            New Audiobook
          </Button>
        </>
      )}
    </div>
  );
}

function ProjectCard({
  project,
  onOpenStudio,
}: {
  project: AudiobookProjectItem;
  onOpenStudio: () => void;
}) {
  const config = STATUS_CONFIG[project.status] ?? STATUS_CONFIG.configuring;
  const StatusIcon = config.icon;
  const progress = getStatusProgress(project);
  const cost = project.actual_cost > 0 ? project.actual_cost : project.estimated_cost;
  const narratorVoice = project.narrator_name || project.voice_name || "Not set";

  const handleAction = (e: React.MouseEvent, action: string) => {
    e.stopPropagation();
    console.log(`Action: ${action} for project ${project.id}`);
    // TODO: Implement specific action handlers
  };

  const renderActionButtons = () => {
    const buttonClass = "h-8 text-xs";
    
    switch (project.status) {
      case "configuring":
        return (
          <>
            <Button 
              size="sm" 
              className={buttonClass}
              onClick={onOpenStudio}
            >
              <Settings className="h-3 w-3 mr-1" />
              Open Studio
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className={buttonClass}
              onClick={(e) => handleAction(e, "continue-setup")}
            >
              Continue Setup
            </Button>
          </>
        );
      
      case "generating":
        return (
          <>
            <Button 
              size="sm" 
              className={buttonClass}
              onClick={onOpenStudio}
            >
              <Play className="h-3 w-3 mr-1" />
              Open Studio
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className={buttonClass}
              onClick={(e) => handleAction(e, "pause-generation")}
            >
              <Pause className="h-3 w-3 mr-1" />
              Pause
            </Button>
          </>
        );
      
      case "reviewing":
        return (
          <>
            <Button 
              size="sm" 
              className={buttonClass}
              onClick={onOpenStudio}
            >
              <Play className="h-3 w-3 mr-1" />
              Open Studio
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className={buttonClass}
              onClick={(e) => handleAction(e, "approve-all")}
            >
              <ThumbsUp className="h-3 w-3 mr-1" />
              Approve All
            </Button>
          </>
        );
      
      case "mastering":
        return (
          <>
            <Button 
              size="sm" 
              className={buttonClass}
              onClick={onOpenStudio}
            >
              <Play className="h-3 w-3 mr-1" />
              Open Studio
            </Button>
          </>
        );
      
      case "complete":
        return (
          <>
            <Button 
              size="sm" 
              className={buttonClass}
              onClick={onOpenStudio}
            >
              <Play className="h-3 w-3 mr-1" />
              Open Studio
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className={buttonClass}
              onClick={(e) => handleAction(e, "download")}
            >
              <Download className="h-3 w-3 mr-1" />
              Download
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className={buttonClass}
              onClick={(e) => handleAction(e, "export-acx")}
            >
              <FileAudio className="h-3 w-3 mr-1" />
              Export ACX
            </Button>
          </>
        );
      
      default:
        return (
          <Button size="sm" className={buttonClass} onClick={onOpenStudio}>
            Open Studio
          </Button>
        );
    }
  };

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md hover:border-primary/30">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-base leading-tight line-clamp-2 flex items-center gap-1.5">
            <Headphones className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            {project.title}
          </h3>
          <Badge variant={config.variant} className="shrink-0 text-xs">
            <StatusIcon
              className={cn(
                "h-3 w-3 mr-1",
                project.status === "generating" && "animate-spin",
              )}
              aria-hidden="true"
            />
            {config.label}
            {project.status === "generating" && ` (${progress}%)`}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress bar with status-based coloring */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-medium">Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cn("h-full transition-all duration-300", config.progressColor)}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>
              {project.chapter_count} chapter{project.chapter_count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>{formatDuration(project.total_duration)}</span>
          </div>
          <div className="col-span-2 flex items-center gap-1.5 text-muted-foreground">
            <Headphones className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">{narratorVoice}</span>
          </div>
        </div>

        {/* Cost tracker */}
        <div className="rounded-md bg-muted/50 p-2.5 space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-medium">Cost Tracker</span>
            <span className="font-semibold">
              {formatCost(cost)} / {formatCost(project.budget)}
            </span>
          </div>
          {project.estimated_cost > 0 && project.actual_cost === 0 && (
            <div className="text-xs text-muted-foreground">
              Est: {formatCost(project.estimated_cost)}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          {renderActionButtons()}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AudiobookProjectList({ onCreateNew }: AudiobookProjectListProps) {
  const router = useRouter();

  // Filters & sorting (client-side)
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | "all">("all");
  const [sortKey, setSortKey] = useState<SortKey>("date-newest");

  // Fetch all projects (first page  large page size for client-side filtering)
  const { data, isLoading } = useAudiobookProjects(1, 100);

  const projects: AudiobookProjectItem[] = useMemo(() => {
    if (!data?.items) return [];

    // Normalize API response to our local shape
    return data.items.map((item) => ({
      id: item.id ?? "",
      title: item.title ?? "Untitled",
      status: (item.status ?? "configuring") as ProjectStatus,
      total_duration: item.total_duration_seconds ?? 0,
      estimated_cost: item.total_cost_usd ?? 0,
      actual_cost: item.total_cost_usd ?? 0,
      budget: (item as unknown as Record<string, number>).budget_usd ?? 100,
      chapter_count: item.total_chapters ?? 0,
      completed_chapters: item.completed_chapters ?? 0,
      narrator_name: item.narrator,
      voice_name: item.voice_id,
      created_at: item.created_at ?? "",
      updated_at: item.updated_at ?? "",
    }));
  }, [data]);

  // Apply filters & sorting
  const filtered = useMemo(() => {
    let result = projects;

    // Status filter
    if (statusFilter !== "all") {
      result = result.filter((p) => p.status === statusFilter);
    }

    // Search
    const q = search.trim().toLowerCase();
    if (q) {
      result = result.filter((p) => p.title.toLowerCase().includes(q));
    }

    // Sort
    result = [...result].sort((a, b) => {
      switch (sortKey) {
        case "date-newest":
          return (b.updated_at || b.created_at).localeCompare(a.updated_at || a.created_at);
        case "date-oldest":
          return (a.created_at).localeCompare(b.created_at);
        case "progress": {
          const pa = getStatusProgress(a);
          const pb = getStatusProgress(b);
          return pb - pa;
        }
        case "title":
          return a.title.localeCompare(b.title);
        default:
          return 0;
      }
    });

    return result;
  }, [projects, statusFilter, search, sortKey]);

  const hasFilters = statusFilter !== "all" || search.trim().length > 0;

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            placeholder="Search by title"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Status filter */}
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as ProjectStatus | "all")}
        >
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="configuring">Configuring</SelectItem>
            <SelectItem value="generating">Generating</SelectItem>
            <SelectItem value="reviewing">Reviewing</SelectItem>
            <SelectItem value="mastering">Mastering</SelectItem>
            <SelectItem value="complete">Complete</SelectItem>
          </SelectContent>
        </Select>

        {/* Sort */}
        <Select value={sortKey} onValueChange={(v) => setSortKey(v as SortKey)}>
          <SelectTrigger className="w-full sm:w-44">
            <ArrowUpDown className="h-4 w-4 mr-1 shrink-0" aria-hidden="true" />
            <SelectValue placeholder="Sort" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date-newest">Newest first</SelectItem>
            <SelectItem value="date-oldest">Oldest first</SelectItem>
            <SelectItem value="progress">By progress</SelectItem>
            <SelectItem value="title">By title</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Project grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <>
            {[...Array(6)].map((_, i) => (
              <ProjectCardSkeleton key={i} />
            ))}
          </>
        ) : filtered.length === 0 ? (
          <EmptyState hasFilters={hasFilters} onCreateNew={onCreateNew} />
        ) : (
          filtered.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onOpenStudio={() => router.push(`/audiobook-studio/${project.id}`)}
            />
          ))
        )}
      </div>
    </div>
  );
}
