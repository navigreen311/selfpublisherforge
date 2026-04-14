"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "@/hooks/use-translations";
import {
  Plus,
  FolderOpen,
  AlertCircle,
  MoreHorizontal,
  Archive,
  Trash2,
  CheckSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { BulkActionsToolbar } from "@/components/shared/BulkActionsToolbar";
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
import { FilterBar } from "@/components/shared/FilterBar";
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
  const t = useTranslations("projects");
  const router = useRouter();
  const [search, setSearch] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState("all");
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [sortBy, setSortBy] = React.useState("updated_desc");

  const [debouncedSearch, setDebouncedSearch] = React.useState("");

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = React.useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  // Archive confirmation state
  const [archiveTarget, setArchiveTarget] = React.useState<Project | null>(null);
  const [isArchiving, setIsArchiving] = React.useState(false);

  // Bulk selection state
  const [bulkMode, setBulkMode] = React.useState(false);
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(
    new Set(),
  );

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

  // Client-side type filter + sort (the API may not support type filtering)
  const filteredProjects = React.useMemo(() => {
    if (!projects) return [];
    const filtered = projects.filter((p: Project) => {
      const matchesType = typeFilter === "all" || p.type === typeFilter;
      return matchesType;
    });
    const sorted = [...filtered];
    switch (sortBy) {
      case "title_asc":
        sorted.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "title_desc":
        sorted.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case "created_desc":
        sorted.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
        break;
      case "updated_desc":
      default:
        sorted.sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        );
    }
    return sorted;
  }, [projects, typeFilter, sortBy]);

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
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={bulkMode ? "default" : "outline"}
            onClick={() => {
              setBulkMode((v) => !v);
              setSelectedIds(new Set());
            }}
            aria-label={bulkMode ? "Exit bulk mode" : "Enter bulk mode"}
            aria-pressed={bulkMode}
          >
            <CheckSquare className="mr-2 h-4 w-4" />
            {bulkMode ? "Exit Bulk" : "Bulk Select"}
          </Button>
          <Button asChild aria-label="Create a new project" className="w-full sm:w-auto">
            <Link href="/projects/new">
              <Plus className="mr-2 h-4 w-4" /> {t("newProject")}
            </Link>
          </Button>
        </div>
      </div>

      {bulkMode && (
        <BulkActionsToolbar
          selectedIds={Array.from(selectedIds)}
          totalCount={filteredProjects.length}
          allSelected={
            filteredProjects.length > 0 &&
            selectedIds.size === filteredProjects.length
          }
          onToggleSelectAll={() => {
            if (selectedIds.size === filteredProjects.length) {
              setSelectedIds(new Set());
            } else {
              setSelectedIds(
                new Set(filteredProjects.map((p: Project) => p.id)),
              );
            }
          }}
          onClearSelection={() => {
            setSelectedIds(new Set());
            setBulkMode(false);
          }}
          selectedPreview={filteredProjects
            .filter((p: Project) => selectedIds.has(p.id))
            .map((p: Project) => ({ id: p.id, title: p.title }))}
        />
      )}

      {/* Filters -- shared FilterBar per Phase 1.2 + inline type filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <FilterBar
            searchPlaceholder={t("searchPlaceholder")}
            onSearch={setSearch}
            statusOptions={[
              { label: t("filters.allStatus"), value: "all" },
              { label: t("filters.draft"), value: "draft" },
              { label: t("filters.active"), value: "active" },
              { label: t("filters.archived"), value: "archived" },
            ]}
            onStatusChange={setStatusFilter}
            initialStatus={statusFilter}
            onSortChange={setSortBy}
            initialSort={sortBy}
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[140px]" aria-label="Filter by project type">
            <SelectValue placeholder={t("filters.type")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("filters.allTypes")}</SelectItem>
            <SelectItem value="book">{t("filters.book")}</SelectItem>
            <SelectItem value="series">{t("filters.series")}</SelectItem>
            <SelectItem value="course">{t("filters.course")}</SelectItem>
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
                {t("error.title")}
              </p>
              <p className="text-sm text-muted-foreground">
                {error?.message || t("error.fallback")}
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
          title={t("empty.title")}
          description={t("empty.description")}
          actionLabel={t("empty.action")}
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
                  {bulkMode && (
                    <Checkbox
                      checked={selectedIds.has(project.id)}
                      onCheckedChange={(checked) => {
                        setSelectedIds((prev) => {
                          const next = new Set(prev);
                          if (checked) {
                            next.add(project.id);
                          } else {
                            next.delete(project.id);
                          }
                          return next;
                        });
                      }}
                      aria-label={`Select project ${project.title}`}
                      className="mt-1"
                    />
                  )}
                  <Link
                    href={`/projects/${project.id}`}
                    className="flex-1 min-w-0"
                    aria-label={`Open project ${project.title}`}
                    onClick={(e) => {
                      if (bulkMode) {
                        e.preventDefault();
                        setSelectedIds((prev) => {
                          const next = new Set(prev);
                          if (next.has(project.id)) {
                            next.delete(project.id);
                          } else {
                            next.add(project.id);
                          }
                          return next;
                        });
                      }
                    }}
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
                          {t("actions.open")}
                        </DropdownMenuItem>
                        {project.status !== "archived" && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => setArchiveTarget(project)}
                              aria-label={`Archive project ${project.title}`}
                            >
                              <Archive className="mr-2 h-4 w-4" />
                              {t("actions.archive")}
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
                          {t("actions.delete")}
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
                      {(project.books?.length ?? 0) === 1 ? t("stats.book") : t("stats.books")}
                    </span>
                    <span className="text-[10px] sm:text-xs">
                      {t("stats.updated")}{" "}
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
        title={t("deleteDialog.title")}
        description={
          deleteTarget
            ? t("deleteDialog.description", { title: deleteTarget.title })
            : ""
        }
        confirmText={t("deleteDialog.confirm")}
        cancelText={t("deleteDialog.cancel")}
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
        title={t("archiveDialog.title")}
        description={
          archiveTarget
            ? t("archiveDialog.description", { title: archiveTarget.title })
            : ""
        }
        confirmText={t("archiveDialog.confirm")}
        cancelText={t("archiveDialog.cancel")}
        variant="default"
        loading={isArchiving}
      />
    </div>
  );
}
