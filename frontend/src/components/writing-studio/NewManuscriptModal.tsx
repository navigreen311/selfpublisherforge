"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useCreateManuscript } from "@/modules/writing/hooks";
import { useProjects } from "@/modules/projects/hooks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NewManuscriptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type BookType = "book" | "series" | "short_story";
type StartingContent = "blank" | "import" | "outline";

const ACCEPTED_FILE_EXTENSIONS = ".docx,.epub,.txt,.md";
const ACCEPTED_EXTENSIONS_LIST = ["docx", "epub", "txt", "md"];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function NewManuscriptModal({
  open,
  onOpenChange,
}: NewManuscriptModalProps) {
  const t = useTranslations("writing");
  const router = useRouter();

  // ---- Form state ----
  const [projectId, setProjectId] = useState<string | undefined>(undefined);
  const [title, setTitle] = useState("");
  const [bookType, setBookType] = useState<BookType>("book");
  const [startingContent, setStartingContent] =
    useState<StartingContent>("blank");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [titleError, setTitleError] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ---- Queries / mutations ----
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const createManuscript = useCreateManuscript();

  // When a project is selected, auto-fill the title if it is still empty
  const handleProjectChange = useCallback(
    (value: string) => {
      const selectedId = value === "__none__" ? undefined : value;
      setProjectId(selectedId);

      if (selectedId) {
        const project = projects.find((p) => p.id === selectedId);
        if (project && !title.trim()) {
          setTitle(project.title);
          setTitleError(false);
        }
      }
    },
    [projects, title],
  );

  // ---- File handling ----
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ACCEPTED_EXTENSIONS_LIST.includes(ext ?? "")) {
      setImportFile(file);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  // ---- Create ----
  const handleCreate = () => {
    if (!title.trim()) {
      setTitleError(true);
      return;
    }

    createManuscript.mutate(
      {
        title: title.trim(),
        type: bookType,
        project_id: projectId,
      },
      {
        onSuccess: (data) => {
          onOpenChange(false);

          if (startingContent === "outline") {
            router.push(`/writing/outline?manuscript=${data.id}`);
          } else {
            router.push(`/writing/${data.id}`);
          }
        },
      },
    );
  };

  // ---- Reset on close ----
  const handleClose = useCallback(() => {
    setProjectId(undefined);
    setTitle("");
    setBookType("book");
    setStartingContent("blank");
    setImportFile(null);
    setTitleError(false);
    setDragActive(false);
    onOpenChange(false);
  }, [onOpenChange]);

  // Reset file when switching away from import
  useEffect(() => {
    if (startingContent !== "import") {
      setImportFile(null);
    }
  }, [startingContent]);

  // ---- Render helpers ----
  const bookTypeOptions: { value: BookType; labelKey: string }[] = [
    { value: "book", labelKey: "newManuscript.typeBook" },
    { value: "series", labelKey: "newManuscript.typeSeries" },
    { value: "short_story", labelKey: "newManuscript.typeShortStory" },
  ];

  const startingContentOptions: {
    value: StartingContent;
    labelKey: string;
  }[] = [
    { value: "blank", labelKey: "newManuscript.blankManuscript" },
    { value: "import", labelKey: "newManuscript.importFile" },
    { value: "outline", labelKey: "newManuscript.fromOutline" },
  ];

  const isCreating = createManuscript.isPending;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("newManuscript.modalTitle")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* ---- Link to Project ---- */}
          <div className="space-y-1.5">
            <Label htmlFor="ms-project">
              {t("newManuscript.linkToProject")}
            </Label>
            <Select
              value={projectId ?? "__none__"}
              onValueChange={handleProjectChange}
            >
              <SelectTrigger id="ms-project" className="w-full">
                <SelectValue
                  placeholder={t("newManuscript.selectProject")}
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">
                  {t("newManuscript.noProject")}
                </SelectItem>
                {projectsLoading ? (
                  <SelectItem value="__loading__" disabled>
                    Loading...
                  </SelectItem>
                ) : (
                  projects.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.title}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>

          <Separator />

          {/* ---- Title ---- */}
          <div className="space-y-1.5">
            <Label htmlFor="ms-title">
              {t("newManuscript.titleLabel")} <span className="text-destructive">*</span>
            </Label>
            <Input
              id="ms-title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (titleError) setTitleError(false);
              }}
              placeholder={t("newManuscript.titlePlaceholder")}
              error={titleError ? t("newManuscript.titleRequired") : undefined}
              autoFocus
            />
          </div>

          {/* ---- Book Type ---- */}
          <div className="space-y-1.5">
            <Label>{t("newManuscript.bookType")}</Label>
            <div className="flex gap-4">
              {bookTypeOptions.map(({ value, labelKey }) => (
                <label
                  key={value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="bookType"
                    value={value}
                    checked={bookType === value}
                    onChange={() => setBookType(value)}
                    className="h-4 w-4 accent-primary"
                  />
                  <span className="text-sm">{t(labelKey)}</span>
                </label>
              ))}
            </div>
          </div>

          {/* ---- Starting Content ---- */}
          <div className="space-y-2">
            <Label>{t("newManuscript.startingContent")}</Label>
            <div className="space-y-2">
              {startingContentOptions.map(({ value, labelKey }) => (
                <label
                  key={value}
                  className={cn(
                    "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                    startingContent === value
                      ? "border-primary bg-primary/5"
                      : "hover:bg-accent/50",
                  )}
                >
                  <input
                    type="radio"
                    name="startingContent"
                    value={value}
                    checked={startingContent === value}
                    onChange={() => setStartingContent(value)}
                    className="h-4 w-4 accent-primary"
                  />
                  <span className="text-sm">{t(labelKey)}</span>
                </label>
              ))}
            </div>
          </div>

          {/* ---- Import file drop zone ---- */}
          {startingContent === "import" && (
            <div
              role="button"
              tabIndex={0}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={cn(
                "rounded-md border-2 border-dashed p-6 text-center cursor-pointer transition-colors",
                dragActive
                  ? "border-primary bg-primary/5"
                  : "hover:border-muted-foreground/50",
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_FILE_EXTENSIONS}
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files)}
              />

              {importFile ? (
                <div className="flex flex-col items-center gap-1">
                  <p className="text-sm font-medium text-foreground">
                    {importFile.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(importFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    type="button"
                    className="mt-1 text-xs text-primary underline underline-offset-2 hover:text-primary/80"
                    onClick={(e) => {
                      e.stopPropagation();
                      setImportFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    {t("newManuscript.removeFile")}
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    {t("newManuscript.dropFileHere")}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t("newManuscript.acceptedFormats")}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ---- Actions ---- */}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isCreating}
          >
            {t("newManuscript.cancel")}
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            {isCreating
              ? t("newManuscript.creating")
              : t("newManuscript.createButton")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
