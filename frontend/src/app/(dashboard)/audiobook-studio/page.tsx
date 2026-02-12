"use client";

import { useRouter } from "next/navigation";
import { Plus, Headphones } from "lucide-react";

// ASSUMPTION: AudiobookStudio components and hooks will be provided by the
// audiobook frontend module (VF23/VF24). For now we render a project list page
// that mirrors the cover-design pattern and will integrate once the module lands.

export default function AudiobookStudioPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Headphones className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-2xl font-bold">Audiobook Studio</h1>
        </div>
        <button
          onClick={() => router.push("/audiobook-studio/new")}
          aria-label="Create new audiobook project"
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New Audiobook
        </button>
      </div>

      {/* Description */}
      <p className="text-muted-foreground">
        AI-powered audiobook production studio. Create professional audiobooks
        with multi-provider TTS, SSML narration, voice cloning, and ACX-ready
        mastering.
      </p>

      {/* Placeholder – will be replaced by AudiobookProjectList component */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="border rounded-lg p-6 text-center text-muted-foreground">
          <Headphones className="h-12 w-12 mx-auto mb-4 opacity-40" aria-hidden="true" />
          <p className="font-medium">No audiobook projects yet</p>
          <p className="text-sm mt-1">
            Click &ldquo;New Audiobook&rdquo; to start your first production.
          </p>
        </div>
      </div>
    </div>
  );
}
