"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, ChevronLeft, ChevronRight, Loader2, Check, Palette, FileText } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useCreateColoringBook } from "../hooks";
import type { ColoringAudience, LineArtStyle, TrimSize, GenerationMethod, BonusPageConfig, ColoringTemplate } from "../types";

export interface CreateColoringBookWizardProps { open: boolean; onOpenChange: (open: boolean) => void; prefilledTemplate?: ColoringTemplate | null; }
type WizardStep = 1 | 2 | 3;
const STEPS: { step: WizardStep; label: string; icon: React.ElementType }[] = [{ step: 1, label: "Book Details", icon: BookOpen }, { step: 2, label: "Format & Style", icon: Palette }, { step: 3, label: "Content", icon: FileText }];
const AUDIENCE_OPTIONS: { value: ColoringAudience; label: string }[] = [{ value: "kids_3_8", label: "Kids (3-8)" }, { value: "teens_9_14", label: "Teens (9-14)" }, { value: "adults_15_plus", label: "Adults (15+)" }];
const LINE_STYLE_OPTIONS: { value: LineArtStyle; label: string; description: string }[] = [{ value: "clean", label: "Clean Outlines", description: "Smooth, uniform lines" }, { value: "sketchy", label: "Sketchy Hand-drawn", description: "Natural pencil feel" }, { value: "whimsical", label: "Whimsical Decorative", description: "Fun, playful details" }, { value: "realistic", label: "Realistic Detailed", description: "Lifelike illustrations" }, { value: "zentangle", label: "Zentangle", description: "Intricate patterns" }, { value: "bold", label: "Bold & Simple", description: "Thick, easy-to-color lines" }];
const TRIM_SIZE_OPTIONS: { value: TrimSize; label: string }[] = [{ value: "8.5x11", label: '8.5" x 11" (Standard)' }, { value: "8.5x8.5", label: '8.5" x 8.5" (Square)' }, { value: "6x9", label: '6" x 9" (Compact)' }];
const GENERATION_METHOD_OPTIONS: { value: GenerationMethod; label: string; description: string }[] = [{ value: "all_at_once", label: "All at Once", description: "Generate all pages in a batch" }, { value: "one_at_a_time", label: "One at a Time", description: "Review each page individually" }, { value: "mix", label: "Mix", description: "Generate batch, then refine" }];

function StepIndicator({ current }: { current: WizardStep }) {
  return (<div className="flex items-center gap-2 mb-6">{STEPS.map(({ step, label, icon: Icon }, idx) => { const isActive = step === current; const isComplete = step < current; return (<div key={step} className="flex items-center gap-2">{idx > 0 && <div className={cn("h-px w-8", isComplete ? "bg-primary" : "bg-border")} />}<div className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors", isActive && "bg-primary text-primary-foreground", isComplete && "bg-primary/10 text-primary", !isActive && !isComplete && "bg-muted text-muted-foreground")}>{isComplete ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}<span className="hidden sm:inline">{label}</span></div></div>); })}</div>);
}

export function CreateColoringBookWizard({ open, onOpenChange, prefilledTemplate }: CreateColoringBookWizardProps) {
  const router = useRouter();
  const [step, setStep] = useState<WizardStep>(1);
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [audience, setAudience] = useState<ColoringAudience>(prefilledTemplate?.defaultAudience ?? "kids_3_8");
  const [seriesName, setSeriesName] = useState("");
  const [seriesVolume, setSeriesVolume] = useState("");
  const [pageCount, setPageCount] = useState(prefilledTemplate?.defaultPageCount ?? 30);
  const [trimSize, setTrimSize] = useState<TrimSize>("8.5x11");
  const [lineStyle, setLineStyle] = useState<LineArtStyle>(prefilledTemplate?.defaultStyle ?? "clean");
  const [lineWeight, setLineWeight] = useState(2);
  const [strokeUniformity, setStrokeUniformity] = useState(true);
  const [complexity, setComplexity] = useState(prefilledTemplate?.defaultComplexity ?? 50);
  const [themeDescription, setThemeDescription] = useState(prefilledTemplate?.themeDescription ?? "");
  const [generationMethod, setGenerationMethod] = useState<GenerationMethod>("all_at_once");
  const [bonusPages, setBonusPages] = useState<BonusPageConfig>({ title_page: true, belongs_to: true, color_test: false, progress_tracker: false, certificate: false, difficulty_ratings: false });
  const { mutate: createBook, isPending } = useCreateColoringBook();

  const reset = () => { setStep(1); setTitle(""); setSubtitle(""); setAudience(prefilledTemplate?.defaultAudience ?? "kids_3_8"); setSeriesName(""); setSeriesVolume(""); setPageCount(prefilledTemplate?.defaultPageCount ?? 30); setTrimSize("8.5x11"); setLineStyle(prefilledTemplate?.defaultStyle ?? "clean"); setLineWeight(2); setStrokeUniformity(true); setComplexity(prefilledTemplate?.defaultComplexity ?? 50); setThemeDescription(prefilledTemplate?.themeDescription ?? ""); setGenerationMethod("all_at_once"); setBonusPages({ title_page: true, belongs_to: true, color_test: false, progress_tracker: false, certificate: false, difficulty_ratings: false }); };

  React.useEffect(() => { if (prefilledTemplate) { setAudience(prefilledTemplate.defaultAudience); setLineStyle(prefilledTemplate.defaultStyle); setPageCount(prefilledTemplate.defaultPageCount); setComplexity(prefilledTemplate.defaultComplexity); setThemeDescription(prefilledTemplate.themeDescription); } }, [prefilledTemplate]);

  const handleOpenChange = (nextOpen: boolean) => { if (!nextOpen && !isPending) reset(); onOpenChange(nextOpen); };
  const canProceed = (): boolean => { if (step === 1) return title.trim().length > 0; if (step === 3) return themeDescription.trim().length > 0; return true; };

  const handleCreate = () => { createBook({ title: title.trim(), subtitle: subtitle.trim() || undefined, audience, series_name: seriesName.trim() || undefined, series_volume: seriesVolume ? parseInt(seriesVolume, 10) : undefined, page_count: pageCount, trim_size: trimSize, line_style: lineStyle, line_weight: lineWeight, stroke_uniformity: strokeUniformity, complexity, theme_description: themeDescription.trim(), generation_method: generationMethod, bonus_pages: bonusPages, template_id: prefilledTemplate?.id }, { onSuccess: (book) => { toast.success("Coloring book created!"); reset(); onOpenChange(false); router.push("/specialty-books/coloring/" + book.id); } }); };

  const toggleBonus = (key: keyof BonusPageConfig) => { setBonusPages({ ...bonusPages, [key]: !bonusPages[key] }); };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader><DialogTitle>Create Coloring Book</DialogTitle><DialogDescription>Set up your coloring book in 3 easy steps.</DialogDescription></DialogHeader>
        <StepIndicator current={step} />
        {step === 1 && (<div className="space-y-4">
          <div className="space-y-2"><Label htmlFor="cb-title">Title *</Label><Input id="cb-title" placeholder="e.g., Amazing Animals Coloring Book" value={title} onChange={(e) => setTitle(e.target.value)} /></div>
          <div className="space-y-2"><Label htmlFor="cb-subtitle">Subtitle</Label><Input id="cb-subtitle" placeholder="e.g., 30 Beautiful Designs for All Ages" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} /></div>
          <div className="space-y-2"><Label>Audience *</Label><div className="grid grid-cols-3 gap-3">{AUDIENCE_OPTIONS.map((opt) => (<button key={opt.value} type="button" onClick={() => setAudience(opt.value)} className={cn("border rounded-lg p-3 text-sm font-medium transition-all text-center", audience === opt.value ? "ring-2 ring-primary border-primary shadow-sm" : "hover:shadow-md hover:border-primary/30")}>{opt.label}</button>))}</div></div>
          <div className="grid grid-cols-2 gap-4"><div className="space-y-2"><Label htmlFor="cb-series-name">Series Name</Label><Input id="cb-series-name" placeholder="e.g., Amazing Animals" value={seriesName} onChange={(e) => setSeriesName(e.target.value)} /></div><div className="space-y-2"><Label htmlFor="cb-series-vol">Volume Number</Label><Input id="cb-series-vol" type="number" min={1} placeholder="1" value={seriesVolume} onChange={(e) => setSeriesVolume(e.target.value)} /></div></div>
        </div>)}
        {step === 2 && (<div className="space-y-5">
          <div className="grid grid-cols-2 gap-4"><div className="space-y-2"><Label>Page Count ({pageCount})</Label><Slider min={20} max={60} step={5} value={[pageCount]} onValueChange={([v]) => setPageCount(v)} /><p className="text-xs text-muted-foreground">20-60 coloring pages</p></div><div className="space-y-2"><Label>Trim Size</Label><Select value={trimSize} onValueChange={(v) => setTrimSize(v as TrimSize)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TRIM_SIZE_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent></Select></div></div>
          <div className="space-y-2"><Label>Line Art Style *</Label><div className="grid grid-cols-2 sm:grid-cols-3 gap-2">{LINE_STYLE_OPTIONS.map((opt) => (<button key={opt.value} type="button" onClick={() => setLineStyle(opt.value)} className={cn("border rounded-lg p-3 text-left transition-all space-y-0.5", lineStyle === opt.value ? "ring-2 ring-primary border-primary shadow-sm" : "hover:shadow-md hover:border-primary/30")}><span className="text-sm font-medium block">{opt.label}</span><span className="text-xs text-muted-foreground">{opt.description}</span></button>))}</div></div>
          <div className="space-y-2"><Label>Line Weight ({lineWeight}px)</Label><Slider min={1} max={8} step={0.5} value={[lineWeight]} onValueChange={([v]) => setLineWeight(v)} /></div>
          <div className="flex items-center gap-2"><Checkbox id="cb-stroke" checked={strokeUniformity} onCheckedChange={(v) => setStrokeUniformity(v === true)} /><Label htmlFor="cb-stroke" className="text-sm">Enforce stroke uniformity</Label></div>
          <div className="space-y-2"><Label>Complexity ({complexity}%)</Label><Slider min={10} max={100} step={5} value={[complexity]} onValueChange={([v]) => setComplexity(v)} /><p className="text-xs text-muted-foreground">Lower = simpler (kids), Higher = intricate (adults)</p></div>
          <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground"><strong>Single-sided printing enforced.</strong> Blank backs auto-inserted. Coloring-safe inner margin (+0.25in) applied.</div>
        </div>)}
        {step === 3 && (<div className="space-y-5">
          <div className="space-y-2"><Label htmlFor="cb-theme">Theme Description *</Label><Textarea id="cb-theme" placeholder="Describe the theme for your coloring book pages..." value={themeDescription} onChange={(e) => setThemeDescription(e.target.value)} rows={4} /></div>
          <div className="space-y-2"><Label>Generation Method</Label><div className="grid grid-cols-1 sm:grid-cols-3 gap-2">{GENERATION_METHOD_OPTIONS.map((opt) => (<button key={opt.value} type="button" onClick={() => setGenerationMethod(opt.value)} className={cn("border rounded-lg p-3 text-left transition-all space-y-0.5", generationMethod === opt.value ? "ring-2 ring-primary border-primary shadow-sm" : "hover:shadow-md hover:border-primary/30")}><span className="text-sm font-medium block">{opt.label}</span><span className="text-xs text-muted-foreground">{opt.description}</span></button>))}</div></div>
          <div className="space-y-3"><Label>Bonus Pages</Label><div className="grid grid-cols-2 gap-2">{([{ key: "title_page" as const, label: "Title Page" }, { key: "belongs_to" as const, label: "This Book Belongs To" }, { key: "color_test" as const, label: "Color Test Page" }, { key: "progress_tracker" as const, label: "Progress Tracker" }, { key: "certificate" as const, label: "Completion Certificate" }, { key: "difficulty_ratings" as const, label: "Difficulty Ratings" }]).map(({ key, label }) => (<div key={key} className="flex items-center gap-2"><Checkbox id={"bonus-" + key} checked={bonusPages[key]} onCheckedChange={() => toggleBonus(key)} /><Label htmlFor={"bonus-" + key} className="text-sm">{label}</Label></div>))}</div></div>
        </div>)}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button variant="outline" onClick={() => { if (step > 1) setStep((s) => (s - 1) as WizardStep); }} disabled={step === 1 || isPending}><ChevronLeft className="h-4 w-4 mr-1" />Back</Button>
          {step < 3 ? (<Button onClick={() => { if (step < 3) setStep((s) => (s + 1) as WizardStep); }} disabled={!canProceed()}>Next<ChevronRight className="h-4 w-4 ml-1" /></Button>) : (<Button onClick={handleCreate} disabled={isPending || !canProceed()}>{isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}{isPending ? "Creating..." : "Create Coloring Book"}</Button>)}
        </div>
      </DialogContent>
    </Dialog>
  );
}
