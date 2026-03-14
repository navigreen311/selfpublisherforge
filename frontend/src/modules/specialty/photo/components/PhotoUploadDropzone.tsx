"use client";

import { useCallback, useState, useRef } from "react";
import { Upload, Image as ImageIcon, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useUploadPhoto } from "../hooks";
import type { PhotoReference, PhotoUsageType } from "@/modules/specialty/types/photo";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const USAGE_TYPE_OPTIONS: { value: PhotoUsageType; label: string }[] = [
  { value: "style_reference", label: "Style" },
  { value: "composition_reference", label: "Composition" },
  { value: "character_reference", label: "Character" },
  { value: "background_reference", label: "Background" },
  { value: "color_reference", label: "Color" },
  { value: "texture_reference", label: "Texture" },
  { value: "pose_reference", label: "Pose" },
];

interface PhotoUploadDropzoneProps {
  bookType?: string;
  bookId?: string;
  onUploaded?: (photo: PhotoReference) => void;
}

export function PhotoUploadDropzone({
  bookType,
  bookId,
  onUploaded,
}: PhotoUploadDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [usageType, setUsageType] = useState<PhotoUsageType>("style_reference");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadPhoto();

  const validateFile = useCallback((file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return "Invalid file type. Please upload a JPEG, PNG, or WebP image.";
    }
    if (file.size > MAX_FILE_SIZE) {
      return "File is too large. Maximum size is 10MB.";
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      setSelectedFile(file);
      setName(file.name.replace(/\.[^/.]+$/, ""));

      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
    },
    [validateFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleCancel = useCallback(() => {
    setSelectedFile(null);
    setPreview(null);
    setName("");
    setUsageType("style_reference");
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile || !name.trim()) return;

    uploadMutation.mutate(
      {
        file: selectedFile,
        name: name.trim(),
        usage_type: usageType,
        book_type: bookType,
        book_id: bookId,
      },
      {
        onSuccess: (photo) => {
          handleCancel();
          onUploaded?.(photo);
        },
      },
    );
  }, [selectedFile, name, usageType, bookType, bookId, uploadMutation, handleCancel, onUploaded]);

  return (
    <div className="space-y-4">
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
            dragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50",
          )}
        >
          <Upload className="mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm font-medium">
            {dragOver ? "Drop image here" : "Drag & drop an image, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            JPEG, PNG, or WebP up to 10MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(",")}
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      ) : (
        <div className="rounded-lg border p-4">
          <div className="flex gap-4">
            <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden rounded-md border">
              {preview ? (
                <img
                  src={preview}
                  alt="Preview"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-muted">
                  <ImageIcon className="h-8 w-8 text-muted-foreground" />
                </div>
              )}
            </div>
            <div className="flex-1 space-y-3">
              <div>
                <Label htmlFor="photo-name">Name</Label>
                <Input
                  id="photo-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Photo name"
                />
              </div>
              <div>
                <Label>Usage Type</Label>
                <Select
                  value={usageType}
                  onValueChange={(v) => setUsageType(v as PhotoUsageType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {USAGE_TYPE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={uploadMutation.isPending}
            >
              <X className="mr-1 h-4 w-4" />
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleUpload}
              disabled={!name.trim() || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-1 h-4 w-4" />
              )}
              Upload
            </Button>
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
