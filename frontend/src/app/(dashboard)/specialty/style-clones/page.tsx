"use client";

import { useMemo, useState } from "react";
import {
  Palette,
  Plus,
  Search,
  Trash2,
  Eye,
  Wand2,
  AlertTriangle,
  Star,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { EmptyState } from "@/components/shared/empty-state";
import { FilterBar } from "@/modules/specialty/shared/components/FilterBar";
import {
  useStyleClones,
  useDeleteStyleClone,
  useAnalyzeStyle,
  useTestGenerate,
  useCheckDrift,
  useSetDefault,
} from "@/modules/specialty/style-clone/hooks/index";
import { StyleCloneCreator } from "@/modules/specialty/style-clone/components/StyleCloneCreator";
import type { StyleCloneProfile } from "@/modules/specialty/types/style-clone";

// ---------------------------------------------------------------------------
// Drift badge helper
// ---------------------------------------------------------------------------

function DriftBadge({ score }: { score?: number }) {
  if (score == null) return null;

  const variant: "outline" | "secondary" | "destructive" =
    score <= 0.3 ? "outline" : score <= 0.6 ? "secondary" : "destructive";

  const label =
    score <= 0.3 ? "Low drift" : score <= 0.6 ? "Med drift" : "High drift";

  return (
    <Badge variant={variant} className="text-[10px]">
      <BarChart3 className="h-3 w-3 mr-1" />
      {label} ({(score * 100).toFixed(0)}%)
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Profile Card
// ---------------------------------------------------------------------------

interface ProfileCardProps {
  profile: StyleCloneProfile;
  onDeleted: () => void;
}

function ProfileCard({ profile, onDeleted }: ProfileCardProps) {
  const deleteMutation = useDeleteStyleClone();
  const analyzeMutation = useAnalyzeStyle(profile.id);
  const testMutation = useTestGenerate(profile.id);
  const driftMutation = useCheckDrift(profile.id);
  const defaultMutation = useSetDefault(profile.id);

  const handleDelete = () => {
    if (!confirm(`Delete style profile "${profile.name}"?`)) return;
    deleteMutation.mutate(profile.id, { onSuccess: onDeleted });
  };

  const images = profile.reference_image_urls ?? [];

  return (
    <Card className="overflow-hidden hover:ring-2 hover:ring-primary/50 transition-all">
      {/* Reference image grid (2x2) */}
      <div className="grid grid-cols-2 aspect-square">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-muted flex items-center justify-center overflow-hidden"
          >
            {images[i] ? (
              <img
                src={images[i]}
                alt={`Reference ${i + 1}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <Palette className="h-5 w-5 text-muted-foreground/40" />
            )}
          </div>
        ))}
      </div>

      <CardContent className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-sm truncate">{profile.name}</h3>
          {profile.is_default && (
            <Star className="h-4 w-4 text-yellow-500 shrink-0 fill-yellow-500" />
          )}
        </div>

        {profile.description && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {profile.description}
          </p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {profile.book_type && (
            <Badge variant="outline" className="text-[10px] capitalize">
              {profile.book_type}
            </Badge>
          )}
          <DriftBadge score={profile.drift_score} />
          {!profile.is_active && (
            <Badge variant="secondary" className="text-[10px]">
              Inactive
            </Badge>
          )}
        </div>

        <p className="text-xs text-muted-foreground">
          Used {profile.times_used} time
          {profile.times_used !== 1 ? "s" : ""} &middot;{" "}
          {profile.reference_count} ref image
          {profile.reference_count !== 1 ? "s" : ""}
        </p>

        <div className="flex flex-wrap gap-1.5 pt-1">
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
          >
            <Wand2 className="h-3 w-3 mr-1" />
            Analyze
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
          >
            <Eye className="h-3 w-3 mr-1" />
            Test
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={() => driftMutation.mutate()}
            disabled={driftMutation.isPending}
          >
            <AlertTriangle className="h-3 w-3 mr-1" />
            Drift
          </Button>
          {!profile.is_default && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              onClick={() => defaultMutation.mutate()}
              disabled={defaultMutation.isPending}
            >
              <Star className="h-3 w-3 mr-1" />
              Default
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs text-destructive hover:text-destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StyleClonesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("newest");
  const [dialogOpen, setDialogOpen] = useState(false);

  const filters = {
    ...(search && { search }),
    ...(statusFilter !== "all" && { active_only: statusFilter === "active" }),
  };

  const { data, isLoading, error } = useStyleClones(1, 50, filters);
  const rawProfiles = data?.items ?? [];

  const profiles = useMemo(() => {
    const sorted = [...rawProfiles];
    switch (sortBy) {
      case "oldest":
        sorted.sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        );
        break;
      case "title-asc":
        sorted.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "title-desc":
        sorted.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case "updated":
        sorted.sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        );
        break;
      case "newest":
      case "created":
      default:
        sorted.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
        break;
    }
    return sorted;
  }, [rawProfiles, sortBy]);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <Breadcrumb
        items={[
          { label: "Specialty", href: "/specialty" },
          { label: "Style Profiles" },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Palette className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Style Profiles</h1>
            <p className="text-muted-foreground">
              Clone and manage art styles for consistent illustration generation
            </p>
          </div>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create New
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Style Profile</DialogTitle>
            </DialogHeader>
            <StyleCloneCreator
              onCreated={() => setDialogOpen(false)}
              onCancel={() => setDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filter Bar */}
      <FilterBar
        searchPlaceholder="Search style profiles..."
        searchValue={search}
        onSearchChange={setSearch}
        statusValue={statusFilter}
        onStatusChange={setStatusFilter}
        sortValue={sortBy}
        onSortChange={setSortBy}
      />

      {/* Grid or states */}
      {isLoading && !data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-72 rounded-lg" />
          ))}
        </div>
      ) : error ? (
        <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
          Failed to load style profiles. Please try again.
        </div>
      ) : profiles.length === 0 ? (
        <EmptyState
          icon={Palette}
          title="No style profiles yet"
          description="Upload illustrations to create your first style clone profile. AI will analyze the art style and let you apply it to all your books."
          actionLabel="+ Create Your First Style Profile"
          onAction={() => setDialogOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              onDeleted={() => {}}
            />
          ))}
        </div>
      )}
    </div>
  );
}
