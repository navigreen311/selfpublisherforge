"use client";

import { useState, useCallback, useRef } from "react";
import {
  Upload,
  X,
  Image as ImageIcon,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateStyleClone } from "../hooks";
import type { StyleCloneProfile } from "@/modules/specialty/types/style-clone";

interface StyleCloneCreatorProps {
  onCreated?: (profile: StyleCloneProfile) => void;
  onCancel?: () => void;
}

const BOOK_TYPE_OPTIONS = [
  { value: "all", label: "All Types" },
  { value: "childrens", label: "Children's" },
  { value: "coloring", label: "Coloring" },
  { value: "puzzle", label: "Puzzle" },
  { value: "comic", label: "Comic" },
  { value: "cookbook", label: "Cookbook" },
];

const MIN_IMAGES = 3;
const MAX_IMAGES = 10;

export function StyleCloneCreator({ onCreated, onCancel }: StyleCloneCreatorProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [bookType, setBookType] = useState("all");
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [urlInput, setUrlInput] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const createMutation = useCreateStyleClone();

  const addImageUrl = useCallback(
    (url: string) => {
      const trimmed = url.trim();
      if (trimmed && imageUrls.length < MAX_IMAGES && !imageUrls.includes(trimmed)) {
        setImageUrls((prev) => [...prev, trimmed]);
      }
    },
    [imageUrls],
  );

  const removeImage = useCallback((index: number) => {
    setImageUrls((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleUrlAdd = () => {
    if (urlInput.trim()) {
      addImageUrl(urlInput);
      setUrlInput("");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach((file) => {
      const objectUrl = URL.createObjectURL(file);
      addImageUrl(objectUrl);
    });
    e.target.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    Array.from(files).forEach((file) => {
      if (file.type.startsWith("image/")) {
        const objectUrl = URL.createObjectURL(file);
        addImageUrl(objectUrl);
      }
    });
  };

  const handleSubmit = () => {
    if (!name.trim() || imageUrls.length < MIN_IMAGES) return;
    createMutation.mutate(
      {
        name: name.trim(),
        description: description.trim() || undefined,
        reference_image_urls: imageUrls,
        book_type: bookType === "all" ? undefined : bookType,
      },
      {
        onSuccess: (profile) => {
          onCreated?.(profile);
        },
      },
    );
  };

  const canSubmit = name.trim().length > 0 && imageUrls.length >= MIN_IMAGES;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="style-name">Profile Name *</Label>
        <Input
          id="style-name"
          placeholder="e.g. Watercolor Children's Style"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="style-description">Description</Label>
        <Textarea
          id="style-description"
          placeholder="Describe the art style characteristics..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </div>

      <div className="space-y-2">
        <Label>Book Type</Label>
        <Select value={bookType} onValueChange={setBookType}>
          <SelectTrigger>
            <SelectValue placeholder="Select book type" />
          </SelectTrigger>
          <SelectContent>
            {BOOK_TYPE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-3">
        <Label>
          Reference Images ({imageUrls.length}/{MAX_IMAGES}) — minimum {MIN_IMAGES}
        </Label>

        {imageUrls.length > 0 && (
          <div className="grid grid-cols-5 gap-2">
            {imageUrls.map((url, i) => (
              <div
                key={i}
                className="relative aspect-square rounded-md overflow-hidden border bg-muted group"
              >
                <img
                  src={url}
                  alt={`Reference ${i + 1}`}
                  className="h-full w-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removeImage(i)}
                  className="absolute top-1 right-1 h-5 w-5 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            isDragging
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50"
          }`}
        >
          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground mb-2">
            Drag & drop images here, or
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={imageUrls.length >= MAX_IMAGES}
          >
            <ImageIcon className="h-4 w-4 mr-2" />
            Browse Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Paste image URL..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleUrlAdd();
              }
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={handleUrlAdd}
            disabled={!urlInput.trim() || imageUrls.length >= MAX_IMAGES}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || createMutation.isPending}
        >
          {createMutation.isPending ? "Creating..." : "Create Profile"}
        </Button>
      </div>
    </div>
  );
}
