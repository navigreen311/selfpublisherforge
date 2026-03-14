"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Type,
  Palette,
  Image as ImageIcon,
  Wand2,
  Upload,
  RefreshCw,
  Grid2X2,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Sparkles,
  Eye,
} from "lucide-react";
import { LayoutSelector, type LayoutType } from "./LayoutSelector";

// ─── Types ──────────────────────────────────────────────────────────────────

export type AgeRange = "board" | "picture" | "early-reader" | "chapter";
export type TextPosition = "top" | "middle" | "bottom";

const MIN_FONT_SIZES: Record<AgeRange, number> = {
  board: 24,
  picture: 18,
  "early-reader": 14,
  chapter: 12,
};

const AGE_RANGE_LABELS: Record<AgeRange, string> = {
  board: "Board (0-3)",
  picture: "Picture (3-5)",
  "early-reader": "Early Reader (5-8)",
  chapter: "Chapter (8-12)",
};

const FONT_FAMILIES = [
  "Inter",
  "Merriweather",
  "Lora",
  "Quicksand",
  "Nunito",
  "Comic Neue",
  "Patrick Hand",
  "Fredoka One",
  "Baloo 2",
  "Bubblegum Sans",
] as const;

interface TextProperties {
  fontFamily: string;
  fontSize: number;
  color: string;
  position: TextPosition;
  autoTextPlate: boolean;
}

interface IllustrationProperties {
  prompt: string;
  trademarkSafe: boolean | null; // null = unchecked
  characterConsistency: boolean;
  provenanceModel?: string;
  provenanceDate?: string;
}

interface ReadabilityInfo {
  contrastScore: number; // 0-21 WCAG ratio
  contrastPass: boolean; // WCAG AA
  gutterSafe: boolean;
}

interface PagePropertiesProps {
  layout: LayoutType;
  onLayoutChange: (layout: LayoutType) => void;
  ageRange: AgeRange;
  textProps: TextProperties;
  onTextPropsChange: (props: TextProperties) => void;
  illustrationProps: IllustrationProperties;
  onIllustrationPropsChange: (props: IllustrationProperties) => void;
  readability: ReadabilityInfo;
  onGenerateIllustration: () => void;
  onUploadImage: () => void;
  onRegenerate: () => void;
  onGenerateVariations: () => void;
}

// ─── Component ──────────────────────────────────────────────────────────────

export function PageProperties({
  layout,
  onLayoutChange,
  ageRange,
  textProps,
  onTextPropsChange,
  illustrationProps,
  onIllustrationPropsChange,
  readability,
  onGenerateIllustration,
  onUploadImage,
  onRegenerate,
  onGenerateVariations,
}: PagePropertiesProps) {
  const minFontSize = MIN_FONT_SIZES[ageRange];

  const handleFontSizeChange = React.useCallback(
    (value: string) => {
      const parsed = parseInt(value, 10);
      if (!isNaN(parsed)) {
        onTextPropsChange({
          ...textProps,
          fontSize: Math.max(parsed, minFontSize),
        });
      }
    },
    [textProps, onTextPropsChange, minFontSize]
  );

  const handleFontSizeBlur = React.useCallback(() => {
    if (textProps.fontSize < minFontSize) {
      onTextPropsChange({ ...textProps, fontSize: minFontSize });
    }
  }, [textProps, onTextPropsChange, minFontSize]);

  return (
    <div className="flex h-full flex-col border-l bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <h3 className="text-sm font-semibold text-foreground">Properties</h3>
        <Badge variant="outline" className="text-[10px]">
          {AGE_RANGE_LABELS[ageRange]}
        </Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
          {/* ── Layout Section ──────────────────────────────────────── */}
          <section aria-labelledby="layout-heading">
            <h4
              id="layout-heading"
              className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
            >
              <Grid2X2 className="h-3.5 w-3.5" />
              Layout
            </h4>
            <LayoutSelector value={layout} onChange={onLayoutChange} />
          </section>

          <Separator />

          {/* ── Text Properties Section ─────────────────────────────── */}
          {layout !== "full-bleed-no-text" && (
            <>
              <section aria-labelledby="text-heading">
                <h4
                  id="text-heading"
                  className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  <Type className="h-3.5 w-3.5" />
                  Text Properties
                </h4>

                <div className="flex flex-col gap-3">
                  {/* Font family */}
                  <div className="space-y-1.5">
                    <Label htmlFor="font-family" className="text-xs">
                      Font Family
                    </Label>
                    <Select
                      value={textProps.fontFamily}
                      onValueChange={(v) =>
                        onTextPropsChange({ ...textProps, fontFamily: v })
                      }
                    >
                      <SelectTrigger id="font-family" className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FONT_FAMILIES.map((font) => (
                          <SelectItem key={font} value={font} className="text-xs">
                            {font}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Font size */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="font-size" className="text-xs">
                        Font Size
                      </Label>
                      <TooltipProvider delayDuration={200}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-[10px] text-muted-foreground">
                              Min: {minFontSize}pt
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            Minimum font size enforced for{" "}
                            {AGE_RANGE_LABELS[ageRange]} age band
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <Input
                      id="font-size"
                      type="number"
                      min={minFontSize}
                      value={textProps.fontSize}
                      onChange={(e) => handleFontSizeChange(e.target.value)}
                      onBlur={handleFontSizeBlur}
                      className="h-8 text-xs"
                    />
                    {textProps.fontSize < minFontSize && (
                      <p className="flex items-center gap-1 text-[10px] text-destructive">
                        <AlertTriangle className="h-3 w-3" />
                        Below minimum for {AGE_RANGE_LABELS[ageRange]}
                      </p>
                    )}
                  </div>

                  {/* Color picker */}
                  <div className="space-y-1.5">
                    <Label htmlFor="text-color" className="text-xs">
                      Color
                    </Label>
                    <div className="flex items-center gap-2">
                      <input
                        id="text-color"
                        type="color"
                        value={textProps.color}
                        onChange={(e) =>
                          onTextPropsChange({
                            ...textProps,
                            color: e.target.value,
                          })
                        }
                        className="h-8 w-8 cursor-pointer rounded border p-0.5"
                        aria-label="Text color"
                      />
                      <Input
                        value={textProps.color}
                        onChange={(e) =>
                          onTextPropsChange({
                            ...textProps,
                            color: e.target.value,
                          })
                        }
                        className="h-8 flex-1 font-mono text-xs"
                        maxLength={7}
                      />
                    </div>
                  </div>

                  {/* Position */}
                  <div className="space-y-1.5">
                    <Label htmlFor="text-position" className="text-xs">
                      Position
                    </Label>
                    <Select
                      value={textProps.position}
                      onValueChange={(v) =>
                        onTextPropsChange({
                          ...textProps,
                          position: v as TextPosition,
                        })
                      }
                    >
                      <SelectTrigger id="text-position" className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="top" className="text-xs">
                          Top Third
                        </SelectItem>
                        <SelectItem value="middle" className="text-xs">
                          Middle
                        </SelectItem>
                        <SelectItem value="bottom" className="text-xs">
                          Bottom Third
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Auto text plate */}
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="auto-text-plate"
                        className="text-xs font-medium"
                      >
                        Auto Text Plate
                      </Label>
                      <p className="text-[10px] text-muted-foreground">
                        Adds background behind text when contrast is low
                      </p>
                    </div>
                    <Switch
                      id="auto-text-plate"
                      checked={textProps.autoTextPlate}
                      onCheckedChange={(checked) =>
                        onTextPropsChange({
                          ...textProps,
                          autoTextPlate: checked,
                        })
                      }
                    />
                  </div>
                </div>
              </section>

              <Separator />

              {/* ── Readability Section ──────────────────────────────── */}
              <section aria-labelledby="readability-heading">
                <h4
                  id="readability-heading"
                  className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  <Eye className="h-3.5 w-3.5" />
                  Readability
                </h4>

                <div className="flex flex-col gap-2">
                  {/* Contrast score */}
                  <Card
                    className={cn(
                      "border",
                      readability.contrastPass
                        ? "border-green-200 bg-green-50/50"
                        : "border-red-200 bg-red-50/50"
                    )}
                  >
                    <CardContent className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-2">
                        {readability.contrastPass ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600" />
                        )}
                        <div>
                          <p className="text-xs font-medium">Contrast</p>
                          <p className="text-[10px] text-muted-foreground">
                            WCAG AA ({readability.contrastScore.toFixed(1)}:1)
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant={
                          readability.contrastPass ? "default" : "destructive"
                        }
                        className="text-[10px]"
                      >
                        {readability.contrastPass ? "PASS" : "FAIL"}
                      </Badge>
                    </CardContent>
                  </Card>

                  {/* Gutter safety */}
                  <Card
                    className={cn(
                      "border",
                      readability.gutterSafe
                        ? "border-green-200 bg-green-50/50"
                        : "border-red-200 bg-red-50/50"
                    )}
                  >
                    <CardContent className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-2">
                        {readability.gutterSafe ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                        )}
                        <div>
                          <p className="text-xs font-medium">Gutter Safety</p>
                          <p className="text-[10px] text-muted-foreground">
                            0.5in spine clearance
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant={
                          readability.gutterSafe ? "default" : "destructive"
                        }
                        className="text-[10px]"
                      >
                        {readability.gutterSafe ? "SAFE" : "WARNING"}
                      </Badge>
                    </CardContent>
                  </Card>
                </div>
              </section>

              <Separator />
            </>
          )}

          {/* ── Illustration Section ────────────────────────────────── */}
          {layout !== "text-only" && (
            <section aria-labelledby="illustration-heading">
              <h4
                id="illustration-heading"
                className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                <ImageIcon className="h-3.5 w-3.5" />
                Illustration
              </h4>

              <div className="flex flex-col gap-3">
                {/* Prompt textarea */}
                <div className="space-y-1.5">
                  <Label htmlFor="illustration-prompt" className="text-xs">
                    Illustration Prompt
                  </Label>
                  <Textarea
                    id="illustration-prompt"
                    value={illustrationProps.prompt}
                    onChange={(e) =>
                      onIllustrationPropsChange({
                        ...illustrationProps,
                        prompt: e.target.value,
                      })
                    }
                    placeholder="Describe the illustration for this page..."
                    className="min-h-[80px] resize-y text-xs"
                    rows={4}
                  />
                </div>

                {/* Trademark check indicator */}
                <div className="flex items-center gap-2">
                  {illustrationProps.trademarkSafe === null ? (
                    <Badge
                      variant="outline"
                      className="gap-1 text-[10px] text-muted-foreground"
                    >
                      <Info className="h-3 w-3" />
                      Trademark check pending
                    </Badge>
                  ) : illustrationProps.trademarkSafe ? (
                    <Badge
                      variant="default"
                      className="gap-1 bg-green-600 text-[10px] hover:bg-green-700"
                    >
                      <ShieldCheck className="h-3 w-3" />
                      Trademark safe
                    </Badge>
                  ) : (
                    <Badge
                      variant="destructive"
                      className="gap-1 text-[10px]"
                    >
                      <ShieldAlert className="h-3 w-3" />
                      Trademark issue detected
                    </Badge>
                  )}
                </div>

                {/* Action buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={onGenerateIllustration}
                  >
                    <Wand2 className="h-3 w-3" />
                    Generate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={onUploadImage}
                  >
                    <Upload className="h-3 w-3" />
                    Upload
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={onRegenerate}
                  >
                    <RefreshCw className="h-3 w-3" />
                    Regenerate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={onGenerateVariations}
                  >
                    <Grid2X2 className="h-3 w-3" />
                    4 Variations
                  </Button>
                </div>

                {/* Character consistency toggle */}
                <div className="flex items-center justify-between rounded-md border p-2.5">
                  <div className="space-y-0.5">
                    <Label
                      htmlFor="char-consistency"
                      className="text-xs font-medium"
                    >
                      Character Consistency
                    </Label>
                    <p className="text-[10px] text-muted-foreground">
                      Auto-append character description to prompt
                    </p>
                  </div>
                  <Switch
                    id="char-consistency"
                    checked={illustrationProps.characterConsistency}
                    onCheckedChange={(checked) =>
                      onIllustrationPropsChange({
                        ...illustrationProps,
                        characterConsistency: checked,
                      })
                    }
                  />
                </div>

                {/* Provenance info */}
                {(illustrationProps.provenanceModel ||
                  illustrationProps.provenanceDate) && (
                  <Card className="border-muted">
                    <CardContent className="p-2.5">
                      <div className="flex items-start gap-2">
                        <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                        <div className="space-y-0.5 text-[10px] text-muted-foreground">
                          {illustrationProps.provenanceModel && (
                            <p>
                              <span className="font-medium">Model:</span>{" "}
                              {illustrationProps.provenanceModel}
                            </p>
                          )}
                          {illustrationProps.provenanceDate && (
                            <p>
                              <span className="font-medium">Generated:</span>{" "}
                              {illustrationProps.provenanceDate}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </section>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export { MIN_FONT_SIZES, AGE_RANGE_LABELS, FONT_FAMILIES };
export type {
  TextProperties,
  IllustrationProperties,
  ReadabilityInfo,
  PagePropertiesProps,
};
