"use client";

import { useState } from "react";
import {
  Image as ImageIcon,
  Search,
  Grid,
  List,
  Plus,
  Trash2,
  Check,
  Eye,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { usePhotoReferences, useDeletePhoto } from "../hooks";
import { PhotoUploadDropzone } from "./PhotoUploadDropzone";
import type { PhotoReference, PhotoUsageType } from "@/modules/specialty/types/photo";

const USAGE_TYPE_LABELS: Record<PhotoUsageType, string> = {
  style_reference: "Style",
  composition_reference: "Composition",
  character_reference: "Character",
  background_reference: "Background",
  color_reference: "Color",
  texture_reference: "Texture",
  pose_reference: "Pose",
};

function formatFileSize(bytes?: number): string {
  if (!bytes) return "\u2014";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface PhotoReferencePanelProps {
  bookType?: string;
  bookId?: string;
  selectionMode?: boolean;
  selectedIds?: string[];
  onSelect?: (photo: PhotoReference) => void;
  onDeselect?: (photoId: string) => void;
  maxSelections?: number;
}

export function PhotoReferencePanel({
  bookType,
  bookId,
  selectionMode = false,
  selectedIds = [],
  onSelect,
  onDeselect,
  maxSelections,
}: PhotoReferencePanelProps) {
  const [search, setSearch] = useState("");
  const [usageFilter, setUsageFilter] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [showUpload, setShowUpload] = useState(false);
  const [previewPhoto, setPreviewPhoto] = useState<PhotoReference | null>(null);

  const { data, isLoading } = usePhotoReferences(1, 50, {
    book_type: bookType,
    book_id: bookId,
    usage_type: usageFilter === "all" ? undefined : usageFilter,
    search: search || undefined,
  });

  const deleteMutation = useDeletePhoto();

  const photos = data?.items ?? [];

  const handleToggleSelect = (photo: PhotoReference) => {
    if (!selectionMode) return;
    if (selectedIds.includes(photo.id)) {
      onDeselect?.(photo.id);
    } else {
      if (maxSelections && selectedIds.length >= maxSelections) return;
      onSelect?.(photo);
    }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search photos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={usageFilter} onValueChange={setUsageFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.entries(USAGE_TYPE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex items-center rounded-md border">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8 rounded-r-none"
            onClick={() => setViewMode("grid")}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8 rounded-l-none"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowUpload((v) => !v)}
        >
          {showUpload ? (
            <X className="mr-1 h-4 w-4" />
          ) : (
            <Plus className="mr-1 h-4 w-4" />
          )}
          {showUpload ? "Close" : "Upload"}
        </Button>
        {selectionMode && selectedIds.length > 0 && (
          <Badge variant="secondary">
            {selectedIds.length} selected
            {maxSelections ? ` / ${maxSelections}` : ""}
          </Badge>
        )}
      </div>

      {/* Upload Section */}
      {showUpload && (
        <PhotoUploadDropzone
          bookType={bookType}
          bookId={bookId}
          onUploaded={() => setShowUpload(false)}
        />
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : photos.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <ImageIcon className="mb-3 h-12 w-12 text-muted-foreground" />
          <p className="text-sm font-medium">No photo references yet</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Upload your first photo reference to get started.
          </p>
          {!showUpload && (
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => setShowUpload(true)}
            >
              <Plus className="mr-1 h-4 w-4" />
              Upload Photo
            </Button>
          )}
        </div>
      ) : viewMode === "grid" ? (
        <ScrollArea className="h-[500px]">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {photos.map((photo) => {
              const isSelected = selectedIds.includes(photo.id);
              return (
                <Card
                  key={photo.id}
                  className={cn(
                    "group relative cursor-pointer overflow-hidden transition-all hover:ring-2 hover:ring-primary/50",
                    isSelected && "ring-2 ring-primary",
                  )}
                  onClick={() =>
                    selectionMode
                      ? handleToggleSelect(photo)
                      : setPreviewPhoto(photo)
                  }
                >
                  <CardContent className="p-0">
                    <div className="relative aspect-square">
                      {photo.thumbnail_url || photo.file_url ? (
                        <img
                          src={photo.thumbnail_url || photo.file_url}
                          alt={photo.name}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-muted">
                          <ImageIcon className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}

                      {/* Selection indicator */}
                      {selectionMode && isSelected && (
                        <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Check className="h-4 w-4" />
                        </div>
                      )}

                      {/* Hover overlay */}
                      <div className="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                        <Button
                          variant="secondary"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            setPreviewPhoto(photo);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteMutation.mutate(photo.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="p-2">
                      <p className="truncate text-xs font-medium">
                        {photo.name}
                      </p>
                      <Badge variant="outline" className="mt-1 text-[10px]">
                        {USAGE_TYPE_LABELS[photo.usage_type] ?? photo.usage_type}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      ) : (
        <ScrollArea className="h-[500px]">
          <div className="space-y-1">
            {photos.map((photo) => {
              const isSelected = selectedIds.includes(photo.id);
              return (
                <div
                  key={photo.id}
                  className={cn(
                    "group flex items-center gap-3 rounded-md border p-2 transition-colors hover:bg-accent",
                    isSelected && "border-primary bg-primary/5",
                  )}
                  onClick={() =>
                    selectionMode
                      ? handleToggleSelect(photo)
                      : setPreviewPhoto(photo)
                  }
                >
                  <div className="h-10 w-10 flex-shrink-0 overflow-hidden rounded">
                    {photo.thumbnail_url || photo.file_url ? (
                      <img
                        src={photo.thumbnail_url || photo.file_url}
                        alt={photo.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-muted">
                        <ImageIcon className="h-4 w-4 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium">{photo.name}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="outline" className="text-[10px]">
                        {USAGE_TYPE_LABELS[photo.usage_type] ?? photo.usage_type}
                      </Badge>
                      {photo.width && photo.height && (
                        <span>
                          {photo.width}&times;{photo.height}
                        </span>
                      )}
                      <span>{formatFileSize(photo.file_size_bytes)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    {selectionMode && isSelected && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewPhoto(photo);
                      }}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteMutation.mutate(photo.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}

      {/* Preview Dialog */}
      <Dialog
        open={!!previewPhoto}
        onOpenChange={(open) => !open && setPreviewPhoto(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{previewPhoto?.name}</DialogTitle>
          </DialogHeader>
          {previewPhoto && (
            <div className="space-y-4">
              <div className="overflow-hidden rounded-lg border">
                <img
                  src={previewPhoto.file_url}
                  alt={previewPhoto.name}
                  className="w-full object-contain"
                />
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Type:</span>{" "}
                  <Badge variant="outline">
                    {USAGE_TYPE_LABELS[previewPhoto.usage_type] ??
                      previewPhoto.usage_type}
                  </Badge>
                </div>
                {previewPhoto.width && previewPhoto.height && (
                  <div>
                    <span className="text-muted-foreground">Dimensions:</span>{" "}
                    {previewPhoto.width}&times;{previewPhoto.height}
                  </div>
                )}
                {previewPhoto.file_size_bytes && (
                  <div>
                    <span className="text-muted-foreground">Size:</span>{" "}
                    {formatFileSize(previewPhoto.file_size_bytes)}
                  </div>
                )}
                {previewPhoto.mime_type && (
                  <div>
                    <span className="text-muted-foreground">Format:</span>{" "}
                    {previewPhoto.mime_type}
                  </div>
                )}
                {previewPhoto.description && (
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Description:</span>{" "}
                    {previewPhoto.description}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
