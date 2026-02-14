"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProjects } from "@/modules/projects/hooks";
import { useGenerateSocialPosts } from "../hooks";
import type { SocialPlatform } from "../types";

interface SocialPostGeneratorProps {
  onGenerated?: () => void;
}

const PLATFORMS: { value: SocialPlatform; label: string }[] = [
  { value: "instagram", label: "Instagram" },
  { value: "twitter", label: "X / Twitter" },
  { value: "facebook", label: "Facebook" },
  { value: "tiktok", label: "TikTok" },
];

const TONES = ["Engaging", "Professional", "Casual", "Humorous"];

export function SocialPostGenerator({ onGenerated }: SocialPostGeneratorProps) {
  const [selectedPlatforms, setSelectedPlatforms] = useState<SocialPlatform[]>([]);
  const [postsPerWeek, setPostsPerWeek] = useState("3");
  const [durationWeeks, setDurationWeeks] = useState("4");
  const [tone, setTone] = useState("Engaging");
  const [bookId, setBookId] = useState("");

  const { data: projects, isLoading: projectsLoading } = useProjects();
  const generateMutation = useGenerateSocialPosts();

  const togglePlatform = (platform: SocialPlatform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  const handleGenerate = async () => {
    if (!bookId || selectedPlatforms.length === 0) return;

    try {
      await generateMutation.mutateAsync({
        book_id: bookId,
        platforms: selectedPlatforms,
        posts_per_week: parseInt(postsPerWeek, 10),
        duration_weeks: parseInt(durationWeeks, 10),
        tone,
      });
      onGenerated?.();
    } catch {
      // Error handled by hook
    }
  };

  const isValid = bookId && selectedPlatforms.length > 0;

  return (
    <div className="bg-card border rounded-lg p-4 sm:p-6 space-y-4">
      <h3 className="text-lg font-semibold">Generate Social Content</h3>

      {/* Book Selector */}
      <div className="space-y-1.5">
        <Label htmlFor="social-book">Book</Label>
        {projectsLoading ? (
          <div className="h-10 bg-gray-100 rounded-md animate-pulse" />
        ) : (
          <Select value={bookId} onValueChange={setBookId}>
            <SelectTrigger id="social-book">
              <SelectValue placeholder="Select a book" />
            </SelectTrigger>
            <SelectContent>
              {projects && projects.length > 0 ? (
                projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.title}
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="__none" disabled>
                  No books found
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Platform Checkboxes */}
      <div className="space-y-1.5">
        <Label>Platforms</Label>
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map(({ value, label }) => {
            const isSelected = selectedPlatforms.includes(value);
            return (
              <button
                key={value}
                type="button"
                onClick={() => togglePlatform(value)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                  isSelected
                    ? "bg-purple-100 border-purple-300 text-purple-800"
                    : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                }`}
                aria-pressed={isSelected}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Posts per week */}
        <div className="space-y-1.5">
          <Label htmlFor="posts-per-week">Posts per week</Label>
          <Select value={postsPerWeek} onValueChange={setPostsPerWeek}>
            <SelectTrigger id="posts-per-week">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Duration */}
        <div className="space-y-1.5">
          <Label htmlFor="duration-weeks">Duration (weeks)</Label>
          <Select value={durationWeeks} onValueChange={setDurationWeeks}>
            <SelectTrigger id="duration-weeks">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n} week{n > 1 ? "s" : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Tone */}
        <div className="space-y-1.5">
          <Label htmlFor="social-tone">Tone</Label>
          <Select value={tone} onValueChange={setTone}>
            <SelectTrigger id="social-tone">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TONES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Generate Button */}
      <Button
        onClick={handleGenerate}
        disabled={!isValid || generateMutation.isPending}
        className="w-full sm:w-auto"
      >
        {generateMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generating...
          </>
        ) : (
          "Generate Content Calendar"
        )}
      </Button>
    </div>
  );
}
