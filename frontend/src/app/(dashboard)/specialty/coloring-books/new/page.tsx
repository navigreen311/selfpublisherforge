"use client";

import { useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Info,
  Users,
  Sparkles,
  Baby,
  User,
  UserCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useCreateColoringBook } from "@/modules/specialty/coloring/hooks";
import type { CreateColoringBookInput } from "@/modules/specialty/coloring/hooks";

// ─── Constants ────────────────────────────────────────────────────────────────

const AUDIENCES = [
  {
    value: "kids" as const,
    label: "Kids 3-8",
    description: "Simple designs, large shapes, bold outlines",
    icon: Baby,
  },
  {
    value: "teens" as const,
    label: "Teens 9-14",
    description: "Medium detail, engaging themes, moderate complexity",
    icon: User,
  },
  {
    value: "adults" as const,
    label: "Adults 15+",
    description: "Intricate details, fine lines, high complexity",
    icon: UserCircle,
  },
];

const LINE_STYLES = [
  {
    value: "clean_outlines",
    label: "Clean Outlines",
    description: "Crisp, uniform lines with consistent weight",
  },
  {
    value: "sketchy_hand_drawn",
    label: "Sketchy Hand-drawn",
    description: "Organic, imperfect lines with a hand-drawn feel",
  },
  {
    value: "whimsical_decorative",
    label: "Whimsical Decorative",
    description: "Playful designs with decorative flourishes",
  },
  {
    value: "realistic_detailed",
    label: "Realistic Detailed",
    description: "Highly detailed, realistic illustrations",
  },
  {
    value: "zentangle",
    label: "Zentangle",
    description: "Structured patterns within organic shapes",
  },
  {
    value: "bold_simple",
    label: "Bold & Simple",
    description: "Thick lines, simple shapes, easy to color",
  },
];

const TRIM_SIZES = [
  { value: "8.5x11", label: '8.5" x 11" (Letter)' },
  { value: "8.5x8.5", label: '8.5" x 8.5" (Square)' },
  { value: "6x9", label: '6" x 9"' },
  { value: "8x10", label: '8" x 10"' },
];

const GENERATION_METHODS = [
  { value: "all_at_once", label: "All at once", description: "Generate every page in a single batch" },
  { value: "one_at_a_time", label: "One at a time", description: "Generate pages individually for more control" },
  { value: "mix", label: "Mix", description: "Generate some pages in batch, refine others individually" },
] as const;

const BONUS_PAGE_OPTIONS = [
  { value: "title_page", label: "Title Page" },
  { value: "belongs_to", label: "This Book Belongs To" },
  { value: "color_test", label: "Color Test Page" },
  { value: "progress_tracker", label: "Progress Tracker" },
  { value: "certificate", label: "Certificate of Completion" },
  { value: "difficulty_ratings", label: "Difficulty Ratings Key" },
];

const STEPS = ["Book Details", "Format & Style", "Content"];


// Template Pre-fill Config

const TEMPLATE_PREFILLS: Record<
  string,
  {
    title: string;
    themeDescription: string;
    audience?: "kids" | "teens" | "adults";
    lineStyle?: string;
    complexity?: number[];
  }
> = {
  animals: {
    title: "Animals & Wildlife Coloring Book",
    themeDescription: "Lions, elephants, birds, and sea creatures in detailed line art.",
  },
  mandalas: {
    title: "Mandalas & Patterns Coloring Book",
    themeDescription: "Intricate circular mandala designs with repeating symmetry.",
    lineStyle: "zentangle",
    complexity: [7],
  },
  fantasy: {
    title: "Fantasy Worlds Coloring Book",
    themeDescription: "Dragons, castles, fairies, and enchanted forests to color.",
    lineStyle: "whimsical_decorative",
  },
  nature: {
    title: "Nature Scenes Coloring Book",
    themeDescription: "Landscapes, gardens, flowers, and tranquil outdoor scenes.",
    lineStyle: "sketchy_hand_drawn",
  },
  holidays: {
    title: "Holidays & Seasons Coloring Book",
    themeDescription: "Christmas, Halloween, Easter, and seasonal celebrations.",
    lineStyle: "whimsical_decorative",
  },
  space: {
    title: "Space & Sci-Fi Coloring Book",
    themeDescription: "Planets, rockets, aliens, and futuristic cityscapes.",
    lineStyle: "clean_outlines",
  },
  food: {
    title: "Food & Desserts Coloring Book",
    themeDescription: "Cupcakes, fruits, sweets, and delicious dishes to color.",
    lineStyle: "bold_simple",
  },
  geometric: {
    title: "Geometric Abstract Coloring Book",
    themeDescription: "Tessellations, op-art illusions, and abstract geometric forms.",
    lineStyle: "clean_outlines",
    complexity: [8],
  },
};

function getTemplatePrefill(templateId: string | null) {
  if (!templateId) return null;
  return TEMPLATE_PREFILLS[templateId] ?? null;
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function NewColoringBookPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateId = searchParams.get("template");
  const createBook = useCreateColoringBook();

  const prefill = useMemo(() => getTemplatePrefill(templateId), [templateId]);

  const [step, setStep] = useState(0);

  // Step 1 state
  const [title, setTitle] = useState(prefill?.title ?? "");
  const [subtitle, setSubtitle] = useState("");
  const [audience, setAudience] = useState<"kids" | "teens" | "adults">(prefill?.audience ?? "adults");
  const [seriesEnabled, setSeriesEnabled] = useState(false);
  const [seriesName, setSeriesName] = useState("");
  const [volumeNumber, setVolumeNumber] = useState(1);

  // Step 2 state
  const [pageCount, setPageCount] = useState([30]);
  const [trimSize, setTrimSize] = useState("8.5x11");
  const [lineStyle, setLineStyle] = useState(prefill?.lineStyle ?? "clean_outlines");
  const [lineWeight, setLineWeight] = useState([3]);
  const [strokeUniformity, setStrokeUniformity] = useState(true);
  const [complexity, setComplexity] = useState(prefill?.complexity ?? [5]);

  // Step 3 state
  const [themeDescription, setThemeDescription] = useState(prefill?.themeDescription ?? "");
  const [generationMethod, setGenerationMethod] =
    useState<CreateColoringBookInput["generation_method"]>("all_at_once");
  const [bonusPages, setBonusPages] = useState<string[]>(["title_page"]);

  const progressPercent = ((step + 1) / STEPS.length) * 100;

  const canNext = () => {
    if (step === 0) return title.trim().length > 0;
    if (step === 1) return true;
    if (step === 2) return themeDescription.trim().length > 0;
    return false;
  };

  const handleCreate = async () => {
    const input: CreateColoringBookInput = {
      title,
      subtitle: subtitle || undefined,
      audience,
      page_count: pageCount[0],
      trim_size: trimSize,
      line_style: lineStyle,
      line_weight: lineWeight[0],
      complexity: complexity[0],
      stroke_uniformity: strokeUniformity,
      theme_description: themeDescription,
      generation_method: generationMethod,
      bonus_pages: bonusPages,
      series_name: seriesEnabled ? seriesName : undefined,
      volume_number: seriesEnabled ? volumeNumber : undefined,
      template_id: templateId ?? undefined,
    };
    const book = await createBook.mutateAsync(input);
    router.push(`/specialty/coloring-books/${book.id}`);
  };

  const toggleBonusPage = (value: string) => {
    setBonusPages((prev) =>
      prev.includes(value)
        ? prev.filter((v) => v !== value)
        : [...prev, value]
    );
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/specialty/coloring-books")}
          className="mb-2"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
        <h1 className="text-2xl font-bold">Create Coloring Book</h1>
        <p className="text-muted-foreground mt-1">
          {templateId
            ? `Starting from template. Customize your settings below.`
            : `Set up your new coloring book in 3 easy steps.`}
        </p>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground">
          {STEPS.map((s, i) => (
            <span
              key={s}
              className={i <= step ? "text-primary font-medium" : ""}
            >
              {i + 1}. {s}
            </span>
          ))}
        </div>
        <Progress value={progressPercent} className="h-2" />
      </div>

      {/* Step 1: Book Details */}
      {step === 0 && (
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Amazing Animals Coloring Book"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subtitle">Subtitle</Label>
            <Input
              id="subtitle"
              placeholder="e.g., 30 Beautiful Designs for Relaxation"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
            />
          </div>

          <div className="space-y-3">
            <Label>Audience</Label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {AUDIENCES.map((a) => (
                <Card
                  key={a.value}
                  className={`cursor-pointer transition-all ${
                    audience === a.value
                      ? "ring-2 ring-primary"
                      : "hover:shadow-sm"
                  }`}
                  onClick={() => setAudience(a.value)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      setAudience(a.value);
                  }}
                >
                  <CardContent className="p-4 text-center">
                    <a.icon className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <p className="font-medium text-sm">{a.label}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {a.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Switch
                id="series"
                checked={seriesEnabled}
                onCheckedChange={setSeriesEnabled}
              />
              <Label htmlFor="series">Part of a series</Label>
            </div>
            {seriesEnabled && (
              <div className="grid grid-cols-2 gap-4 pl-1">
                <div className="space-y-2">
                  <Label htmlFor="series-name">Series Name</Label>
                  <Input
                    id="series-name"
                    placeholder="e.g., Relaxing Coloring Series"
                    value={seriesName}
                    onChange={(e) => setSeriesName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="volume">Volume Number</Label>
                  <Input
                    id="volume"
                    type="number"
                    min={1}
                    value={volumeNumber}
                    onChange={(e) =>
                      setVolumeNumber(parseInt(e.target.value) || 1)
                    }
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 2: Format & Style */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Page Count: {pageCount[0]}</Label>
              <span className="text-xs text-muted-foreground">20 - 60</span>
            </div>
            <Slider
              min={20}
              max={60}
              step={2}
              value={pageCount}
              onValueChange={setPageCount}
            />
          </div>

          <div className="space-y-2">
            <Label>Trim Size</Label>
            <Select value={trimSize} onValueChange={setTrimSize}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TRIM_SIZES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Line Art Style</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {LINE_STYLES.map((ls) => (
                <Card
                  key={ls.value}
                  className={`cursor-pointer transition-all ${
                    lineStyle === ls.value
                      ? "ring-2 ring-primary"
                      : "hover:shadow-sm"
                  }`}
                  onClick={() => setLineStyle(ls.value)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      setLineStyle(ls.value);
                  }}
                >
                  <CardContent className="p-3">
                    <p className="font-medium text-sm">{ls.label}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {ls.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Line Weight: {lineWeight[0]}px</Label>
              <span className="text-xs text-muted-foreground">1 - 10</span>
            </div>
            <Slider
              min={1}
              max={10}
              step={1}
              value={lineWeight}
              onValueChange={setLineWeight}
            />
          </div>

          <div className="flex items-center gap-3">
            <Switch
              id="stroke-uniformity"
              checked={strokeUniformity}
              onCheckedChange={setStrokeUniformity}
            />
            <Label htmlFor="stroke-uniformity">
              Enforce stroke uniformity
            </Label>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Complexity: {complexity[0]} / 10</Label>
              <span className="text-xs text-muted-foreground">1 - 10</span>
            </div>
            <Slider
              min={1}
              max={10}
              step={1}
              value={complexity}
              onValueChange={setComplexity}
            />
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Single-sided printing enforced &bull; Coloring-safe inner margin
              applied (+0.25&quot; at spine)
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Step 3: Content */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="theme">Theme Description *</Label>
            <Textarea
              id="theme"
              placeholder="Describe the theme or subjects for your coloring pages. Be as specific as you like — e.g., 'Cute woodland animals in whimsical forest settings with mushrooms, flowers, and tiny houses.'"
              rows={4}
              value={themeDescription}
              onChange={(e) => setThemeDescription(e.target.value)}
            />
          </div>

          <div className="space-y-3">
            <Label>Generation Method</Label>
            <div className="space-y-2">
              {GENERATION_METHODS.map((m) => (
                <Card
                  key={m.value}
                  className={`cursor-pointer transition-all ${
                    generationMethod === m.value
                      ? "ring-2 ring-primary"
                      : "hover:shadow-sm"
                  }`}
                  onClick={() => setGenerationMethod(m.value)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      setGenerationMethod(m.value);
                  }}
                >
                  <CardContent className="p-3 flex items-center gap-3">
                    <div
                      className={`h-4 w-4 rounded-full border-2 flex items-center justify-center ${
                        generationMethod === m.value
                          ? "border-primary"
                          : "border-muted-foreground/40"
                      }`}
                    >
                      {generationMethod === m.value && (
                        <div className="h-2 w-2 rounded-full bg-primary" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{m.label}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label>Bonus Pages</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {BONUS_PAGE_OPTIONS.map((bp) => (
                <div
                  key={bp.value}
                  className="flex items-center gap-2 rounded-md border p-3"
                >
                  <Checkbox
                    id={`bonus-${bp.value}`}
                    checked={bonusPages.includes(bp.value)}
                    onCheckedChange={() => toggleBonusPage(bp.value)}
                  />
                  <Label
                    htmlFor={`bonus-${bp.value}`}
                    className="cursor-pointer text-sm font-normal"
                  >
                    {bp.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button
          variant="outline"
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </Button>

        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep((s) => s + 1)} disabled={!canNext()}>
            Next
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        ) : (
          <Button
            onClick={handleCreate}
            disabled={!canNext() || createBook.isPending}
          >
            {createBook.isPending ? (
              <>
                <Sparkles className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Create Coloring Book
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
