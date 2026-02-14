"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { ProfileCard } from "./ProfileCard";
import type { ProfileResponse } from "../types";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type SortOption = "recent" | "name-az" | "oldest";

interface ProfileListProps {
  profiles: ProfileResponse[];
  isLoading: boolean;
  onDelete?: (id: string) => void;
}

export function ProfileList({ profiles, isLoading, onDelete }: ProfileListProps) {
  const [sort, setSort] = useState<SortOption>("recent");

  const sorted = useMemo(() => {
    const copy = [...profiles];
    switch (sort) {
      case "recent":
        return copy.sort(
          (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
      case "name-az":
        return copy.sort((a, b) => a.name.localeCompare(b.name));
      case "oldest":
        return copy.sort(
          (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
        );
    }
  }, [profiles, sort]);

  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        aria-label="Loading style profiles"
      >
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-56 rounded-lg" />
        ))}
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="text-center py-12">
        <Sparkles className="mx-auto h-12 w-12 text-muted-foreground/30" aria-hidden="true" />
        <h3 className="mt-4 text-lg font-medium">No style profiles yet</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Create your first style profile to start analyzing writing styles.
        </p>
        <Button asChild className="mt-6">
          <Link href="/style-profiles/new">Create Style Profile</Link>
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          {profiles.length} {profiles.length === 1 ? "profile" : "profiles"}
        </p>
        <Select value={sort} onValueChange={(v) => setSort(v as SortOption)}>
          <SelectTrigger className="w-[160px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Recent</SelectItem>
            <SelectItem value="name-az">Name A-Z</SelectItem>
            <SelectItem value="oldest">Oldest</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        role="list"
        aria-label="Style profiles"
      >
        {sorted.map((profile) => (
          <div key={profile.id} role="listitem">
            <ProfileCard profile={profile} onDelete={onDelete} />
          </div>
        ))}
      </div>
    </div>
  );
}
