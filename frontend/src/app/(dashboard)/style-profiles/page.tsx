"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Sparkles, Trash2 } from "lucide-react";
import { ProfileList } from "@/modules/style-profiles/components/ProfileList";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { useStyleProfiles, useDeleteProfile } from "@/modules/style-profiles/hooks";
import type { ProfileResponse } from "@/modules/style-profiles/types";

export default function StyleProfilesPage() {
  const { data: profilesData, isPending } = useStyleProfiles();
  const deleteMutation = useDeleteProfile();
  const [deleteTarget, setDeleteTarget] = useState<ProfileResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteRequest = (profile: ProfileResponse) => {
    setDeleteTarget(profile);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  const handleCancelDelete = () => {
    setDeleteTarget(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-2xl font-bold">Style Profiles</h1>
        </div>
        <Link
          href="/style-profiles/new"
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New Profile
        </Link>
      </div>

      {/* Description */}
      <div className="border-l-4 border-primary pl-4 py-2">
        <p className="text-sm text-muted-foreground">
          Analyze and clone writing styles. Create profiles from sample texts to match specific voices and tones.
        </p>
      </div>

      {/* Profile List */}
      <div>
        {!isPending && profilesData && (
          <p className="text-sm text-muted-foreground mb-4">
            {profilesData.total} {profilesData.total === 1 ? "profile" : "profiles"}
          </p>
        )}
        <div className="relative">
          <ProfileList
            profiles={profilesData?.items || []}
            isLoading={isPending}
          />
          {/* Delete buttons overlay */}
          {profilesData?.items && profilesData.items.length > 0 && (
            <div className="absolute inset-0 pointer-events-none">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {profilesData.items.map((profile) => (
                  <div key={profile.id} className="relative h-56">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDeleteRequest(profile);
                      }}
                      aria-label={`Delete profile: ${profile.name}`}
                      className="pointer-events-auto absolute top-3 right-3 p-1.5 rounded-md bg-background/80 border opacity-0 hover:opacity-100 focus:opacity-100 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title="Delete Style Profile"
        description={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        loading={isDeleting}
      />
    </div>
  );
}
