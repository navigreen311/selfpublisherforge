"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, X, ChevronDown, ChevronUp, Upload } from "lucide-react";
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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GENRES = [
  { value: "fiction", label: "Fiction" },
  { value: "nonfiction", label: "Nonfiction" },
  { value: "romance", label: "Romance" },
  { value: "mystery", label: "Mystery & Thriller" },
  { value: "sciFi", label: "Science Fiction" },
  { value: "fantasy", label: "Fantasy" },
  { value: "selfHelp", label: "Self-Help" },
  { value: "business", label: "Business & Money" },
  { value: "biography", label: "Biography & Memoir" },
  { value: "health", label: "Health & Wellness" },
  { value: "history", label: "History" },
  { value: "childrens", label: "Children's Books" },
  { value: "youngAdult", label: "Young Adult" },
  { value: "horror", label: "Horror" },
  { value: "poetry", label: "Poetry" },
  { value: "other", label: "Other" },
];

const PROJECT_TYPES = ["book", "series", "course"] as const;

const MARKETPLACES = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "d2d", label: "Draft2Digital" },
  { value: "acx", label: "ACX (Audiobook)" },
  { value: "multiple", label: "Multiple Platforms" },
];

const TEMPLATES = [
  { value: "", label: "Blank Project", description: "Start from scratch" },
  { value: "nonfiction", label: "Nonfiction Book", description: "Structured chapters with key takeaways" },
  { value: "novel", label: "Novel / Fiction", description: "Three-act structure with character arcs" },
  { value: "self-help", label: "Self-Help / How-To", description: "Problem-solution framework" },
  { value: "memoir", label: "Memoir", description: "Chronological life story structure" },
  { value: "childrens", label: "Children's Book", description: "Short chapters with illustration notes" },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
  { value: "ko", label: "Korean" },
  { value: "ar", label: "Arabic" },
];

// ---------------------------------------------------------------------------
// Keywords Tag Input
// ---------------------------------------------------------------------------

function KeywordsInput({
  keywords,
  onChange,
  placeholder,
  maxKeywords = 20,
}: {
  keywords: string[];
  onChange: (keywords: string[]) => void;
  placeholder: string;
  maxKeywords?: number;
}) {
  const [inputValue, setInputValue] = React.useState("");

  const addKeyword = (value: string) => {
    const trimmed = value.trim().toLowerCase();
    if (!trimmed || keywords.includes(trimmed) || keywords.length >= maxKeywords) return;
    onChange([...keywords, trimmed]);
    setInputValue("");
  };

  const removeKeyword = (index: number) => {
    onChange(keywords.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addKeyword(inputValue);
    } else if (e.key === "Backspace" && !inputValue && keywords.length > 0) {
      removeKeyword(keywords.length - 1);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5 min-h-[38px] p-2 rounded-md border bg-background">
        {keywords.map((kw, i) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium"
          >
            {kw}
            <button
              type="button"
              onClick={() => removeKeyword(i)}
              className="hover:text-destructive"
              aria-label={`Remove ${kw}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => { if (inputValue) addKeyword(inputValue); }}
          placeholder={keywords.length === 0 ? placeholder : ""}
          className="flex-1 min-w-[120px] bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          disabled={keywords.length >= maxKeywords}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        {keywords.length}/{maxKeywords} keywords
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Template Selector
// ---------------------------------------------------------------------------

function TemplateSelector({
  value,
  onChange,
  t,
}: {
  value: string;
  onChange: (v: string) => void;
  t: (key: string) => string;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {TEMPLATES.map((tmpl) => (
        <button
          key={tmpl.value}
          type="button"
          onClick={() => onChange(tmpl.value)}
          className={`text-left p-3 rounded-lg border transition-all ${
            value === tmpl.value
              ? "border-primary bg-primary/5 ring-1 ring-primary"
              : "hover:border-primary/50"
          }`}
        >
          <p className="text-sm font-medium">{tmpl.label}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{tmpl.description}</p>
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function NewProjectPage() {
  const t = useTranslations("projects");
  const router = useRouter();
  const createProject = useCreateProject();

  // Basic info
  const [title, setTitle] = React.useState("");
  const [type, setType] = React.useState("");
  const [genre, setGenre] = React.useState("");
  const [subgenre, setSubgenre] = React.useState("");
  const [penName, setPenName] = React.useState("");

  // About
  const [description, setDescription] = React.useState("");
  const [targetAudience, setTargetAudience] = React.useState("");
  const [keywords, setKeywords] = React.useState<string[]>([]);

  // Goals & timeline
  const [targetWordCount, setTargetWordCount] = React.useState("");
  const [targetDate, setTargetDate] = React.useState("");
  const [marketplace, setMarketplace] = React.useState("");

  // Cover & template
  const [template, setTemplate] = React.useState("");
  const [coverPreview, setCoverPreview] = React.useState<string | null>(null);

  // Advanced
  const [advancedOpen, setAdvancedOpen] = React.useState(false);
  const [language, setLanguage] = React.useState("en");
  const [contentRating, setContentRating] = React.useState("general");
  const [hasAIContent, setHasAIContent] = React.useState(false);
  const [isPublicDomain, setIsPublicDomain] = React.useState(false);

  // Validation
  const [touched, setTouched] = React.useState<Record<string, boolean>>({});
  const [submitAttempted, setSubmitAttempted] = React.useState(false);

  const markTouched = React.useCallback((field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }, []);

  const titleValid = title.trim().length >= 2 && title.trim().length <= 200;
  const typeValid = PROJECT_TYPES.includes(type as typeof PROJECT_TYPES[number]);
  const isFormValid = titleValid && typeValid;

  const showError = (field: string, valid: boolean) =>
    (touched[field] || submitAttempted) && !valid;

  const handleCoverUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setCoverPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitAttempted(true);
    if (!isFormValid) return;

    try {
      const result = await createProject.mutateAsync({
        title: title.trim(),
        type: type as "book" | "series" | "course",
        genre: genre || undefined,
        subgenre: subgenre || undefined,
        pen_name: penName || undefined,
        description: description || undefined,
        target_audience: targetAudience || undefined,
        keywords: keywords.length > 0 ? keywords : undefined,
        target_word_count: targetWordCount ? parseInt(targetWordCount) : undefined,
        target_date: targetDate || undefined,
        marketplace: marketplace || undefined,
        template: template || undefined,
        language: language || undefined,
        content_rating: contentRating || undefined,
        has_ai_content: hasAIContent,
        is_public_domain: isPublicDomain,
      });
      toast.success(t("new.messages.success"));
      router.push(`/projects/${result.id}`);
    } catch {
      toast.error(t("new.messages.error"));
    }
  };

  const descriptionCharCount = description.length;

  return (
    <div className="max-w-3xl mx-auto space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild aria-label={t("new.backToProjects")}>
          <Link href="/projects">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
            {t("new.title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("new.subtitle")}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-6">
        {/* ── Section 1: Basic Information ── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("new.form.basicInfo")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label={t("new.form.projectTitle")}
              placeholder={t("new.form.projectTitlePlaceholder")}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => markTouched("title")}
              error={showError("title", titleValid) ? t("new.form.validation.titleRequired") : undefined}
              required
              aria-required="true"
            />

            <div className="space-y-1.5">
              <label htmlFor="project-type" className="text-sm font-medium">
                {t("new.form.projectType")} <span className="text-destructive">*</span>
              </label>
              <Select
                value={type}
                onValueChange={(v) => { setType(v); markTouched("type"); }}
                required
              >
                <SelectTrigger
                  id="project-type"
                  className={showError("type", typeValid) ? "border-destructive" : ""}
                  onBlur={() => markTouched("type")}
                >
                  <SelectValue placeholder={t("new.form.projectTypePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {PROJECT_TYPES.map((pt) => (
                    <SelectItem key={pt} value={pt}>
                      {pt.charAt(0).toUpperCase() + pt.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {showError("type", typeValid) && (
                <p className="text-sm text-destructive">{t("new.form.validation.typeRequired")}</p>
              )}
              <p className="text-xs text-muted-foreground">{t("new.form.projectTypeHelp")}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label htmlFor="project-genre" className="text-sm font-medium">
                  {t("new.form.genre")}
                </label>
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger id="project-genre">
                    <SelectValue placeholder={t("new.form.genrePlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    {GENRES.map((g) => (
                      <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">{t("new.form.genreHelp")}</p>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="project-subgenre" className="text-sm font-medium">
                  {t("new.form.subgenre")}
                </label>
                <Input
                  id="project-subgenre"
                  placeholder={t("new.form.subgenrePlaceholder")}
                  value={subgenre}
                  onChange={(e) => setSubgenre(e.target.value)}
                />
              </div>
            </div>

            <Input
              label={t("new.form.penName")}
              placeholder={t("new.form.penNamePlaceholder")}
              value={penName}
              onChange={(e) => setPenName(e.target.value)}
              helperText={t("new.form.penNameHelp")}
            />
          </CardContent>
        </Card>

        {/* ── Section 2: About Your Book ── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("new.form.aboutBook")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="project-description" className="text-sm font-medium">
                {t("new.form.description")}
              </label>
              <Textarea
                id="project-description"
                placeholder={t("new.form.descriptionPlaceholder")}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                autoGrow
                className="min-h-[100px]"
                maxLength={2000}
              />
              <div className="flex justify-between">
                <p className="text-xs text-muted-foreground">{t("new.form.descriptionHelp")}</p>
                <p className={`text-xs ${descriptionCharCount > 1800 ? "text-destructive" : "text-muted-foreground"}`}>
                  {descriptionCharCount}/2000
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="target-audience" className="text-sm font-medium">
                {t("new.form.targetAudience")}
              </label>
              <Textarea
                id="target-audience"
                placeholder={t("new.form.targetAudiencePlaceholder")}
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                autoGrow
                className="min-h-[80px]"
              />
              <p className="text-xs text-muted-foreground">{t("new.form.targetAudienceHelp")}</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t("new.form.keywords")}</label>
              <KeywordsInput
                keywords={keywords}
                onChange={setKeywords}
                placeholder={t("new.form.keywordsPlaceholder")}
              />
              <p className="text-xs text-muted-foreground">{t("new.form.keywordsHelp")}</p>
            </div>
          </CardContent>
        </Card>

        {/* ── Section 3: Goals & Timeline ── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("new.form.goalsTimeline")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label htmlFor="target-word-count" className="text-sm font-medium">
                  {t("new.form.targetWordCount")}
                </label>
                <Input
                  id="target-word-count"
                  type="number"
                  placeholder={t("new.form.targetWordCountPlaceholder")}
                  value={targetWordCount}
                  onChange={(e) => setTargetWordCount(e.target.value)}
                  min={1000}
                  max={500000}
                />
                <p className="text-xs text-muted-foreground">{t("new.form.targetWordCountHelp")}</p>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="target-date" className="text-sm font-medium">
                  {t("new.form.targetDate")}
                </label>
                <Input
                  id="target-date"
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  min={new Date().toISOString().split("T")[0]}
                />
                <p className="text-xs text-muted-foreground">{t("new.form.targetDateHelp")}</p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="marketplace" className="text-sm font-medium">
                {t("new.form.marketplace")}
              </label>
              <Select value={marketplace} onValueChange={setMarketplace}>
                <SelectTrigger id="marketplace">
                  <SelectValue placeholder={t("new.form.marketplacePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {MARKETPLACES.map((m) => (
                    <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">{t("new.form.marketplaceHelp")}</p>
            </div>
          </CardContent>
        </Card>

        {/* ── Section 4: Cover & Template ── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("new.form.coverTemplate")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Cover Image Upload */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t("new.form.coverImage")}</label>
              <div className="flex items-start gap-4">
                <label
                  htmlFor="cover-upload"
                  className="flex flex-col items-center justify-center w-32 h-40 rounded-lg border-2 border-dashed cursor-pointer hover:border-primary/50 transition-colors bg-muted/30"
                >
                  {coverPreview ? (
                    <img src={coverPreview} alt="Cover preview" className="w-full h-full object-cover rounded-lg" />
                  ) : (
                    <>
                      <Upload className="h-6 w-6 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground mt-1">{t("new.form.coverImageUpload")}</span>
                    </>
                  )}
                  <input
                    id="cover-upload"
                    type="file"
                    accept=".png,.jpg,.jpeg,.tiff"
                    onChange={handleCoverUpload}
                    className="sr-only"
                  />
                </label>
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground">{t("new.form.coverImageDragDrop")}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t("new.form.coverImageFormats")}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t("new.form.coverImageHelp")}</p>
                </div>
              </div>
            </div>

            {/* Template Selector */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t("new.form.template")}</label>
              <TemplateSelector value={template} onChange={setTemplate} t={t} />
              <p className="text-xs text-muted-foreground">{t("new.form.templateHelp")}</p>
            </div>
          </CardContent>
        </Card>

        {/* ── Section 5: Advanced Settings (Collapsible) ── */}
        <Card>
          <CardHeader
            className="cursor-pointer select-none"
            onClick={() => setAdvancedOpen(!advancedOpen)}
          >
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{t("new.form.advancedSettings")}</CardTitle>
              {advancedOpen ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </CardHeader>
          {advancedOpen && (
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label htmlFor="language" className="text-sm font-medium">
                    {t("new.form.language")}
                  </label>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger id="language">
                      <SelectValue placeholder={t("new.form.languagePlaceholder")} />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGES.map((l) => (
                        <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="content-rating" className="text-sm font-medium">
                    {t("new.form.contentRating")}
                  </label>
                  <Select value={contentRating} onValueChange={setContentRating}>
                    <SelectTrigger id="content-rating">
                      <SelectValue placeholder={t("new.form.contentRatingPlaceholder")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">{t("new.form.contentRatingGeneral")}</SelectItem>
                      <SelectItem value="mature">{t("new.form.contentRatingMature")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasAIContent}
                    onChange={(e) => setHasAIContent(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{t("new.form.hasAIContent")}</span>
                </label>
                <p className="text-xs text-muted-foreground ml-6">{t("new.form.aiContentHelp")}</p>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isPublicDomain}
                    onChange={(e) => setIsPublicDomain(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{t("new.form.isPublicDomain")}</span>
                </label>
              </div>
            </CardContent>
          )}
        </Card>

        {/* ── Submit ── */}
        <div className="flex justify-between">
          <Button variant="outline" type="button" asChild>
            <Link href="/projects">{t("new.form.cancel")}</Link>
          </Button>
          <Button
            type="submit"
            disabled={(submitAttempted && !isFormValid) || createProject.isPending}
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
        </div>
      </form>
    </div>
  );
}
