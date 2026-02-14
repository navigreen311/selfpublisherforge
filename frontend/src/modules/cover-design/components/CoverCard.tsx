"use client";

import Link from "next/link";
import { ImageIcon, Loader2 } from "lucide-react";
import type { Cover } from "../types";

interface CoverCardProps {
  cover: Cover;
}

const statusColors: Partial<Record<Cover["status"], string>> = {
  pending: "bg-yellow-100 text-yellow-800",
  generating: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  draft: "bg-gray-100 text-gray-800",
  active: "bg-green-100 text-green-800",
  edited: "bg-purple-100 text-purple-800",
  exported: "bg-teal-100 text-teal-800",
};

const statusLabels: Partial<Record<Cover["status"], string>> = {
  pending: "Pending",
  generating: "Generating",
  completed: "Ready",
  failed: "Failed",
  draft: "Draft",
  active: "Active",
  edited: "Edited",
  exported: "Exported",
};

export function CoverCard({ cover }: CoverCardProps) {
  const formattedDate = cover.created_at
    ? new Date(cover.created_at).toLocaleDateString()
    : "";

  return (
    <Link
      href={`/cover-design/${cover.id}`}
      className="block border rounded-lg overflow-hidden hover:shadow-lg transition-shadow bg-card"
    >
      {/* Cover image */}
      <div className="aspect-[2/3] bg-muted relative overflow-hidden">
        {cover.status === "generating" && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        {cover.thumbnail_url || cover.image_url ? (
          <img
            src={cover.thumbnail_url || cover.image_url || ""}
            alt={cover.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
            <ImageIcon className="h-12 w-12" />
          </div>
        )}
        <div className="absolute top-2 right-2">
          <span
            className={`text-[10px] px-2 py-1 rounded-full font-medium ${
              statusColors[cover.status]
            }`}
          >
            {statusLabels[cover.status]}
          </span>
        </div>
      </div>

      {/* Cover info */}
      <div className="p-4 space-y-2">
        <div>
          <h3 className="font-semibold text-sm truncate">{cover.title}</h3>
          {cover.subtitle && (
            <p className="text-xs text-muted-foreground truncate">
              {cover.subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="capitalize">{cover.genre.replace("-", " ")}</span>
          <span>{formattedDate}</span>
        </div>

        <div className="text-xs text-muted-foreground truncate">
          by {cover.author_name}
        </div>
      </div>
    </Link>
  );
}
