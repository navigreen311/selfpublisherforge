"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Plus,
  Search,
  FolderOpen,
  AlertCircle,
  MoreHorizontal,
  Archive,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useProjects,
  useDeleteProject,
  useUpdateProject,
  type Project,
} from "@/modules/projects/hooks";

const badgeVariant = (status: string) => {
  switch (status) {
    case "active":
      return "default" as const;
    case "draft":
      return "secondary" as const;
    case "archived":
      return "outline" as const;
    default:
      return "secondary" as const;
  }
};

function ProjectCardSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-4 w-16 mt-1" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-28" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function ProjectsPage() {
  const router = useRouter();
  const [search, setSearch] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState("all");
  const [statusFilter, setStatusFilter] = React.useState("all");

  const [debouncedSearch, setDebouncedSearch] = React.useState("");

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = React.useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  // Archive confirmation state
  const [archiveTarget, setArchiveTarget] = React.useState<Project | null>(null);
  const [isArchiving, setIsArchiving] = React.useState(false);

  const deleteProject = useDeleteProject();
  const updateProject = useUpdateProject();

  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data: projects, isLoading, isError, error } = useProjects({
    status: statusFilter !== "all" ? statusFilter : undefined,
    search: debouncedSearch || undefined,
  });

  // Client-side type filter (the API may not support type filtering)
  const filteredProjects = React.useMemo(() => {
    if (!projects) return [];
    return projects.filter((p: Project) => {
      const matchesType = typeFilter === "all" || p.type === typeFilter;
      return matchesType;
    });
  }, [projects, typeFilter]);

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteProject.mutateAsync(deleteTarget.id);
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  const handleArchiveConfirm = async () => {
    if (!archiveTarget) return;
    setIsArchiving(true);
    try {
      await updateProject.mutateAsync({
        id: archiveTarget.id,
        data: { status: "archived" },
      });
    } finally {
      setIsArchiving(false);
      setArchiveTarget(null);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Manage all your publishing projects
          </p>
        </div>
        <Button asChild aria-label="Create a new project" className="w-full sm:w-auto">
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search projects"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[140px]" aria-label="Filter by project type">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="book">Book</SelectItem>
            <SelectItem value="series">Series</SelectItem>
            <SelectItem value="course">Course</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[140px]" aria-label="Filter by project status">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Error State */}
      {isError && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 py-6">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">
                Failed to load projects
              </p>
              <p className="text-sm text-muted-foreground">
                {error?.message || "An unexpected error occurred. Please try again."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ProjectCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && filteredProjects.length === 0 && (
        <EmptyState
          icon={FolderOpen}
          title="No projects found"
          description="Try adjusting your search or filters, or create a new project to get started."
          actionLabel="Create Project"
          onAction={() => router.push("/projects/new")}
        />
      )}

      {/* Projects Grid */}
      {!isLoading && !isError && filteredProjects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((project: Project) => (
            <Card
              key={project.id}
              className="hover:shadow-md transition-shadow h-full"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <Link
                    href={`/projects/${project.id}`}
                    className="flex-1 min-w-0"
                    aria-label={`Open project ${project.title}`}
                  >
                    <CardTitle className="text-sm sm:text-base hover:underline cursor-pointer">
                      {project.title}
                    </CardTitle>
                  </Link>
                  <div className="flex items-center gap-1 sm:gap-2 shrink-0">
                    <Badge variant={badgeVariant(project.status)} className="text-[10px] sm:text-xs">
                      {project.status}
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 sm:h-8 sm:w-8"
                          aria-label={`Actions for project ${project.title}`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreHorizontal className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => router.push(`/projects/${project.id}`)}
                          aria-label={`Open project ${project.title}`}
                        >
                          <FolderOpen className="mr-2 h-4 w-4" />
                          Open
                        </DropdownMenuItem>
                        {project.status !== "archived" && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => setArchiveTarget(project)}
                              aria-label={`Archive project ${project.title}`}
                            >
                              <Archive className="mr-2 h-4 w-4" />
                              Archive
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => setDeleteTarget(project)}
                          className="text-destructive focus:text-destructive"
                          aria-label={`Delete project ${project.title}`}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
                <CardDescription className="capitalize text-xs sm:text-sm">
                  {project.type}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link
                  href={`/projects/${project.id}`}
                  className="block cursor-pointer"
                  aria-label={`View details for project ${project.title}`}
                >
                  <div className="flex items-center justify-between text-xs sm:text-sm text-muted-foreground">
                    <span>
                      {project.books?.length ?? 0}{" "}
                      {(project.books?.length ?? 0) === 1 ? "book" : "books"}
                    </span>
                    <span className="text-[10px] sm:text-xs">
                      Updated{" "}
                      {new Date(project.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete Project"
        description={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.title}"? This action cannot be undone and all associated data will be permanently removed.`
            : ""
        }
        confirmText="Delete Project"
        cancelText="Cancel"
        variant="destructive"
        loading={isDeleting}
      />

      {/* Archive Confirmation Dialog */}
      <ConfirmDialog
        open={!!archiveTarget}
        onOpenChange={(open) => {
          if (!open) setArchiveTarget(null);
        }}
        onConfirm={handleArchiveConfirm}
        title="Archive Project"
        description={
          archiveTarget
            ? `Are you sure you want to archive "${archiveTarget.title}"? Archived projects can be restored later from the archived filter.`
            : ""
        }
        confirmText="Archive Project"
        cancelText="Cancel"
        variant="default"
        loading={isArchiving}
      />
    </div>
  );
}
