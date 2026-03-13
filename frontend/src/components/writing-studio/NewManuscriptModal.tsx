"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface NewManuscriptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type BookType = "book" | "series" | "short_story";
type StartingContent = "blank" | "import" | "outline";

export function NewManuscriptModal({ open, onOpenChange }: NewManuscriptModalProps) {
  const t = useTranslations("writing");
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [bookType, setBookType] = useState<BookType>("book");
  const [startingContent, setStartingContent] = useState<StartingContent>("blank");
  const [isCreating, setIsCreating] = useState(false);
  const [titleError, setTitleError] = useState(false);

  const handleCreate = async () => {
    if (!title.trim()) {
      setTitleError(true);
      return;
    }

    setIsCreating(true);
    try {
      // Call the create manuscript API
      const token = localStorage.getItem("access_token");
      const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${baseURL}/api/v1/manuscripts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ title: title.trim(), type: bookType }),
      });

      if (!res.ok) throw new Error("Failed to create manuscript");

      const data = await res.json();
      onOpenChange(false);

      // If "Start from outline" selected, go to outline page
      if (startingContent === "outline") {
        router.push("/writing/outline");
      } else {
        // Navigate to the editor for the new manuscript
        router.push(`/writing/${data.id}`);
      }
    } catch {
      // Just close on error for now
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    setTitle("");
    setBookType("book");
    setStartingContent("blank");
    setTitleError(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("newManuscript.modalTitle")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Title */}
          <div className="space-y-1.5">
            <label htmlFor="ms-title" className="text-sm font-medium text-foreground">
              {t("newManuscript.titleLabel")} *
            </label>
            <input
              id="ms-title"
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (titleError) setTitleError(false);
              }}
              placeholder={t("newManuscript.titlePlaceholder")}
              className={cn(
                "w-full rounded-md border px-3 py-2 text-sm bg-background text-foreground",
                "placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary",
                titleError && "border-red-500 focus:ring-red-500"
              )}
              autoFocus
            />
            {titleError && (
              <p className="text-xs text-red-500">{t("newManuscript.titleRequired")}</p>
            )}
          </div>

          {/* Book Type */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              {t("newManuscript.bookType")}
            </label>
            <div className="flex gap-3">
              {(["book", "series", "short_story"] as BookType[]).map((type) => {
                const labelKey = type === "book" ? "typeBook" : type === "series" ? "typeSeries" : "typeShortStory";
                return (
                  <label key={type} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="bookType"
                      value={type}
                      checked={bookType === type}
                      onChange={() => setBookType(type)}
                      className="h-4 w-4 text-primary"
                    />
                    <span className="text-sm">{t(`newManuscript.${labelKey}`)}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Starting Content */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              {t("newManuscript.startingContent")}
            </label>
            <div className="space-y-2">
              {(["blank", "import", "outline"] as StartingContent[]).map((option) => {
                const labelKey = option === "blank" ? "blankManuscript" : option === "import" ? "importFile" : "fromOutline";
                return (
                  <label key={option} className={cn(
                    "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                    startingContent === option ? "border-primary bg-primary/5" : "hover:bg-accent/50"
                  )}>
                    <input
                      type="radio"
                      name="startingContent"
                      value={option}
                      checked={startingContent === option}
                      onChange={() => setStartingContent(option)}
                      className="h-4 w-4 text-primary"
                    />
                    <span className="text-sm">{t(`newManuscript.${labelKey}`)}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Import file zone (shown when "import" is selected) */}
          {startingContent === "import" && (
            <div className="rounded-md border-2 border-dashed p-6 text-center">
              <p className="text-sm text-muted-foreground">
                Drop a file here or click to browse
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Accepts: DOCX, EPUB, TXT, MD
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" onClick={handleClose} disabled={isCreating}>
            {t("newManuscript.cancel")}
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            {isCreating ? t("newManuscript.creating") : t("newManuscript.createButton")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
