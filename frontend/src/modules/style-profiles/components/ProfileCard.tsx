"use client";

import Link from "next/link";
import { FileText, Calendar, TrendingUp, Trash2 } from "lucide-react";
import type { ProfileResponse } from "../types";

interface ProfileCardProps {
  profile: ProfileResponse;
  onDelete?: (id: string) => void;
}

export function ProfileCard({ profile, onDelete }: ProfileCardProps) {
  const statusColors = {
    pending: "bg-gray-100 text-gray-700",
    analyzing: "bg-blue-100 text-blue-700",
    ready: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  const statusColor = statusColors[profile.status] || statusColors.pending;

  return (
    <Link
      href={`/style-profiles/${profile.id}`}
      className="block border rounded-lg p-5 bg-card hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <h3 className="font-semibold text-lg line-clamp-1">{profile.name}</h3>
        <span className={`text-xs px-2 py-1 rounded-full shrink-0 ${statusColor}`}>
          {profile.status}
        </span>
      </div>

      {profile.description && (
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {profile.description}
        </p>
      )}

      {profile.genre && (
        <div className="text-xs text-muted-foreground mb-4">
          <span className="font-medium">Genre:</span> {profile.genre}
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="flex items-center gap-1.5 text-sm">
          <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <div>
            <div className="text-xs text-muted-foreground">Samples</div>
            <div className="font-semibold">{profile.sample_count}</div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-sm">
          <TrendingUp className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <div>
            <div className="text-xs text-muted-foreground">Words</div>
            <div className="font-semibold">{profile.word_count.toLocaleString()}</div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-sm">
          <div className="h-4 w-4 flex items-center justify-center text-muted-foreground" aria-hidden="true">
            %
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Confidence</div>
            <div className="font-semibold">{Math.round(profile.confidence * 100)}%</div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t">
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
          <span>
            Updated {new Date(profile.updated_at).toLocaleDateString()}
          </span>
        </div>
        {onDelete && (
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDelete(profile.id);
            }}
            className="p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-colors"
            aria-label={`Delete ${profile.name}`}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </Link>
  );
}
