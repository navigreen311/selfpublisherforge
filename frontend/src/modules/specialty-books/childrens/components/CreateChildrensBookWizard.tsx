"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight, Loader2, Check, BookOpen, Palette, PenTool, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { useCreateChildrensBook } from "../hooks";
import type {
  AgeRange,
  TrimSize,
  IllustrationStyle,
  ColorPalette,
  CreationMode,
  StoryMode,
  Tone,
  FearLevel,
  SafetySettings,
  CreateChildrensBookPayload,
} from "../types";

// ---------------------------------------------------------------------------
// Props & local types
// ---------------------------------------------------------------------------

export interface CreateChildrensBookWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type WizardStep = 1 | 2 | 3 | 4;

const STEPS: { step: WizardStep; label: string; icon: React.ElementType }[] = [
  { step: 1, label: "Book Details", icon: BookOpen },
  { step: 2, label: "Format & Style", icon: Palette },
  { step: 3, label: "Story Setup", icon: PenTool },
  { step: 4, label: "Content Safety", icon: ShieldCheck },
];

const AGE_OPTIONS: { value: AgeRange; label: string; pages: string }[] = [
  { value: "board", label: "Board Book (0-3)", pages: "10-16 pages" },
  { value: "picture", label: "Picture Book (3-5)", pages: "24-32 pages" },
  { value: "early_reader", label: "Early Reader (5-8)", pages: "32-48 pages" },
  { value: "chapter", label: "Chapter Book (8-12)", pages: "48-80 pages" },
];

const STYLE_OPTIONS: { value: IllustrationStyle; label: string }[] = [
  { value: "watercolor", label: "Watercolor" },
  { value: "cartoon", label: "Cartoon" },
  { value: "flat", label: "Flat" },
  { value: "storybook", label: "Storybook" },
  { value: "realistic", label: "Realistic" },
  { value: "crayon_pencil", label: "Crayon / Pencil" },
  { value: "collage", label: "Collage" },
  { value: "anime_manga", label: "Anime / Manga" },
];

const PALETTE_OPTIONS: { value: ColorPalette; label: string }[] = [
  { value: "bright_vibrant", label: "Bright & Vibrant" },
  { value: "soft_pastel", label: "Soft & Pastel" },
  { value: "warm_earthy", label: "Warm & Earthy" },
  { value: "cool_dreamy", label: "Cool & Dreamy" },
  { value: "monochrome_accent", label: "Monochrome + Accent" },
];

const TRIM_OPTIONS: { value: TrimSize; label: string }[] = [
  { value: "8.5x8.5", label: "8.5 x 8.5 (Square)" },
  { value: "8.5x11", label: "8.5 x 11 (Portrait)" },
  { value: "10x8", label: "10 x 8 (Landscape)" },
  { value: "6x9", label: "6 x 9 (Chapter)" },
];

const PAGE_COUNTS: Record<AgeRange, number[]> = {
  board: [10, 12, 14, 16],
  picture: [24, 28, 32],
  early_reader: [32, 36, 40, 48],
  chapter: [48, 56, 64, 72, 80],
};

// ---------------------------------------------------------------------------
// Step indicator
// ---------------------------------------------------------------------------

function StepIndicator({ current }: { current: WizardStep }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map(({ step, label, icon: Icon }, idx) => {
        const isActive = step === current;
        const isComplete = step < current;
        return (
          <div key={step} className="flex items-center gap-2">
            {idx > 0 && <div className={cn("h-px w-8", isComplete ? "bg-primary" : "bg-border")} />}
            <div
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive && "bg-primary text-primary-foreground",
                isComplete && "bg-primary/10 text-primary",
                !isActive && !isComplete && "bg-muted text-muted-foreground",
              )}
            >
              {isComplete ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
              <span className="hidden sm:inline">{label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main wizard
// ---------------------------------------------------------------------------

export function CreateChildrensBookWizard({ open, onOpenChange }: CreateChildrensBookWizardProps) {
  const router = useRouter();
  const { mutate: createBook, isPending } = useCreateChildrensBook();

  const [step, setStep] = useState<WizardStep>(1);

  // Step 1: Book Details
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [author, setAuthor] = useState("");
  const [ageRange, setAgeRange] = useState<AgeRange>("picture");
  const [bilingual, setBilingual] = useState(false);
  const [secondaryLanguage, setSecondaryLanguage] = useState("es");

  // Step 2: Format & Style
  const [pageCount, setPageCount] = useState(32);
  const [trimSize, setTrimSize] = useState<TrimSize>("8.5x8.5");
  const [illustrationStyle, setIllustrationStyle] = useState<IllustrationStyle>("watercolor");
  const [colorPalette, setColorPalette] = useState<ColorPalette>("bright_vibrant");

  // Step 3: Story Setup
  const [creationMode, setCreationMode] = useState<CreationMode>("ai_generate");
  const [storyPrompt, setStoryPrompt] = useState("");
  const [themeMoral, setThemeMoral] = useState("");
  const [mainCharacter, setMainCharacter] = useState("");
  const [setting, setSetting] = useState("");
  const [tone, setTone] = useState<Tone>("warm_reassuring");
  const [storyMode, setStoryMode] = useState<StoryMode>("prose");

  // Step 4: Safety
  const [fearIntensity, setFearIntensity] = useState<FearLevel>("none");

  const defaultSafety: SafetySettings = {
    fear_intensity: fearIntensity,
    no_weapons: true,
    no_scary_imagery: true,
    no_trademarked_characters: true,
    no_stereotypes: true,
    age_appropriate_vocabulary: true,
    trademark_safe_prompts: true,
    content_sensitivity_check: true,
    provenance_logging: true,
  };

  const canNext = () => {
    if (step === 1) return title.trim().length > 0 && author.trim().length > 0;
    return true;
  };

  const handleCreate = () => {
    const payload: CreateChildrensBookPayload = {
      title,
      subtitle: subtitle || undefined,
      author,
      age_range: ageRange,
      page_count: pageCount,
      trim_size: trimSize,
      illustration_style: illustrationStyle,
      color_palette: colorPalette,
      creation_mode: creationMode,
      story_mode: storyMode,
      tone,
      safety_settings: { ...defaultSafety, fear_intensity: fearIntensity },
      bilingual,
      secondary_language: bilingual ? secondaryLanguage : undefined,
      story_prompt: storyPrompt || undefined,
      theme_moral: themeMoral || undefined,
      main_character: mainCharacter || undefined,
      setting: setting || undefined,
    };

    createBook(payload, {
      onSuccess: (book) => {
        onOpenChange(false);
        router.push(`/specialty-books/childrens/${book.id}`);
      },
    });
  };

  const handleClose = () => {
    setStep(1);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Children&#39;s Book</DialogTitle>
          <DialogDescription>Set up your illustrated book in 4 easy steps.</DialogDescription>
        </DialogHeader>

        <StepIndicator current={step} />

        {/* Step 1: Book Details */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <Label>Title *</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="My Amazing Story" />
            </div>
            <div>
              <Label>Subtitle</Label>
              <Input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} placeholder="Optional subtitle" />
            </div>
            <div>
              <Label>Author *</Label>
              <Input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Your name or pen name" />
            </div>
            <div>
              <Label>Age Range</Label>
              <div className="grid grid-cols-2 gap-2 mt-1">
                {AGE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => {
                      setAgeRange(opt.value);
                      setPageCount(PAGE_COUNTS[opt.value][0]);
                    }}
                    className={cn(
                      "border rounded-lg p-3 text-left transition-colors",
                      ageRange === opt.value ? "border-primary bg-primary/5 ring-1 ring-primary" : "hover:border-primary/40",
                    )}
                  >
                    <div className="text-sm font-medium">{opt.label}</div>
                    <div className="text-xs text-muted-foreground">{opt.pages}</div>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={bilingual} onCheckedChange={(c) => setBilingual(c === true)} />
              <Label className="text-sm">Bilingual edition</Label>
              {bilingual && (
                <Select value={secondaryLanguage} onValueChange={setSecondaryLanguage}>
                  <SelectTrigger className="w-40 ml-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                    <SelectItem value="zh">Chinese</SelectItem>
                    <SelectItem value="ja">Japanese</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Format & Style */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <Label>Page Count</Label>
              <Select value={String(pageCount)} onValueChange={(v) => setPageCount(Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_COUNTS[ageRange].map((n) => (
                    <SelectItem key={n} value={String(n)}>{n} pages</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Trim Size</Label>
              <Select value={trimSize} onValueChange={(v) => setTrimSize(v as TrimSize)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TRIM_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Illustration Style</Label>
              <div className="grid grid-cols-4 gap-2 mt-1">
                {STYLE_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setIllustrationStyle(s.value)}
                    className={cn(
                      "border rounded-lg p-2 text-center text-xs transition-colors",
                      illustrationStyle === s.value
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "hover:border-primary/40",
                    )}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label>Color Palette</Label>
              <Select value={colorPalette} onValueChange={(v) => setColorPalette(v as ColorPalette)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PALETTE_OPTIONS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {/* Step 3: Story Setup */}
        {step === 3 && (
          <div className="space-y-4">
            <div>
              <Label>Creation Mode</Label>
              <RadioGroup value={creationMode} onValueChange={(v) => setCreationMode(v as CreationMode)} className="mt-1 space-y-2">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="ai_generate" id="mode-ai" />
                  <Label htmlFor="mode-ai" className="text-sm font-normal">AI Generate Full Story</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="write_own" id="mode-write" />
                  <Label htmlFor="mode-write" className="text-sm font-normal">Write My Own</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="import_text" id="mode-import" />
                  <Label htmlFor="mode-import" className="text-sm font-normal">Import Text</Label>
                </div>
              </RadioGroup>
            </div>
            {creationMode === "ai_generate" && (
              <div>
                <Label>Story Prompt</Label>
                <Textarea value={storyPrompt} onChange={(e) => setStoryPrompt(e.target.value)} rows={3} placeholder="Describe your story idea..." />
              </div>
            )}
            <div>
              <Label>Theme / Moral</Label>
              <Input value={themeMoral} onChange={(e) => setThemeMoral(e.target.value)} placeholder="e.g., Courage / Overcoming fears" />
            </div>
            <div>
              <Label>Main Character</Label>
              <Input value={mainCharacter} onChange={(e) => setMainCharacter(e.target.value)} placeholder="e.g., Luna - a small orange tabby kitten" />
            </div>
            <div>
              <Label>Setting</Label>
              <Input value={setting} onChange={(e) => setSetting(e.target.value)} placeholder="e.g., A cozy village with gardens and woods" />
            </div>
            <div>
              <Label>Tone</Label>
              <Select value={tone} onValueChange={(v) => setTone(v as Tone)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="warm_reassuring">Warm & Reassuring</SelectItem>
                  <SelectItem value="exciting">Exciting</SelectItem>
                  <SelectItem value="humorous">Humorous</SelectItem>
                  <SelectItem value="educational">Educational</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Story Mode</Label>
              <RadioGroup value={storyMode} onValueChange={(v) => setStoryMode(v as StoryMode)} className="mt-1 space-y-2">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="prose" id="sm-prose" />
                  <Label htmlFor="sm-prose" className="text-sm font-normal">Prose</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="rhyming_aabb" id="sm-aabb" />
                  <Label htmlFor="sm-aabb" className="text-sm font-normal">Rhyming (AABB)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="rhyming_abab" id="sm-abab" />
                  <Label htmlFor="sm-abab" className="text-sm font-normal">Rhyming (ABAB)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="repetitive_cumulative" id="sm-rep" />
                  <Label htmlFor="sm-rep" className="text-sm font-normal">Repetitive / Cumulative</Label>
                </div>
              </RadioGroup>
            </div>
          </div>
        )}

        {/* Step 4: Content Safety */}
        {step === 4 && (
          <div className="space-y-4">
            <div>
              <Label>Fear Intensity Level</Label>
              <RadioGroup value={fearIntensity} onValueChange={(v) => setFearIntensity(v as FearLevel)} className="mt-1 space-y-2">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="none" id="fear-none" />
                  <Label htmlFor="fear-none" className="text-sm font-normal">None</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="mild" id="fear-mild" />
                  <Label htmlFor="fear-mild" className="text-sm font-normal">Mild</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="moderate" id="fear-moderate" />
                  <Label htmlFor="fear-moderate" className="text-sm font-normal">Moderate</Label>
                </div>
              </RadioGroup>
            </div>
            <div className="space-y-3 border rounded-lg p-4">
              <p className="text-sm font-medium">Safety Enforcement (always on)</p>
              {[
                "No weapons or violence",
                "No scary/dark imagery",
                "No trademarked characters",
                "No stereotypical depictions",
                "Age-appropriate vocabulary",
                "Trademark-safe prompt enforcement",
                "Content sensitivity pre-check",
                "Model/style provenance logging",
              ].map((label) => (
                <div key={label} className="flex items-center gap-2">
                  <Checkbox checked disabled />
                  <span className="text-sm text-muted-foreground">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex justify-between pt-4 border-t">
          <Button variant="outline" onClick={() => (step === 1 ? handleClose() : setStep((step - 1) as WizardStep))}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            {step === 1 ? "Cancel" : "Back"}
          </Button>
          {step < 4 ? (
            <Button onClick={() => setStep((step + 1) as WizardStep)} disabled={!canNext()}>
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button onClick={handleCreate} disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
              Create Book
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
