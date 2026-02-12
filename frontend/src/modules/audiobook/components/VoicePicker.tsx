"use client";

import { useState, useCallback, useRef } from "react";
import {
  Play,
  Square,
  Search,
  Mic,
  Upload,
  User,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type VoiceGender = "male" | "female" | "neutral";
export type VoiceProvider = "self-hosted" | "premium";
export type VoiceCostTier = "$" | "$$" | "$$$";

export interface Voice {
  id: string;
  name: string;
  gender: VoiceGender;
  accent: string;
  provider: VoiceProvider;
  cost_tier: VoiceCostTier;
  sample_url: string | null;
  preview_endpoint?: string;
}

export interface VoicePickerProps {
  selectedVoiceId?: string;
  onSelect: (voiceId: string) => void;
  voices: Voice[];
  isLoading: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GENDER_OPTIONS: { value: VoiceGender | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "neutral", label: "Neutral" },
];

const PROVIDER_OPTIONS: { value: VoiceProvider | "all"; label: string }[] = [
  { value: "all", label: "All Providers" },
  { value: "self-hosted", label: "Self-Hosted" },
  { value: "premium", label: "Premium" },
];

const COST_TIER_OPTIONS: { value: VoiceCostTier | "all"; label: string }[] = [
  { value: "all", label: "Any Price" },
  { value: "$", label: "$" },
  { value: "$$", label: "$$" },
  { value: "$$$", label: "$$$" },
];

const providerBadgeStyles: Record<VoiceProvider, string> = {
  "self-hosted": "bg-blue-100 text-blue-800",
  premium: "bg-purple-100 text-purple-800",
};

const genderIcons: Record<VoiceGender, string> = {
  male: "M",
  female: "F",
  neutral: "N",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function VoicePicker({
  selectedVoiceId,
  onSelect,
  voices,
  isLoading,
}: VoicePickerProps) {
  const [search, setSearch] = useState("");
  const [genderFilter, setGenderFilter] = useState<VoiceGender | "all">("all");
  const [accentFilter, setAccentFilter] = useState<string>("all");
  const [providerFilter, setProviderFilter] = useState<VoiceProvider | "all">("all");
  const [costFilter, setCostFilter] = useState<VoiceCostTier | "all">("all");
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [previewText, setPreviewText] = useState(
    "The quick brown fox jumps over the lazy dog."
  );
  const [cloneModalOpen, setCloneModalOpen] = useState(false);
  const [cloneFile, setCloneFile] = useState<File | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Derive unique accents from voice list
  const accentOptions = Array.from(new Set(voices.map((v) => v.accent))).sort();

  const filteredVoices = useCallback(() => {
    let result = voices;

    if (genderFilter !== "all") {
      result = result.filter((v) => v.gender === genderFilter);
    }
    if (accentFilter !== "all") {
      result = result.filter((v) => v.accent === accentFilter);
    }
    if (providerFilter !== "all") {
      result = result.filter((v) => v.provider === providerFilter);
    }
    if (costFilter !== "all") {
      result = result.filter((v) => v.cost_tier === costFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((v) => v.name.toLowerCase().includes(q));
    }

    return result;
  }, [voices, genderFilter, accentFilter, providerFilter, costFilter, search]);

  const displayed = filteredVoices();

  const handlePlaySample = (voice: Voice) => {
    if (playingVoiceId === voice.id) {
      // Stop playing
      audioRef.current?.pause();
      audioRef.current = null;
      setPlayingVoiceId(null);
      return;
    }

    // Stop any current playback
    audioRef.current?.pause();
    audioRef.current = null;

    if (!voice.sample_url) return;

    const audio = new Audio(voice.sample_url);
    audio.onended = () => setPlayingVoiceId(null);
    audio.play();
    audioRef.current = audio;
    setPlayingVoiceId(voice.id);
  };

  const handleCloneFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setCloneFile(file);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
          aria-label="Loading voices"
        >
          {[...Array(8)].map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="h-40 w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search & Filters */}
      <div className="flex flex-col gap-3">
        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search voices by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border rounded-lg pl-10 pr-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            aria-label="Search voices"
          />
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap gap-3 items-center">
          {/* Gender filter */}
          <div className="flex gap-1" role="radiogroup" aria-label="Filter by gender">
            {GENDER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setGenderFilter(opt.value)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-md border transition-colors",
                  genderFilter === opt.value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background hover:bg-accent border-input"
                )}
                aria-pressed={genderFilter === opt.value}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Accent dropdown */}
          <select
            value={accentFilter}
            onChange={(e) => setAccentFilter(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            aria-label="Filter by accent"
          >
            <option value="all">All Accents</option>
            {accentOptions.map((accent) => (
              <option key={accent} value={accent}>
                {accent}
              </option>
            ))}
          </select>

          {/* Provider toggle */}
          <select
            value={providerFilter}
            onChange={(e) => setProviderFilter(e.target.value as VoiceProvider | "all")}
            className="border rounded-lg px-3 py-1.5 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            aria-label="Filter by provider"
          >
            {PROVIDER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Price tier */}
          <select
            value={costFilter}
            onChange={(e) => setCostFilter(e.target.value as VoiceCostTier | "all")}
            className="border rounded-lg px-3 py-1.5 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            aria-label="Filter by price tier"
          >
            {COST_TIER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Clone My Voice */}
          <Dialog open={cloneModalOpen} onOpenChange={setCloneModalOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5">
                <Mic className="h-3.5 w-3.5" />
                Clone My Voice
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Clone Your Voice</DialogTitle>
                <DialogDescription>
                  Upload an audio file of your voice (minimum 3 minutes) to create
                  a custom voice clone.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="border-2 border-dashed rounded-lg p-6 text-center space-y-3">
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
                  <div>
                    <label
                      htmlFor="voice-clone-upload"
                      className="text-sm font-medium text-primary cursor-pointer hover:underline"
                    >
                      Choose audio file
                    </label>
                    <input
                      id="voice-clone-upload"
                      type="file"
                      accept="audio/*"
                      className="hidden"
                      onChange={handleCloneFileChange}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      MP3, WAV, M4A &mdash; minimum 3 minutes
                    </p>
                  </div>
                  {cloneFile && (
                    <div className="flex items-center gap-2 justify-center text-sm">
                      <span className="truncate max-w-[200px]">{cloneFile.name}</span>
                      <button
                        onClick={() => setCloneFile(null)}
                        className="text-muted-foreground hover:text-foreground"
                        aria-label="Remove file"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setCloneModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button disabled={!cloneFile}>Upload &amp; Clone</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Preview text input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={previewText}
          onChange={(e) => setPreviewText(e.target.value)}
          placeholder="Enter text to preview..."
          className="flex-1 border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          aria-label="Preview text"
        />
        <Button variant="secondary" size="sm" disabled={!selectedVoiceId}>
          Preview
        </Button>
      </div>

      {/* Results count */}
      <p className="text-sm text-muted-foreground">
        {displayed.length} voice{displayed.length !== 1 ? "s" : ""} found
      </p>

      {/* Voice grid */}
      {displayed.length > 0 ? (
        <div
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
          role="list"
          aria-label="Available voices"
        >
          {displayed.map((voice) => {
            const isSelected = selectedVoiceId === voice.id;
            const isPlaying = playingVoiceId === voice.id;

            return (
              <button
                key={voice.id}
                onClick={() => onSelect(voice.id)}
                role="listitem"
                className={cn(
                  "text-left border rounded-lg p-4 transition-all bg-card space-y-3",
                  isSelected
                    ? "ring-2 ring-primary shadow-lg border-primary"
                    : "hover:shadow-md hover:border-primary/30"
                )}
                aria-pressed={isSelected}
                aria-label={`Select voice ${voice.name}`}
              >
                {/* Header: name + gender icon */}
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-sm truncate">{voice.name}</h3>
                  <span
                    className="flex items-center justify-center h-6 w-6 rounded-full bg-secondary text-secondary-foreground text-[10px] font-bold"
                    title={voice.gender}
                  >
                    {genderIcons[voice.gender]}
                  </span>
                </div>

                {/* Accent */}
                <p className="text-xs text-muted-foreground">{voice.accent}</p>

                {/* Provider + Cost */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={cn(
                      "text-[10px] px-2 py-0.5 rounded-full font-medium",
                      providerBadgeStyles[voice.provider]
                    )}
                  >
                    {voice.provider === "self-hosted" ? "Self-Hosted" : "Premium"}
                  </span>
                  <Badge variant="outline" className="text-[10px] px-1.5">
                    {voice.cost_tier}
                  </Badge>
                </div>

                {/* Play sample button */}
                <div
                  className="pt-1"
                  onClick={(e) => e.stopPropagation()}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") e.stopPropagation();
                  }}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePlaySample(voice);
                    }}
                    disabled={!voice.sample_url}
                    className={cn(
                      "flex items-center gap-1.5 text-xs font-medium transition-colors",
                      voice.sample_url
                        ? "text-primary hover:text-primary/80"
                        : "text-muted-foreground cursor-not-allowed"
                    )}
                    aria-label={
                      isPlaying
                        ? `Stop sample for ${voice.name}`
                        : `Play sample for ${voice.name}`
                    }
                  >
                    {isPlaying ? (
                      <Square className="h-3.5 w-3.5" />
                    ) : (
                      <Play className="h-3.5 w-3.5" />
                    )}
                    {isPlaying ? "Stop" : "Play Sample"}
                  </button>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <User className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
          <p className="text-muted-foreground">
            No voices match your filters. Try adjusting your criteria.
          </p>
        </div>
      )}
    </div>
  );
}
