"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useChapterVersions, useRestoreChapterVersion } from "@/modules/writing/hooks";
import type { ChapterVersion } from "@/modules/writing/types";
import { formatDistanceToNow } from "date-fns";

interface VersionHistoryModalProps {
  bookId: string;
  chapterId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRestore?: (content: string) => void;
}

export function VersionHistoryModal({
  bookId,
  chapterId,
  open,
  onOpenChange,
  onRestore,
}: VersionHistoryModalProps) {
  const t = useTranslations("writing");
  const [previewVersion, setPreviewVersion] = useState<ChapterVersion | null>(null);
  const [restoring, setRestoring] = useState(false);

  const { data: versions = [] } = useChapterVersions(bookId, chapterId);
  const restoreMutation = useRestoreChapterVersion(bookId, chapterId);

  const handleRestore = async (version: ChapterVersion) => {
    setRestoring(true);
    try {
      const result = await restoreMutation.mutateAsync(version.id);
      onRestore?.(result.content);
      onOpenChange(false);
    } catch {
      // Handle error silently
    } finally {
      setRestoring(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>{t("versionHistory.title")}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-1 py-2">
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No version history available yet.
            </p>
          ) : (
            versions.map((version, idx) => {
              const isCurrent = idx === 0;
              const isPreview = previewVersion?.id === version.id;

              return (
                <div
                  key={version.id}
                  onClick={() => setPreviewVersion(version)}
                  className={cn(
                    "flex items-center justify-between px-4 py-3 rounded-md cursor-pointer transition-colors",
                    isPreview ? "bg-accent" : "hover:bg-accent/50",
                    isCurrent && "border-l-2 border-primary"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      "inline-block h-2.5 w-2.5 rounded-full flex-shrink-0",
                      isCurrent ? "bg-primary" : "bg-muted-foreground/30"
                    )} />
                    <div>
                      <p className="text-sm font-medium">
                        {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {version.word_count.toLocaleString()} {t("versionHistory.words", { count: version.word_count })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isCurrent ? (
                      <span className="text-xs text-primary font-medium">
                        ({t("versionHistory.current")})
                      </span>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRestore(version);
                        }}
                        disabled={restoring}
                      >
                        {restoring ? t("versionHistory.restoring") : t("versionHistory.restore")}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Preview pane */}
        {previewVersion && (
          <div className="border-t pt-3 max-h-48 overflow-y-auto">
            <p className="text-xs font-medium text-muted-foreground mb-2">Preview</p>
            <div
              className="text-sm prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: previewVersion.content || "<p>Empty</p>" }}
            />
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-2">
          {t("versionHistory.preview")}
        </p>
      </DialogContent>
    </Dialog>
  );
}
