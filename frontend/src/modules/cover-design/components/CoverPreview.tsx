"use client";

import { Download, ImageIcon } from "lucide-react";
import type { Cover } from "../types";

interface CoverPreviewProps {
  cover: Cover;
  onDownload?: () => void;
}

export function CoverPreview({ cover, onDownload }: CoverPreviewProps) {
  const handleDownload = async () => {
    if (!cover.image_url) return;

    if (onDownload) {
      onDownload();
    } else {
      // Default download behavior
      const link = document.createElement("a");
      link.href = cover.image_url;
      link.download = `${cover.title.replace(/\s+/g, "_")}_cover.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const dimensionsText = cover.dimensions
    ? `${cover.dimensions.width_px} × ${cover.dimensions.height_px}px @ ${cover.dimensions.dpi} DPI`
    : "Dimensions not available";

  return (
    <div className="space-y-6">
      {/* Cover image */}
      <div className="relative rounded-lg overflow-hidden border bg-muted">
        <div className="aspect-[2/3] flex items-center justify-center">
          {cover.image_url ? (
            <img
              src={cover.image_url}
              alt={cover.title}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="text-muted-foreground">
              <ImageIcon className="h-24 w-24" />
            </div>
          )}
        </div>
      </div>

      {/* Cover details */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold">{cover.title}</h2>
          {cover.subtitle && (
            <p className="text-lg text-muted-foreground mt-1">
              {cover.subtitle}
            </p>
          )}
          <p className="text-sm text-muted-foreground mt-2">
            by {cover.author_name}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Genre:</span>{" "}
            <span className="capitalize text-muted-foreground">
              {cover.genre.replace("-", " ")}
            </span>
          </div>
          <div>
            <span className="font-medium">Platform:</span>{" "}
            <span className="capitalize text-muted-foreground">
              {cover.platform.replace("-", " ")}
            </span>
          </div>
          <div className="col-span-2">
            <span className="font-medium">Dimensions:</span>{" "}
            <span className="text-muted-foreground">{dimensionsText}</span>
          </div>
        </div>

        {cover.prompt_used && (
          <div>
            <h3 className="text-sm font-medium mb-2">AI Prompt Used</h3>
            <p className="text-xs text-muted-foreground p-3 bg-muted rounded-lg">
              {cover.prompt_used}
            </p>
          </div>
        )}

        {/* Download button */}
        {cover.image_url && (
          <button
            onClick={handleDownload}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium transition-colors"
          >
            <Download className="h-4 w-4" />
            Download Cover
          </button>
        )}
      </div>
    </div>
  );
}
