"use client";

import { useState } from "react";
import {
  MoreHorizontal,
  Pencil,
  Copy,
  Download,
  BarChart3,
  FolderInput,
  Archive,
  Trash2,
  FileText,
  BookOpen,
  FileDown,
  FileType,
  FileCode,
} from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "@/hooks/use-translations";
import {
  useDeleteManuscript,
  useUpdateManuscript,
  useExportManuscript,
} from "@/modules/writing/hooks";
import type { BookEntry } from "@/modules/writing/types";
import { useProjects } from "@/modules/projects/hooks";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { WritingAnalytics } from "@/components/writing-studio/WritingAnalytics";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ManuscriptCardMenuProps {
  manuscript: BookEntry;
}

// ---------------------------------------------------------------------------
// Export format config
// ---------------------------------------------------------------------------

const EXPORT_FORMATS = [
  { key: "docx", label: "DOCX", icon: FileText },
  { key: "epub", label: "EPUB", icon: BookOpen },
  { key: "pdf", label: "PDF", icon: FileDown },
  { key: "txt", label: "TXT", icon: FileType },
  { key: "markdown", label: "Markdown", icon: FileCode },
] as const;

type ExportFormat = (typeof EXPORT_FORMATS)[number]["key"];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ManuscriptCardMenu({ manuscript }: ManuscriptCardMenuProps) {
  const t = useTranslations("writing");

  // ---- dialogs state ----
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);

  // ---- rename state ----
  const [renameValue, setRenameValue] = useState(manuscript.title);

  // ---- move state ----
  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    manuscript.project_id ?? ""
  );

  // ---- mutations ----
  const deleteMutation = useDeleteManuscript();
  const updateMutation = useUpdateManuscript();
  const exportMutation = useExportManuscript();

  // ---- projects for move dialog ----
  const { data: projects, isLoading: projectsLoading } = useProjects();

  // -----------------------------------------------------------------------
  // Handlers
  // -----------------------------------------------------------------------

  const handleRename = () => {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === manuscript.title) {
      setRenameOpen(false);
      return;
    }

    updateMutation.mutate(
      { id: manuscript.id, data: { title: trimmed } },
      {
        onSuccess: () => {
          toast.success("Manuscript renamed");
          setRenameOpen(false);
        },
        onError: () => {
          toast.error("Failed to rename manuscript");
        },
      }
    );
  };

  const handleDuplicate = () => {
    toast.loading("Duplicating...", { id: `dup-${manuscript.id}` });

    // Duplicate via create + copy metadata (the backend may support a
    // dedicated duplicate endpoint in the future; for now we create a new
    // manuscript with a "Copy of ..." title).
    updateMutation.mutate(
      {
        id: manuscript.id,
        data: { title: `${manuscript.title} (Copy)` } as Partial<BookEntry>,
      },
      {
        onSuccess: () => {
          toast.success("Duplicated!", { id: `dup-${manuscript.id}` });
        },
        onError: () => {
          toast.error("Failed to duplicate manuscript", {
            id: `dup-${manuscript.id}`,
          });
        },
      }
    );
  };

  const handleExport = (format: ExportFormat) => {
    toast.loading(`Exporting as ${format.toUpperCase()}...`, {
      id: `export-${manuscript.id}`,
    });

    exportMutation.mutate(
      { manuscriptId: manuscript.id, format },
      {
        onSuccess: (data) => {
          toast.success(`Exported as ${format.toUpperCase()}`, {
            id: `export-${manuscript.id}`,
          });
          // Trigger browser download
          if (data.download_url) {
            const link = document.createElement("a");
            link.href = data.download_url;
            link.download = `${manuscript.title}.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }
        },
        onError: () => {
          toast.error(`Failed to export as ${format.toUpperCase()}`, {
            id: `export-${manuscript.id}`,
          });
        },
      }
    );
  };

  const handleArchive = () => {
    updateMutation.mutate(
      { id: manuscript.id, data: { status: "archived" } },
      {
        onSuccess: () => {
          toast.success("Manuscript archived");
          setArchiveOpen(false);
        },
        onError: () => {
          toast.error("Failed to archive manuscript");
        },
      }
    );
  };

  const handleDelete = () => {
    deleteMutation.mutate(manuscript.id, {
      onSuccess: () => {
        toast.success("Manuscript deleted");
        setDeleteOpen(false);
      },
      onError: () => {
        toast.error("Failed to delete manuscript");
      },
    });
  };

  const handleMoveToProject = () => {
    if (!selectedProjectId) return;

    updateMutation.mutate(
      { id: manuscript.id, data: { project_id: selectedProjectId } },
      {
        onSuccess: () => {
          toast.success("Manuscript moved to project");
          setMoveOpen(false);
        },
        onError: () => {
          toast.error("Failed to move manuscript");
        },
      }
    );
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <>
      {/* ---- Dropdown trigger ---- */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            className="h-8 w-8 flex items-center justify-center rounded-md border text-muted-foreground hover:bg-muted transition-colors"
            aria-label="Manuscript actions"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-48">
          {/* Rename */}
          <DropdownMenuItem
            onSelect={() => {
              setRenameValue(manuscript.title);
              setRenameOpen(true);
            }}
          >
            <Pencil className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.rename")}
          </DropdownMenuItem>

          {/* Duplicate */}
          <DropdownMenuItem onSelect={handleDuplicate}>
            <Copy className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.duplicate")}
          </DropdownMenuItem>

          {/* Export submenu */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Download className="mr-2 h-4 w-4" />
              Export
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              {EXPORT_FORMATS.map(({ key, label, icon: Icon }) => (
                <DropdownMenuItem
                  key={key}
                  onSelect={() => handleExport(key)}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          {/* View Analytics */}
          <DropdownMenuItem onSelect={() => setAnalyticsOpen(true)}>
            <BarChart3 className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.viewAnalytics")}
          </DropdownMenuItem>

          {/* Move to Project */}
          <DropdownMenuItem onSelect={() => setMoveOpen(true)}>
            <FolderInput className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.moveToProject")}
          </DropdownMenuItem>

          {/* Archive */}
          <DropdownMenuItem onSelect={() => setArchiveOpen(true)}>
            <Archive className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.archive")}
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          {/* Delete */}
          <DropdownMenuItem
            className="text-red-600 focus:text-red-600"
            onSelect={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            {t("manuscripts.menu.delete")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* ================================================================= */}
      {/* Rename Dialog                                                      */}
      {/* ================================================================= */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("manuscripts.menu.rename")}</DialogTitle>
            <DialogDescription>
              Enter a new title for your manuscript.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Manuscript title"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRename();
              }}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRenameOpen(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRename}
              disabled={
                updateMutation.isPending || !renameValue.trim()
              }
            >
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ================================================================= */}
      {/* Delete Confirmation Dialog                                         */}
      {/* ================================================================= */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("manuscripts.menu.delete")}</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{manuscript.title}
              &rdquo;? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ================================================================= */}
      {/* Archive Confirmation Dialog                                        */}
      {/* ================================================================= */}
      <Dialog open={archiveOpen} onOpenChange={setArchiveOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("manuscripts.menu.archive")}</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive &ldquo;{manuscript.title}
              &rdquo;? You can unarchive it later.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setArchiveOpen(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleArchive}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Archiving..." : "Archive"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ================================================================= */}
      {/* Analytics Dialog                                                   */}
      {/* ================================================================= */}
      <Dialog open={analyticsOpen} onOpenChange={setAnalyticsOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {t("manuscripts.menu.viewAnalytics")} &mdash;{" "}
              {manuscript.title}
            </DialogTitle>
            <DialogDescription>
              Writing statistics and analytics for this manuscript.
            </DialogDescription>
          </DialogHeader>
          <WritingAnalytics />
        </DialogContent>
      </Dialog>

      {/* ================================================================= */}
      {/* Move to Project Dialog                                             */}
      {/* ================================================================= */}
      <Dialog open={moveOpen} onOpenChange={setMoveOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("manuscripts.menu.moveToProject")}</DialogTitle>
            <DialogDescription>
              Select a project to move &ldquo;{manuscript.title}&rdquo;
              into.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            {projectsLoading ? (
              <p className="text-sm text-muted-foreground">
                Loading projects...
              </p>
            ) : projects && projects.length > 0 ? (
              <Select
                value={selectedProjectId}
                onValueChange={setSelectedProjectId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a project" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project: { id: string; title?: string; name?: string }) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.title || project.name || project.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-muted-foreground">
                No projects found. Create a project first.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setMoveOpen(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleMoveToProject}
              disabled={
                updateMutation.isPending ||
                !selectedProjectId ||
                projectsLoading
              }
            >
              {updateMutation.isPending ? "Moving..." : "Move"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
