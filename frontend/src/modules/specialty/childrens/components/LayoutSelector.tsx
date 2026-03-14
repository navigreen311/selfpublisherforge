"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ─── Layout Types ────────────────────────────────────────────────────────────

export type LayoutType =
  | "full-bleed"
  | "top-image-bottom-text"
  | "bottom-image-top-text"
  | "left-image-right-text"
  | "right-image-left-text"
  | "text-only"
  | "full-bleed-no-text";

export interface LayoutOption {
  type: LayoutType;
  label: string;
  description: string;
}

export const LAYOUT_OPTIONS: LayoutOption[] = [
  {
    type: "full-bleed",
    label: "Full Bleed",
    description: "Illustration fills entire page, text overlaid",
  },
  {
    type: "top-image-bottom-text",
    label: "Top Image / Bottom Text",
    description: "Most common picture book layout",
  },
  {
    type: "bottom-image-top-text",
    label: "Bottom Image / Top Text",
    description: "Text above, illustration below",
  },
  {
    type: "left-image-right-text",
    label: "Left Image / Right Text",
    description: "Side-by-side horizontal layout",
  },
  {
    type: "right-image-left-text",
    label: "Right Image / Left Text",
    description: "Side-by-side horizontal layout",
  },
  {
    type: "text-only",
    label: "Text Only",
    description: "No illustration — title page, dedication, credits",
  },
  {
    type: "full-bleed-no-text",
    label: "Full Bleed No Text",
    description: "Full illustration, no text overlay",
  },
];

// ─── Mini-diagram for each layout ───────────────────────────────────────────

function LayoutDiagram({ type }: { type: LayoutType }) {
  const imgClass = "bg-indigo-200 rounded-[2px]";
  const txtClass = "bg-amber-200 rounded-[2px]";

  switch (type) {
    case "full-bleed":
      return (
        <div className="relative h-full w-full">
          <div className={cn(imgClass, "absolute inset-0")} />
          <div
            className={cn(
              txtClass,
              "absolute bottom-1 left-1 right-1 h-[30%] opacity-80"
            )}
          />
        </div>
      );
    case "top-image-bottom-text":
      return (
        <div className="flex h-full w-full flex-col gap-0.5">
          <div className={cn(imgClass, "flex-[6]")} />
          <div className={cn(txtClass, "flex-[4]")} />
        </div>
      );
    case "bottom-image-top-text":
      return (
        <div className="flex h-full w-full flex-col gap-0.5">
          <div className={cn(txtClass, "flex-[4]")} />
          <div className={cn(imgClass, "flex-[6]")} />
        </div>
      );
    case "left-image-right-text":
      return (
        <div className="flex h-full w-full flex-row gap-0.5">
          <div className={cn(imgClass, "flex-1")} />
          <div className={cn(txtClass, "flex-1")} />
        </div>
      );
    case "right-image-left-text":
      return (
        <div className="flex h-full w-full flex-row gap-0.5">
          <div className={cn(txtClass, "flex-1")} />
          <div className={cn(imgClass, "flex-1")} />
        </div>
      );
    case "text-only":
      return (
        <div className="flex h-full w-full flex-col items-center justify-center gap-0.5 p-1">
          <div className={cn(txtClass, "h-1 w-[80%]")} />
          <div className={cn(txtClass, "h-1 w-[60%]")} />
          <div className={cn(txtClass, "h-1 w-[70%]")} />
          <div className={cn(txtClass, "h-1 w-[50%]")} />
        </div>
      );
    case "full-bleed-no-text":
      return <div className={cn(imgClass, "h-full w-full")} />;
    default:
      return null;
  }
}

// ─── LayoutSelector Component ───────────────────────────────────────────────

interface LayoutSelectorProps {
  value: LayoutType;
  onChange: (layout: LayoutType) => void;
}

export function LayoutSelector({ value, onChange }: LayoutSelectorProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div
        className="grid grid-cols-4 gap-2"
        role="radiogroup"
        aria-label="Page layout"
      >
        {LAYOUT_OPTIONS.map((option) => {
          const isSelected = value === option.type;
          return (
            <Tooltip key={option.type}>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  aria-label={option.label}
                  onClick={() => onChange(option.type)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onChange(option.type);
                    }
                  }}
                  className={cn(
                    "flex h-14 w-full items-center justify-center rounded-md border-2 p-1.5 transition-all duration-150",
                    "hover:border-primary/50 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                    isSelected
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-muted bg-background"
                  )}
                >
                  <div className="h-full w-full">
                    <LayoutDiagram type={option.type} />
                  </div>
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[200px]">
                <p className="font-medium">{option.label}</p>
                <p className="text-xs text-muted-foreground">
                  {option.description}
                </p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
