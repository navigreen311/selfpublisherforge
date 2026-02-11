"use client";

import { useState, useRef, useCallback } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "../hooks";
import { Upload, X } from "lucide-react";
import { toast } from "sonner";

interface AvatarUploadProps {
  currentUrl: string | null;
  onUploadComplete: (url: string) => void;
}

export function AvatarUpload({ currentUrl, onUploadComplete }: AvatarUploadProps) {
  const { data: user } = useCurrentUser();
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentUrl);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get user initials for fallback
  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const handleFileSelect = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // Validate file type
      if (!file.type.startsWith("image/")) {
        toast.error("Please select an image file");
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error("Image must be smaller than 5MB");
        return;
      }

      setIsUploading(true);

      try {
        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = e.target?.result as string;
          setPreviewUrl(dataUrl);
        };
        reader.readAsDataURL(file);

        // In a real implementation, you would upload to a storage service
        // For now, we'll simulate an upload and use a placeholder
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Simulate uploaded URL - in production, this would be the actual uploaded URL
        const uploadedUrl = `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
          user?.name || "User"
        )}`;

        onUploadComplete(uploadedUrl);
        toast.success("Avatar uploaded successfully");
      } catch (error) {
        toast.error("Failed to upload avatar");
        console.error("Upload error:", error);
      } finally {
        setIsUploading(false);
      }
    },
    [user?.name, onUploadComplete]
  );

  const handleRemove = useCallback(() => {
    setPreviewUrl(null);
    onUploadComplete("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [onUploadComplete]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className="flex items-center gap-4">
      <Avatar className="h-20 w-20">
        <AvatarImage src={previewUrl || undefined} alt="Profile picture" />
        <AvatarFallback className="text-lg">{initials}</AvatarFallback>
      </Avatar>

      <div className="flex flex-col gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="Upload avatar image"
        />
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleClick}
            disabled={isUploading}
          >
            <Upload className="h-4 w-4 mr-1.5" />
            {isUploading ? "Uploading..." : "Upload Photo"}
          </Button>
          {previewUrl && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRemove}
              disabled={isUploading}
            >
              <X className="h-4 w-4 mr-1.5" />
              Remove
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          JPG, PNG or GIF. Max 5MB.
        </p>
      </div>
    </div>
  );
}
