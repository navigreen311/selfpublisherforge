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
import { projectSchema, validateForm } from "@/lib/validation";

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

const PROJECT_TYPES = ["book", "series", "course"] as const;

export default function NewProjectPage() {
  const t = useTranslations("projects");
  const router = useRouter();
  const createProject = useCreateProject();
  const [title, setTitle] = React.useState("");
  const [type, setType] = React.useState("");
  const [genre, setGenre] = React.useState("");
  const [penName, setPenName] = React.useState("");
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
      type: type || undefined,
      genre: genre || undefined,
      description: description || undefined,
    }),
    [title, type, genre, description]
  );

  const validation = React.useMemo(
    () => validateForm(projectSchema, formData),
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
        type: type as "book" | "series" | "course",
        genre: genre || undefined,
        pen_name: penName || undefined,
        description: description || undefined,
      });
      toast.success(t("new.messages.success"));
      router.push(`/projects/${result.id}`);
    } catch {
      toast.error(t("new.messages.error"));
    }
  };

  const titleError = fieldError("title");
  const typeError = fieldError("type");
  const descriptionError = fieldError("description");

  const descriptionCharCount = description.length;
  const descriptionNearLimit = descriptionCharCount > 1800;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild aria-label={t("new.backToProjects")}>
          <Link href="/projects">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("new.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("new.subtitle")}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <Card>
          <CardHeader>
            <CardTitle>{t("new.form.title")}</CardTitle>
            <CardDescription>
              {t("new.form.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label={t("new.form.projectTitle")}
              placeholder={t("new.form.projectTitlePlaceholder")}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => markTouched("title")}
              error={titleError}
              required
              aria-required="true"
            />

            <div className="space-y-1.5">
              <label
                htmlFor="project-type"
                className="text-sm font-medium"
                id="project-type-label"
              >
                {t("new.form.projectType")}
              </label>
              <Select
                value={type}
                onValueChange={(value) => {
                  setType(value);
                  markTouched("type");
                }}
                required
              >
                <SelectTrigger
                  id="project-type"
                  className={typeError ? "border-destructive focus:ring-destructive" : ""}
                  aria-invalid={!!typeError}
                  aria-describedby={typeError ? "project-type-error" : undefined}
                  aria-required="true"
                  aria-labelledby="project-type-label"
                  onBlur={() => markTouched("type")}
                >
                  <SelectValue placeholder={t("new.form.projectTypePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {PROJECT_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {typeError && (
                <p id="project-type-error" className="text-sm text-destructive">
                  {typeError}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <label htmlFor="project-genre" className="text-sm font-medium">
                {t("new.form.genre")}
              </label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger id="project-genre">
                  <SelectValue placeholder={t("new.form.genrePlaceholder")} />
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

            <Input
              label={t("new.form.penName")}
              placeholder={t("new.form.penNamePlaceholder")}
              value={penName}
              onChange={(e) => setPenName(e.target.value)}
              helperText={t("new.form.penNameHelp")}
            />

            <div className="space-y-1.5">
              <label htmlFor="project-description" className="text-sm font-medium">
                {t("new.form.description")}
              </label>
              <Textarea
                id="project-description"
                placeholder={t("new.form.descriptionPlaceholder")}
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
                    ? "project-description-error"
                    : "project-description-hint"
                }
                maxLength={2000}
              />
              <div className="flex justify-between items-start">
                <div>
                  {descriptionError && (
                    <p
                      id="project-description-error"
                      className="text-sm text-destructive"
                    >
                      {descriptionError}
                    </p>
                  )}
                </div>
                <p
                  id="project-description-hint"
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
              <Link href="/projects">{t("new.form.cancel")}</Link>
            </Button>
            <Button
              type="submit"
              disabled={
                (submitAttempted && !isFormValid) || createProject.isPending
              }
              aria-disabled={
                (submitAttempted && !isFormValid) || createProject.isPending
              }
            >
              {createProject.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("new.form.creating")}
                </>
              ) : (
                t("new.form.create")
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
