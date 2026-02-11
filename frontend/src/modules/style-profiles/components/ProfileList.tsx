"use client";

import { ProfileCard } from "./ProfileCard";
import type { ProfileResponse } from "../types";
import { Skeleton } from "@/components/ui/skeleton";

interface ProfileListProps {
  profiles: ProfileResponse[];
  isLoading?: boolean;
}

export function ProfileList({ profiles, isLoading }: ProfileListProps) {
  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        aria-label="Loading style profiles"
      >
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-56" />
        ))}
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-muted-foreground/30" aria-hidden="true" />
        <h3 className="mt-4 text-lg font-medium">No style profiles yet</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Create your first style profile to start analyzing writing styles.
        </p>
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      role="list"
      aria-label="Style profiles"
    >
      {profiles.map((profile) => (
        <div key={profile.id} role="listitem">
          <ProfileCard profile={profile} />
        </div>
      ))}
    </div>
  );
}

// Import for the empty state icon
import { FileText } from "lucide-react";
