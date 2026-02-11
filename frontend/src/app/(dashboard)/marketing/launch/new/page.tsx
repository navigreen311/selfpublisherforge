"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Link from "next/link";
import { toast } from "sonner";
import { z } from "zod";
import { validateForm } from "@/lib/validation";
import { useGenerateLaunchPlan } from "@/modules/marketing/hooks";
import { useProjects } from "@/modules/projects/hooks";
import { useTranslations } from "@/hooks/use-translations";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const launchPlanSchema = z.object({
  book_id: z.string().min(1, "Please select a book"),
  book_title: z.string().min(1, "Book title is required"),
  genre: z.string().min(1, "Genre is required"),
  target_audience: z
    .string()
    .min(2, "Target audience must be at least 2 characters")
    .max(500, "Target audience must be at most 500 characters"),
  launch_date: z.string().min(1, "Launch date is required"),
  budget: z
    .number()
    .min(0, "Budget cannot be negative")
    .optional(),
  goals: z
    .array(z.string())
    .optional(),
  additional_context: z
    .string()
    .max(2000, "Additional context must be at most 2000 characters")
    .optional()
    .or(z.literal("")),
});

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const genres = [
  "Fiction",
  "Non-Fiction",
  "Romance",
  "Mystery",
  "Sci-Fi",
  "Fantasy",
  "Thriller",
  "Self-Help",
  "Business",
  "Biography",
  "Children",
  "Young Adult",
  "Horror",
  "Historical Fiction",
  "Other",
];

const channels = [
  "Amazon Ads",
  "Facebook Ads",
  "BookBub",
  "Email Newsletter",
  "Social Media Organic",
  "Blog Tour",
  "Book Reviews",
  "Goodreads",
  "Instagram Ads",
  "TikTok / BookTok",
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function NewLaunchPlanPage() {
  const t = useTranslations("marketing");
  const router = useRouter();
  const generatePlan = useGenerateLaunchPlan();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  const [bookId, setBookId] = React.useState("");
  const [bookTitle, setBookTitle] = React.useState("");
  const [genre, setGenre] = React.useState("");
  const [targetAudience, setTargetAudience] = React.useState("");
  const [launchDate, setLaunchDate] = React.useState("");
  const [budget, setBudget] = React.useState("");
  const [selectedChannels, setSelectedChannels] = React.useState<string[]>([]);
  const [additionalContext, setAdditionalContext] = React.useState("");

  // Track which fields have been touched (blurred) for inline validation
  const [touched, setTouched] = React.useState<Record<string, boolean>>({});
  // Track whether the user has attempted to submit
  const [submitAttempted, setSubmitAttempted] = React.useState(false);

  const markTouched = React.useCallback((field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }, []);

  // When a book is selected, auto-fill title from the project
  const handleBookChange = React.useCallback(
    (value: string) => {
      setBookId(value);
      const project = projects?.find((p) => p.id === value);
      if (project) {
        setBookTitle(project.title);
      }
    },
    [projects],
  );

  const toggleChannel = React.useCallback((channel: string) => {
    setSelectedChannels((prev) =>
      prev.includes(channel)
        ? prev.filter((c) => c !== channel)
        : [...prev, channel],
    );
  }, []);

  // Validate current form data against the schema
  const formData = React.useMemo(
    () => ({
      book_id: bookId,
      book_title: bookTitle.trim(),
      genre: genre,
      target_audience: targetAudience.trim(),
      launch_date: launchDate,
      budget: budget ? Number(budget) : undefined,
      goals: selectedChannels.length > 0 ? selectedChannels : undefined,
      additional_context: additionalContext || undefined,
    }),
    [bookId, bookTitle, genre, targetAudience, launchDate, budget, selectedChannels, additionalContext],
  );

  const validation = React.useMemo(
    () => validateForm(launchPlanSchema, formData),
    [formData],
  );

  const errors = validation.errors ?? {};
  const isFormValid = validation.success;

  // Helper: return the error message for a field only if it should be shown
  const fieldError = React.useCallback(
    (field: string): string | undefined => {
      if (!errors[field]) return undefined;
      if (touched[field] || submitAttempted) return errors[field];
      return undefined;
    },
    [errors, touched, submitAttempted],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitAttempted(true);

    if (!isFormValid) return;

    try {
      const result = await generatePlan.mutateAsync({
        book_id: bookId,
        book_title: bookTitle.trim(),
        genre,
        target_audience: targetAudience.trim(),
        launch_date: launchDate,
        budget: budget ? Number(budget) : undefined,
        goals: selectedChannels.length > 0 ? selectedChannels : undefined,
        additional_context: additionalContext || undefined,
      });
      toast.success(t("newLaunchPlan.generateSuccess"));
      router.push(`/marketing/launch/${result.id}`);
    } catch {
      toast.error(t("newLaunchPlan.generateError"));
    }
  };

  const bookIdError = fieldError("book_id");
  const genreError = fieldError("genre");
  const targetAudienceError = fieldError("target_audience");
  const launchDateError = fieldError("launch_date");
  const budgetError = fieldError("budget");
  const additionalContextError = fieldError("additional_context");

  const contextCharCount = additionalContext.length;
  const contextNearLimit = contextCharCount > 1800;

  // Compute minimum date (today) for the date picker
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild aria-label={t("newLaunchPlan.backToMarketing")}>
          <Link href="/marketing">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("newLaunchPlan.pageTitle")}
          </h1>
          <p className="text-muted-foreground">
            {t("newLaunchPlan.pageSubtitle")}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <Card>
          <CardHeader>
            <CardTitle>{t("newLaunchPlan.cardTitle")}</CardTitle>
            <CardDescription>
              {t("newLaunchPlan.cardDescription")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Book Selection */}
            <div className="space-y-1.5">
              <label
                htmlFor="launch-book"
                className="text-sm font-medium"
                id="launch-book-label"
              >
                {t("newLaunchPlan.bookLabel")} <span className="text-destructive">{t("newLaunchPlan.required")}</span>
              </label>
              {projectsLoading ? (
                <div className="h-10 bg-gray-100 rounded-md animate-pulse" />
              ) : (
                <Select
                  value={bookId}
                  onValueChange={handleBookChange}
                >
                  <SelectTrigger
                    id="launch-book"
                    aria-label={t("newLaunchPlan.bookLabel")}
                    aria-labelledby="launch-book-label"
                    aria-invalid={!!bookIdError}
                    aria-describedby={bookIdError ? "launch-book-error" : undefined}
                  >
                    <SelectValue placeholder={t("newLaunchPlan.bookPlaceholder")} />
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
                        {t("newLaunchPlan.noBooksFound")}
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              )}
              {bookIdError && (
                <p id="launch-book-error" className="text-sm text-destructive">
                  {bookIdError}
                </p>
              )}
            </div>

            {/* Genre */}
            <div className="space-y-1.5">
              <label
                htmlFor="launch-genre"
                className="text-sm font-medium"
                id="launch-genre-label"
              >
                {t("newLaunchPlan.genreLabel")} <span className="text-destructive">{t("newLaunchPlan.required")}</span>
              </label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger
                  id="launch-genre"
                  aria-label={t("newLaunchPlan.genreLabel")}
                  aria-labelledby="launch-genre-label"
                  aria-invalid={!!genreError}
                  aria-describedby={genreError ? "launch-genre-error" : undefined}
                >
                  <SelectValue placeholder={t("newLaunchPlan.genrePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {genres.map((g) => (
                    <SelectItem key={g} value={g.toLowerCase()}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {genreError && (
                <p id="launch-genre-error" className="text-sm text-destructive">
                  {genreError}
                </p>
              )}
            </div>

            {/* Target Audience */}
            <div className="space-y-1.5">
              <label htmlFor="launch-target-audience" className="text-sm font-medium">
                {t("newLaunchPlan.targetAudienceLabel")} <span className="text-destructive">{t("newLaunchPlan.required")}</span>
              </label>
              <Input
                id="launch-target-audience"
                placeholder={t("newLaunchPlan.targetAudiencePlaceholder")}
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                onBlur={() => markTouched("target_audience")}
                aria-label={t("newLaunchPlan.targetAudienceLabel")}
                aria-invalid={!!targetAudienceError}
                aria-describedby={
                  targetAudienceError ? "launch-target-audience-error" : undefined
                }
              />
              {targetAudienceError && (
                <p
                  id="launch-target-audience-error"
                  className="text-sm text-destructive"
                >
                  {targetAudienceError}
                </p>
              )}
            </div>

            {/* Launch Date */}
            <div className="space-y-1.5">
              <label htmlFor="launch-date" className="text-sm font-medium">
                {t("newLaunchPlan.launchDateLabel")} <span className="text-destructive">{t("newLaunchPlan.required")}</span>
              </label>
              <Input
                id="launch-date"
                type="date"
                min={today}
                value={launchDate}
                onChange={(e) => setLaunchDate(e.target.value)}
                onBlur={() => markTouched("launch_date")}
                aria-label={t("newLaunchPlan.launchDateLabel")}
                aria-invalid={!!launchDateError}
                aria-describedby={
                  launchDateError ? "launch-date-error" : undefined
                }
              />
              {launchDateError && (
                <p id="launch-date-error" className="text-sm text-destructive">
                  {launchDateError}
                </p>
              )}
            </div>

            {/* Budget */}
            <div className="space-y-1.5">
              <label htmlFor="launch-budget" className="text-sm font-medium">
                {t("newLaunchPlan.budgetLabel")}
              </label>
              <Input
                id="launch-budget"
                type="number"
                min="0"
                step="1"
                placeholder={t("newLaunchPlan.budgetPlaceholder")}
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                onBlur={() => markTouched("budget")}
                aria-label={t("newLaunchPlan.budgetLabel")}
                aria-invalid={!!budgetError}
                aria-describedby={
                  budgetError ? "launch-budget-error" : "launch-budget-hint"
                }
              />
              {budgetError ? (
                <p id="launch-budget-error" className="text-sm text-destructive">
                  {budgetError}
                </p>
              ) : (
                <p id="launch-budget-hint" className="text-xs text-muted-foreground">
                  {t("newLaunchPlan.budgetHint")}
                </p>
              )}
            </div>

            {/* Channels */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium" id="launch-channels-label">
                {t("newLaunchPlan.channelsLabel")}
              </label>
              <p className="text-xs text-muted-foreground">
                {t("newLaunchPlan.channelsHint")}
              </p>
              <div
                className="flex flex-wrap gap-2 mt-2"
                role="group"
                aria-labelledby="launch-channels-label"
              >
                {channels.map((channel) => {
                  const isSelected = selectedChannels.includes(channel);
                  return (
                    <button
                      key={channel}
                      type="button"
                      onClick={() => toggleChannel(channel)}
                      className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                        isSelected
                          ? "bg-blue-100 border-blue-300 text-blue-800"
                          : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                      }`}
                      aria-pressed={isSelected}
                      aria-label={`${channel} channel`}
                    >
                      {channel}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Additional Context */}
            <div className="space-y-1.5">
              <label htmlFor="launch-context" className="text-sm font-medium">
                {t("newLaunchPlan.contextLabel")}
              </label>
              <Textarea
                id="launch-context"
                placeholder={t("newLaunchPlan.contextPlaceholder")}
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                onBlur={() => markTouched("additional_context")}
                className={`min-h-[100px] ${
                  additionalContextError
                    ? "border-destructive focus-visible:ring-destructive"
                    : ""
                }`}
                aria-invalid={!!additionalContextError}
                aria-describedby={
                  additionalContextError
                    ? "launch-context-error"
                    : "launch-context-hint"
                }
                aria-label="Additional context for launch plan"
                maxLength={2000}
              />
              <div className="flex justify-between items-start">
                <div>
                  {additionalContextError && (
                    <p
                      id="launch-context-error"
                      className="text-sm text-destructive"
                    >
                      {additionalContextError}
                    </p>
                  )}
                </div>
                <p
                  id="launch-context-hint"
                  className={`text-xs ${
                    contextNearLimit
                      ? "text-destructive"
                      : "text-muted-foreground"
                  }`}
                >
                  {t("newLaunchPlan.contextCharCount", { count: contextCharCount })}
                </p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" type="button" asChild>
              <Link href="/marketing">{t("newLaunchPlan.cancel")}</Link>
            </Button>
            <Button
              type="submit"
              disabled={
                (submitAttempted && !isFormValid) || generatePlan.isPending
              }
              aria-disabled={
                (submitAttempted && !isFormValid) || generatePlan.isPending
              }
              aria-label={t("newLaunchPlan.generate")}
            >
              {generatePlan.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("newLaunchPlan.generating")}
                </>
              ) : (
                t("newLaunchPlan.generate")
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
