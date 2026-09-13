"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
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
import { useCreateProject } from "@/modules/projects/hooks";
import { z } from "zod";
import { validateForm } from "@/lib/validation";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const manuscriptSchema = z.object({
  title: z
    .string()
    .min(2, "Title must be at least 2 characters")
    .max(100, "Title must be at most 100 characters"),
  genre: z.string().optional(),
  description: z
    .string()
    .max(2000, "Description must be at most 2000 characters")
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
  "Self-Help",
  "Business",
  "Biography",
  "Children",
  "Other",
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function NewManuscriptPage() {
  const t = useTranslations("writing");
  const router = useRouter();
  const createProject = useCreateProject();
  const [title, setTitle] = React.useState("");
  const [genre, setGenre] = React.useState("");
  const [description, setDescription] = React.useState("");

  // Track which fields have been touched (blurred) for inline validation
  const [touched, setTouched] = React.useState<Record<string, boolean>>({});
  // Track whether the user has attempted to submit
  const [submitAttempted, setSubmitAttempted] = React.useState(false);

  const markTouched = React.useCallback((field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }, []);

  // Validate current form data against the schema
  const formData = React.useMemo(
    () => ({
      title: title.trim(),
      genre: genre || undefined,
      description: description || undefined,
    }),
    [title, genre, description]
  );

  const validation = React.useMemo(
    () => validateForm(manuscriptSchema, formData),
    [formData]
  );

  const errors = validation.errors ?? {};
  const isFormValid = validation.success;

  // Helper: return the error message for a field only if it should be shown
  // (i.e., the field has been touched or a submit was attempted)
  const fieldError = React.useCallback(
    (field: string): string | undefined => {
      if (!errors[field]) return undefined;
      if (touched[field] || submitAttempted) return errors[field];
      return undefined;
    },
    [errors, touched, submitAttempted]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitAttempted(true);

    if (!isFormValid) return;

    try {
      const result = await createProject.mutateAsync({
        title: title.trim(),
        type: "book",
        genre: genre || undefined,
        description: description || undefined,
      });
      toast.success(t("newManuscript.success"));
      router.push(`/writing/${result.id}`);
    } catch {
      toast.error(t("newManuscript.error"));
    }
  };

  const titleError = fieldError("title");
  const descriptionError = fieldError("description");

  const descriptionCharCount = description.length;
  const descriptionNearLimit = descriptionCharCount > 1800;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild aria-label={t("newManuscript.backToStudio")}>
          <Link href="/writing">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("newManuscript.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("newManuscript.subtitle")}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <Card>
          <CardHeader>
            <CardTitle>{t("newManuscript.form.title")}</CardTitle>
            <CardDescription>
              {t("newManuscript.form.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label={t("newManuscript.form.titleLabel")}
              placeholder={t("newManuscript.form.titlePlaceholder")}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => markTouched("title")}
              error={titleError}
              required
              aria-required="true"
              aria-label={t("newManuscript.form.titleLabel")}
            />

            <div className="space-y-1.5">
              <label
                htmlFor="manuscript-genre"
                className="text-sm font-medium"
                id="manuscript-genre-label"
              >
                {t("newManuscript.form.genreLabel")}
              </label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger
                  id="manuscript-genre"
                  aria-label={t("newManuscript.form.genreLabel")}
                  aria-labelledby="manuscript-genre-label"
                >
                  <SelectValue placeholder={t("newManuscript.form.genrePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {genres.map((g) => (
                    <SelectItem key={g} value={g.toLowerCase()}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="manuscript-description" className="text-sm font-medium">
                {t("newManuscript.form.descriptionLabel")}
              </label>
              <Textarea
                id="manuscript-description"
                placeholder={t("newManuscript.form.descriptionPlaceholder")}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onBlur={() => markTouched("description")}
                autoGrow
                className={`min-h-[100px] ${
                  descriptionError
                    ? "border-destructive focus-visible:ring-destructive"
                    : ""
                }`}
                aria-invalid={!!descriptionError}
                aria-describedby={
                  descriptionError
                    ? "manuscript-description-error"
                    : "manuscript-description-hint"
                }
                aria-label={t("newManuscript.form.descriptionLabel")}
                maxLength={2000}
              />
              <div className="flex justify-between items-start">
                <div>
                  {descriptionError && (
                    <p
                      id="manuscript-description-error"
                      className="text-sm text-destructive"
                    >
                      {descriptionError}
                    </p>
                  )}
                </div>
                <p
                  id="manuscript-description-hint"
                  className={`text-xs ${
                    descriptionNearLimit
                      ? "text-destructive"
                      : "text-muted-foreground"
                  }`}
                >
                  {descriptionCharCount}/2000
                </p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" type="button" asChild>
              <Link href="/writing">{t("newManuscript.form.cancel")}</Link>
            </Button>
            <Button
              type="submit"
              disabled={
                (submitAttempted && !isFormValid) || createProject.isPending
              }
              aria-disabled={
                (submitAttempted && !isFormValid) || createProject.isPending
              }
              aria-busy={createProject.isPending}
            >
              {createProject.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("newManuscript.form.creating")}
                </>
              ) : (
                t("newManuscript.form.create")
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
