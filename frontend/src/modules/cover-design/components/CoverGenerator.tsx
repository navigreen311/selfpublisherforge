"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { useGenerateCover } from "../hooks";
import type { CoverGenre, CoverPlatform } from "../types";

interface CoverGeneratorProps {
  bookId?: string;
  onSuccess?: (coverId: string) => void;
}

const GENRE_OPTIONS: { value: CoverGenre; label: string }[] = [
  { value: "romance", label: "Romance" },
  { value: "thriller", label: "Thriller" },
  { value: "mystery", label: "Mystery" },
  { value: "sci-fi", label: "Sci-Fi" },
  { value: "fantasy", label: "Fantasy" },
  { value: "horror", label: "Horror" },
  { value: "literary-fiction", label: "Literary Fiction" },
  { value: "nonfiction", label: "Non-Fiction" },
  { value: "self-help", label: "Self-Help" },
  { value: "business", label: "Business" },
  { value: "childrens", label: "Children's" },
  { value: "young-adult", label: "Young Adult" },
  { value: "memoir", label: "Memoir" },
  { value: "cookbook", label: "Cookbook" },
  { value: "other", label: "Other" },
];

const PLATFORM_OPTIONS: { value: CoverPlatform; label: string }[] = [
  { value: "amazon-kdp", label: "Amazon KDP" },
  { value: "ingram-spark", label: "IngramSpark" },
  { value: "barnes-noble", label: "Barnes & Noble Press" },
  { value: "apple-books", label: "Apple Books" },
  { value: "google-play", label: "Google Play Books" },
  { value: "custom", label: "Custom" },
];

export function CoverGenerator({ bookId, onSuccess }: CoverGeneratorProps) {
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [genre, setGenre] = useState<CoverGenre>("fantasy");
  const [mood, setMood] = useState("");
  const [styleKeywords, setStyleKeywords] = useState("");
  const [colorPalette, setColorPalette] = useState("");
  const [platform, setPlatform] = useState<CoverPlatform>("amazon-kdp");
  const [additionalInstructions, setAdditionalInstructions] = useState("");

  const generateMutation = useGenerateCover();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      book_id: bookId,
      title,
      subtitle: subtitle || undefined,
      author_name: authorName,
      genre,
      mood: mood || undefined,
      style_keywords: styleKeywords
        ? styleKeywords.split(",").map((k) => k.trim())
        : undefined,
      color_palette: colorPalette
        ? colorPalette.split(",").map((c) => c.trim())
        : undefined,
      platform,
      additional_instructions: additionalInstructions || undefined,
    };

    const result = await generateMutation.mutateAsync(payload);
    if (onSuccess && result.id) {
      onSuccess(result.id);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Title */}
        <div className="md:col-span-2">
          <label
            htmlFor="cover-title"
            className="block text-sm font-medium mb-2"
          >
            Book Title <span className="text-red-500">*</span>
          </label>
          <input
            id="cover-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            required
            placeholder="Enter your book title"
          />
        </div>

        {/* Subtitle */}
        <div className="md:col-span-2">
          <label
            htmlFor="cover-subtitle"
            className="block text-sm font-medium mb-2"
          >
            Subtitle (Optional)
          </label>
          <input
            id="cover-subtitle"
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="Enter subtitle if applicable"
          />
        </div>

        {/* Author Name */}
        <div>
          <label
            htmlFor="cover-author"
            className="block text-sm font-medium mb-2"
          >
            Author Name <span className="text-red-500">*</span>
          </label>
          <input
            id="cover-author"
            type="text"
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            required
            placeholder="Your author name"
          />
        </div>

        {/* Genre */}
        <div>
          <label htmlFor="cover-genre" className="block text-sm font-medium mb-2">
            Genre <span className="text-red-500">*</span>
          </label>
          <select
            id="cover-genre"
            value={genre}
            onChange={(e) => setGenre(e.target.value as CoverGenre)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            required
          >
            {GENRE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Mood */}
        <div>
          <label htmlFor="cover-mood" className="block text-sm font-medium mb-2">
            Mood / Tone
          </label>
          <input
            id="cover-mood"
            type="text"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="e.g., dark, mysterious, uplifting"
          />
        </div>

        {/* Platform */}
        <div>
          <label
            htmlFor="cover-platform"
            className="block text-sm font-medium mb-2"
          >
            Publishing Platform
          </label>
          <select
            id="cover-platform"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as CoverPlatform)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            {PLATFORM_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Style Keywords */}
        <div className="md:col-span-2">
          <label
            htmlFor="cover-style"
            className="block text-sm font-medium mb-2"
          >
            Style Keywords
          </label>
          <input
            id="cover-style"
            type="text"
            value={styleKeywords}
            onChange={(e) => setStyleKeywords(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="e.g., minimalist, vintage, modern, illustrated (comma-separated)"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Separate multiple keywords with commas
          </p>
        </div>

        {/* Color Palette */}
        <div className="md:col-span-2">
          <label
            htmlFor="cover-colors"
            className="block text-sm font-medium mb-2"
          >
            Color Palette
          </label>
          <input
            id="cover-colors"
            type="text"
            value={colorPalette}
            onChange={(e) => setColorPalette(e.target.value)}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="e.g., #FF5733, midnight blue, burgundy (comma-separated)"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Hex codes or color names, separated by commas
          </p>
        </div>

        {/* Additional Instructions */}
        <div className="md:col-span-2">
          <label
            htmlFor="cover-instructions"
            className="block text-sm font-medium mb-2"
          >
            Additional Instructions
          </label>
          <textarea
            id="cover-instructions"
            value={additionalInstructions}
            onChange={(e) => setAdditionalInstructions(e.target.value)}
            rows={4}
            className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="Any specific elements, imagery, or layout preferences..."
          />
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={generateMutation.isPending}
          className="flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generate Cover
            </>
          )}
        </button>
      </div>

      {generateMutation.isError && (
        <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
          Failed to generate cover. Please try again.
        </div>
      )}
    </form>
  );
}
