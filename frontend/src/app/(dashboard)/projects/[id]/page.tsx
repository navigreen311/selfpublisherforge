"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  AlertCircle,
  Pencil,
  Trash2,
  Loader2,
  Calendar,
  Tag,
  BookOpen,
  FolderOpen,
} from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { EmptyState } from "@/components/shared/EmptyState";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Clock, FileText, StickyNote, Layers } from "lucide-react";
import {
  useProject,
  useUpdateProject,
  useDeleteProject,
  type Project,
} from "@/modules/projects/hooks";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const genres = [
  "Fiction",
  "Non-Fiction",
  "Romance",
  "Mystery",
  "Sci-Fi",
  "Fantasy",
  "Self-Help",
  "Business",
  "Biography",
  "Children",
  "Other",
];

const PROJECT_TYPES = ["book", "series", "course"] as const;
const PROJECT_STATUSES = ["draft", "active", "archived", "completed"] as const;

const badgeVariant = (status: string) => {
  switch (status) {
    case "active":
      return "default" as const;
    case "draft":
      return "secondary" as const;
    case "completed":
      return "default" as const;
    case "archived":
      return "outline" as const;
    default:
      return "secondary" as const;
  }
};

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function ProjectDetailSkeleton() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-md" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-1">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-5 w-32" />
              </div>
            ))}
          </div>
          <div className="space-y-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-16 w-full" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function ProjectDetailPage() {
  const t = useTranslations("projects");
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: project, isLoading, isError, error } = useProject(id);
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  // Edit mode state
  const [isEditing, setIsEditing] = React.useState(false);
  const [editTitle, setEditTitle] = React.useState("");
  const [editType, setEditType] = React.useState("");
  const [editStatus, setEditStatus] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);

  // Delete confirmation state
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);

  // Populate edit form when project loads or edit mode is entered
  const populateEditForm = React.useCallback((p: Project) => {
    setEditTitle(p.title);
    setEditType(p.type);
    setEditStatus(p.status);
  }, []);

  const handleEditStart = () => {
    if (project) {
      populateEditForm(project);
      setIsEditing(true);
    }
  };

  const handleEditCancel = () => {
    setIsEditing(false);
  };

  const handleEditSave = async () => {
    if (!project) return;

    const trimmedTitle = editTitle.trim();
    if (!trimmedTitle) {
      toast.error(t("detail.messages.titleEmpty"));
      return;
    }

    setIsSaving(true);
    try {
      await updateProject.mutateAsync({
        id: project.id,
        data: {
          title: trimmedTitle,
          type: editType as "book" | "series" | "course",
          status: editStatus as "draft" | "active" | "archived" | "completed",
        },
      });
      toast.success(t("detail.messages.updateSuccess"));
      setIsEditing(false);
    } catch {
      toast.error(t("detail.messages.updateError"));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!project) return;
    setIsDeleting(true);
    try {
      await deleteProject.mutateAsync(project.id);
      toast.success(t("detail.messages.deleteSuccess"));
      router.push("/projects");
    } catch {
      toast.error(t("detail.messages.deleteError"));
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  // Loading state
  if (isLoading) {
    return <ProjectDetailSkeleton />;
  }

  // Error state
  if (isError) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label={t("detail.backToProjects")}>
            <Link href="/projects">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold tracking-tight">{t("detail.title")}</h1>
        </div>

        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 py-6">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
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
      </div>
    );
  }

  // No project found (shouldn't happen with proper API, but handle gracefully)
  if (!project) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label={t("detail.backToProjects")}>
            <Link href="/projects">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold tracking-tight">{t("detail.notFound")}</h1>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FolderOpen className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              {t("detail.notFoundDescription")}
            </p>
            <Button asChild className="mt-4" aria-label={t("detail.backToList")}>
              <Link href="/projects">{t("detail.backToList")}</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label={t("detail.backToProjects")}>
            <Link href="/projects">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {project.title}
            </h1>
            <p className="text-muted-foreground capitalize">{project.type}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isEditing && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEditStart}
                aria-label={t("detail.edit")}
              >
                <Pencil className="mr-2 h-4 w-4" />
                {t("detail.edit")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteDialog(true)}
                className="text-destructive hover:text-destructive"
                aria-label={t("detail.delete")}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("detail.delete")}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Phase 2.2 tabbed detail view: Overview / Modules / Timeline / Files / Notes */}
      <Tabs defaultValue="overview">
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="notes">Notes</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-4">
      {/* Project Details Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{t("detail.details.title")}</CardTitle>
            {!isEditing && (
              <Badge variant={badgeVariant(project.status)}>
                {project.status}
              </Badge>
            )}
          </div>
          {!isEditing && (
            <CardDescription>
              {t("detail.details.description")}
            </CardDescription>
          )}
        </CardHeader>

        {isEditing ? (
          /* ---- Inline Edit Form ---- */
          <>
            <CardContent className="space-y-4">
              <Input
                label={t("detail.editForm.projectTitle")}
                placeholder={t("detail.editForm.projectTitle")}
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                required
                aria-required="true"
                aria-label={t("detail.editForm.projectTitle")}
              />

              <div className="space-y-1.5">
                <label
                  htmlFor="edit-project-type"
                  className="text-sm font-medium"
                >
                  {t("detail.editForm.projectType")}
                </label>
                <Select value={editType} onValueChange={setEditType}>
                  <SelectTrigger
                    id="edit-project-type"
                    aria-label={t("detail.editForm.projectType")}
                  >
                    <SelectValue placeholder={t("detail.editForm.projectType")} />
                  </SelectTrigger>
                  <SelectContent>
                    {PROJECT_TYPES.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="edit-project-status"
                  className="text-sm font-medium"
                >
                  {t("detail.editForm.status")}
                </label>
                <Select value={editStatus} onValueChange={setEditStatus}>
                  <SelectTrigger
                    id="edit-project-status"
                    aria-label={t("detail.editForm.status")}
                  >
                    <SelectValue placeholder={t("detail.editForm.status")} />
                  </SelectTrigger>
                  <SelectContent>
                    {PROJECT_STATUSES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={handleEditCancel}
                disabled={isSaving}
                aria-label={t("detail.editForm.cancel")}
              >
                {t("detail.editForm.cancel")}
              </Button>
              <Button
                onClick={handleEditSave}
                disabled={isSaving || !editTitle.trim()}
                aria-label={t("detail.editForm.save")}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t("detail.editForm.saving")}
                  </>
                ) : (
                  t("detail.editForm.save")
                )}
              </Button>
            </CardFooter>
          </>
        ) : (
          /* ---- Read-only view ---- */
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Tag className="h-3.5 w-3.5" />
                  {t("detail.details.type")}
                </div>
                <p className="text-sm font-medium capitalize">{project.type}</p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Tag className="h-3.5 w-3.5" />
                  {t("detail.details.status")}
                </div>
                <p className="text-sm font-medium capitalize">
                  {project.status}
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5" />
                  {t("detail.details.created")}
                </div>
                <p className="text-sm font-medium">
                  {new Date(project.created_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5" />
                  {t("detail.details.lastUpdated")}
                </div>
                <p className="text-sm font-medium">
                  {new Date(project.updated_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>

            {Boolean(project.settings?.genre) && (
              <div className="mt-6 space-y-1">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <BookOpen className="h-3.5 w-3.5" />
                  {t("detail.details.genre")}
                </div>
                <p className="text-sm font-medium capitalize">
                  {String(project.settings?.genre)}
                </p>
              </div>
            )}

            {Boolean(project.settings?.description) && (
              <div className="mt-6 space-y-1">
                <p className="text-sm text-muted-foreground">{t("new.form.description")}</p>
                <p className="text-sm">{String(project.settings?.description)}</p>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Books Section */}
      {!isEditing && project.books && project.books.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              {t("detail.books.title", { count: project.books.length })}
            </CardTitle>
            <CardDescription>
              {t("detail.books.description")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {project.books.map((book) => (
                <div
                  key={book.id}
                  className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                >
                  <div>
                    <p className="text-sm font-medium">{book.title}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {book.format}
                    </p>
                  </div>
                  <Badge variant="secondary" className="capitalize">
                    {book.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

        </TabsContent>

        <TabsContent value="modules" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Linked Modules</CardTitle>
              <CardDescription>
                Production modules attached to this project.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<Layers />}
                title="No linked modules yet"
                description="Modules like Cover Design, Audiobook, and Marketing will appear here once started."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
              <CardDescription>Milestones and activity history.</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<Clock />}
                title="No timeline events yet"
                description="Milestones, stage changes, and completions will be logged here."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="files" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Files</CardTitle>
              <CardDescription>
                Manuscripts, covers, audio masters and other assets.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<FileText />}
                title="No files uploaded"
                description="Upload manuscripts, covers, and other assets to keep everything in one place."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notes" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
              <CardDescription>
                Private notes and to-dos for this project.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<StickyNote />}
                title="No notes yet"
                description="Jot down ideas, blockers, or reminders about this project."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={(open) => {
          if (!open) setShowDeleteDialog(false);
        }}
        onConfirm={handleDeleteConfirm}
        title={t("deleteDialog.title")}
        description={t("deleteDialog.description", { title: project.title })}
        confirmText={t("deleteDialog.confirm")}
        cancelText={t("deleteDialog.cancel")}
        variant="destructive"
        loading={isDeleting}
      />
    </div>
  );
}
