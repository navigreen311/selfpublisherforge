"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, ChevronUp, ChevronDown, Copy, Check, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useGenerateStandaloneOutline, StandaloneOutlineResponse } from "@/modules/writing/hooks";
import { useProjects, useUpdateProject } from "@/modules/projects/hooks";
import { toast } from "sonner";

const GENRES = [
  "Fiction", "Non-Fiction", "Romance", "Mystery", "Sci-Fi",
  "Fantasy", "Self-Help", "Business", "Biography", "Children", "Other",
];

const TONES = [
  { value: "commercial", label: "Commercial" },
  { value: "literary", label: "Literary" },
  { value: "casual", label: "Casual" },
  { value: "formal", label: "Formal" },
];

const NO_PROJECT = "__none__";

export default function OutlineGeneratorPage() {
  const [title, setTitle] = React.useState("");
  const [genre, setGenre] = React.useState("Fiction");
  const [audience, setAudience] = React.useState("");
  const [numChapters, setNumChapters] = React.useState(12);
  const [premise, setPremise] = React.useState("");
  const [tone, setTone] = React.useState("commercial");
  const [result, setResult] = React.useState<StandaloneOutlineResponse | null>(null);
  const [copied, setCopied] = React.useState(false);
  const [selectedProjectId, setSelectedProjectId] = React.useState<string>(NO_PROJECT);
  const [savedToProject, setSavedToProject] = React.useState(false);

  const generateMutation = useGenerateStandaloneOutline();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const updateProjectMutation = useUpdateProject();

  const handleGenerate = async () => {
    if (!title.trim()) {
      toast.error("Please enter a book title");
      return;
    }
    // Reset save state when generating a new outline
    setSavedToProject(false);
    try {
      const data = await generateMutation.mutateAsync({
        book_title: title,
        genre,
        target_audience: audience || undefined,
        num_chapters: numChapters,
        premise: premise || undefined,
        tone,
      });
      setResult(data);
    } catch {
      toast.error("Failed to generate outline. Please try again.");
    }
  };

  const handleSaveToProject = async () => {
    if (!result) return;
    if (selectedProjectId === NO_PROJECT) {
      toast.error("Please select a project first");
      return;
    }
    try {
      await updateProjectMutation.mutateAsync({
        id: selectedProjectId,
        data: {
          settings: {
            outline: {
              book_title: result.book_title,
              genre: result.genre,
              total_chapters: result.total_chapters,
              synopsis: result.synopsis,
              chapters: result.chapters,
              saved_at: new Date().toISOString(),
            },
          },
        },
      });
      setSavedToProject(true);
      const project = projects?.find((p) => p.id === selectedProjectId);
      toast.success(
        `Outline saved to "${project?.title || "project"}" successfully`
      );
    } catch {
      toast.error("Failed to save outline to project. Please try again.");
    }
  };

  const moveChapter = (index: number, direction: "up" | "down") => {
    if (!result) return;
    const chapters = [...result.chapters];
    const target = direction === "up" ? index - 1 : index + 1;
    if (target < 0 || target >= chapters.length) return;
    [chapters[index], chapters[target]] = [chapters[target], chapters[index]];
    // Re-number chapters
    const renumbered = chapters.map((ch, i) => ({ ...ch, chapter_number: i + 1 }));
    setResult({ ...result, chapters: renumbered, total_chapters: renumbered.length });
    // Reset saved state since the outline was modified
    setSavedToProject(false);
  };

  const exportMarkdown = () => {
    if (!result) return;
    let md = `# ${result.book_title}\n\n`;
    md += `**Genre:** ${result.genre}\n\n`;
    md += `## Synopsis\n\n${result.synopsis}\n\n`;
    md += `## Chapters\n\n`;
    for (const ch of result.chapters) {
      md += `### Chapter ${ch.chapter_number}: ${ch.title}\n\n`;
      md += `${ch.description}\n\n`;
      if (ch.key_points.length > 0) {
        md += `**Key Points:**\n`;
        for (const kp of ch.key_points) {
          md += `- ${kp}\n`;
        }
        md += `\n`;
      }
      md += `*Estimated words: ${ch.estimated_word_count.toLocaleString()}*\n\n`;
    }
    navigator.clipboard.writeText(md);
    setCopied(true);
    toast.success("Outline copied to clipboard as Markdown");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/writing">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Outline Generator</h1>
          <p className="text-sm text-muted-foreground">
            Generate a complete book outline with chapter summaries
          </p>
        </div>
      </div>

      {/* Project Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Link to Project</CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label htmlFor="project-selector" className="text-sm font-medium">
              Project (optional)
            </label>
            <p className="text-xs text-muted-foreground mb-2">
              Select a project to save the generated outline to, or leave as standalone.
            </p>
            <Select
              value={selectedProjectId}
              onValueChange={(value) => {
                setSelectedProjectId(value);
                setSavedToProject(false);
              }}
            >
              <SelectTrigger aria-label="Select a project to save outline to">
                <SelectValue placeholder="No project selected" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NO_PROJECT}>None (standalone)</SelectItem>
                {projectsLoading && (
                  <SelectItem value="__loading__" disabled>
                    Loading projects...
                  </SelectItem>
                )}
                {projects?.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.title}
                    {project.status !== "active" ? ` (${project.status})` : ""}
                  </SelectItem>
                ))}
                {!projectsLoading && projects?.length === 0 && (
                  <SelectItem value="__empty__" disabled>
                    No projects found
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Book Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Book Title *</label>
            <Input
              placeholder="Enter your book title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Book title"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Genre</label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger aria-label="Select genre">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((g) => (
                    <SelectItem key={g} value={g}>{g}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Tone</label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger aria-label="Select tone">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TONES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Target Audience</label>
              <Input
                placeholder="e.g. Young adults, business professionals"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                aria-label="Target audience"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Number of Chapters</label>
              <Input
                type="number"
                min={3}
                max={50}
                value={numChapters}
                onChange={(e) => setNumChapters(parseInt(e.target.value) || 12)}
                aria-label="Number of chapters"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Premise / Description</label>
            <textarea
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Describe your book's premise, main themes, or key plot points..."
              value={premise}
              onChange={(e) => setPremise(e.target.value)}
              aria-label="Book premise or description"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generateMutation.isPending || !title.trim()}
            className="w-full sm:w-auto"
            aria-label="Generate book outline"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating Outline...
              </>
            ) : (
              "Generate Outline"
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="text-xl font-semibold">{result.book_title}</h2>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={exportMarkdown}
                aria-label="Export outline as Markdown to clipboard"
              >
                {copied ? (
                  <><Check className="h-4 w-4 mr-1" /> Copied</>
                ) : (
                  <><Copy className="h-4 w-4 mr-1" /> Export as Markdown</>
                )}
              </Button>
              {selectedProjectId !== NO_PROJECT && (
                <Button
                  variant={savedToProject ? "outline" : "default"}
                  size="sm"
                  onClick={handleSaveToProject}
                  disabled={updateProjectMutation.isPending || savedToProject}
                  aria-label={
                    savedToProject
                      ? "Outline already saved to project"
                      : "Save outline to selected project"
                  }
                >
                  {updateProjectMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Saving...
                    </>
                  ) : savedToProject ? (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      Saved to Project
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-1" />
                      Save to Project
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          {selectedProjectId === NO_PROJECT && (
            <p className="text-xs text-muted-foreground italic">
              Tip: Select a project above to save this outline directly to it.
            </p>
          )}

          {result.synopsis && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Synopsis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{result.synopsis}</p>
              </CardContent>
            </Card>
          )}

          <div className="space-y-3">
            {result.chapters.map((ch, index) => (
              <Card key={ch.chapter_number}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h3 className="font-medium">
                        Chapter {ch.chapter_number}: {ch.title}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {ch.description}
                      </p>
                      {ch.key_points.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {ch.key_points.map((kp, ki) => (
                            <li key={ki} className="text-xs text-muted-foreground flex items-start gap-1.5">
                              <span className="text-primary mt-0.5">-</span>
                              {kp}
                            </li>
                          ))}
                        </ul>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        ~{ch.estimated_word_count.toLocaleString()} words
                      </p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveChapter(index, "up")}
                        disabled={index === 0}
                        className="h-7 w-7 p-0"
                        aria-label={`Move chapter ${ch.chapter_number} up`}
                      >
                        <ChevronUp className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveChapter(index, "down")}
                        disabled={index === result.chapters.length - 1}
                        className="h-7 w-7 p-0"
                        aria-label={`Move chapter ${ch.chapter_number} down`}
                      >
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
