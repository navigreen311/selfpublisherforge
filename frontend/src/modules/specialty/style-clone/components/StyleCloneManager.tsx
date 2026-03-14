"use client";

import { useState } from "react";
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
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  useStyleClones,
  useDeleteStyleClone,
  useAnalyzeStyle,
  useTestGenerate,
  useCheckDrift,
  useSetDefault,
} from "../hooks";
import { StyleCloneCreator } from "./StyleCloneCreator";
import type { StyleCloneProfile } from "@/modules/specialty/types/style-clone";

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
    if (!confirm("Delete style profile?")) return;
    deleteMutation.mutate(profile.id, { onSuccess: onDeleted });
  };

  const images = profile.reference_image_urls ?? [];

  return (
    <Card className="overflow-hidden hover:ring-2 hover:ring-primary/50 transition-all">
      <div className="grid grid-cols-2 aspect-square">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-muted flex items-center justify-center overflow-hidden"
          >
            {images[i] ? (
              <img
                src={images[i]}
                alt={"Reference " + (i + 1)}
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
          <DriftBadge score={profile.drift_score} />
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

export function StyleCloneManager() {
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const filters = {
    ...(search && { search }),
  };

  const { data, isLoading } = useStyleClones(1, 50, filters);
  const profiles = data?.items ?? [];

  return (
    <div className="space-y-6">
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

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search style profiles..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="overflow-hidden animate-pulse">
              <div className="aspect-square bg-muted" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : profiles.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              onDeleted={() => {}}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <Palette className="h-12 w-12 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">
            No style profiles yet
          </h3>
          <p className="text-muted-foreground max-w-md mb-6">
            Create your first style profile by uploading reference images.
          </p>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Your First Style Profile
          </Button>
        </div>
      )}
    </div>
  );
}
