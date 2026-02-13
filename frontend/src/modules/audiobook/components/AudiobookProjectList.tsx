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
  CircleDot,
  FileEdit,
} from "lucide-react";
import { useAudiobookProjects } from "../hooks";

// ---------------------------------------------------------------------------
// Types (local — matches the shape returned by the API / useAudiobookProjects)
// ---------------------------------------------------------------------------

type ProjectStatus = "draft" | "generating" | "reviewing" | "mastering" | "complete";

interface AudiobookProjectItem {
  id: string;
  title: string;
  status: ProjectStatus;
  total_duration: number; // seconds
  estimated_cost: number;
  actual_cost: number;
  chapter_count: number;
  completed_chapters: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  ProjectStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ElementType }
> = {
  draft: { label: "Draft", variant: "secondary", icon: FileEdit },
  generating: { label: "Generating", variant: "default", icon: Loader2 },
  reviewing: { label: "Reviewing", variant: "outline", icon: AlertCircle },
  mastering: { label: "Mastering", variant: "default", icon: CircleDot },
  complete: { label: "Complete", variant: "secondary", icon: CheckCircle2 },
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
  onClick,
}: {
  project: AudiobookProjectItem;
  onClick: () => void;
}) {
  const config = STATUS_CONFIG[project.status] ?? STATUS_CONFIG.draft;
  const StatusIcon = config.icon;
  const progress = getProgress(project.completed_chapters, project.chapter_count);
  const cost = project.actual_cost > 0 ? project.actual_cost : project.estimated_cost;

  return (
    <Card
      className="overflow-hidden cursor-pointer transition-shadow hover:shadow-md hover:border-primary/30"
      onClick={onClick}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-sm leading-tight line-clamp-2">
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
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} className="h-1.5" />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <BookOpen className="h-3 w-3 shrink-0" aria-hidden="true" />
            <span>
              {project.chapter_count} ch{project.chapter_count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 shrink-0" aria-hidden="true" />
            <span>{formatDuration(project.total_duration)}</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="h-3 w-3 shrink-0" aria-hidden="true" />
            <span>{formatCost(cost)}</span>
          </div>
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

  // Fetch all projects (first page — large page size for client-side filtering)
  const { data, isLoading } = useAudiobookProjects(1, 100);

  const projects: AudiobookProjectItem[] = useMemo(() => {
    if (!data?.items) return [];

    // Normalize API response to our local shape
    return data.items.map((item) => ({
      id: item.id ?? "",
      title: item.title ?? "Untitled",
      status: (item.status ?? "draft") as ProjectStatus,
      total_duration: item.total_duration_seconds ?? 0,
      estimated_cost: item.total_cost_usd ?? 0,
      actual_cost: item.total_cost_usd ?? 0,
      chapter_count: item.total_chapters ?? 0,
      completed_chapters: item.completed_chapters ?? 0,
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
          const pa = getProgress(a.completed_chapters, a.chapter_count);
          const pb = getProgress(b.completed_chapters, b.chapter_count);
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
            placeholder="Search by title…"
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
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="generating">Generating</SelectItem>
            <SelectItem value="reviewing">Reviewing</SelectItem>
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
              onClick={() => router.push(`/audiobook-studio/${project.id}`)}
            />
          ))
        )}
      </div>
    </div>
  );
}
