"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  showOpacity?: boolean;
}

interface ColorPalette {
  name: string;
  colors: string[];
}

const PRESET_COLORS = [
  "#000000", "#1a1a1a", "#333333", "#4d4d4d", "#666666", "#808080",
  "#999999", "#b3b3b3", "#cccccc", "#e6e6e6", "#f5f5f5", "#ffffff",
  "#8B0000", "#DC143C", "#FF6347", "#FF4500", "#FF8C00", "#FFA500",
  "#FFD700", "#FFFF00", "#9ACD32", "#32CD32", "#00FA9A", "#00CED1",
  "#1E90FF", "#4169E1", "#0000CD", "#8A2BE2", "#9932CC", "#FF1493",
  "#A0522D", "#D2691E", "#CD853F", "#DEB887", "#F4A460", "#DAA520",
];

const COLOR_PALETTES: ColorPalette[] = [
  { name: "Dark & Moody", colors: ["#1a1a1a", "#2d2d2d", "#1c1c2e", "#2c1810", "#1f1f1f", "#0d1117"] },
  { name: "Light & Clean", colors: ["#ffffff", "#f8f9fa", "#f0f0f0", "#e9ecef", "#dee2e6", "#f5f5f5"] },
  { name: "Warm", colors: ["#8B4513", "#A0522D", "#CD853F", "#DEB887", "#D2691E", "#F4A460"] },
  { name: "Cool", colors: ["#2E5090", "#4682B4", "#5F9EA0", "#4169E1", "#6495ED", "#7B68EE"] },
  { name: "Bold", colors: ["#DC143C", "#FF4500", "#FFD700", "#32CD32", "#1E90FF", "#9932CC"] },
  { name: "Pastel", colors: ["#FFB6C1", "#FFE4B5", "#E0BBE4", "#B4E7CE", "#B6D7FF", "#FFD6E8"] },
];

const MAX_RECENT_COLORS = 8;

export function ColorPicker({ value, onChange, showOpacity = false }: ColorPickerProps) {
  const [open, setOpen] = React.useState(false);
  const [hexInput, setHexInput] = React.useState(value);
  const [opacity, setOpacity] = React.useState(100);
  const [recentColors, setRecentColors] = React.useState<string[]>([]);

  React.useEffect(() => {
    setHexInput(value);
  }, [value]);

  React.useEffect(() => {
    try {
      const stored = localStorage.getItem("cover-design-recent-colors");
      if (stored) {
        setRecentColors(JSON.parse(stored));
      }
    } catch (error) {
      console.error("Failed to load recent colors:", error);
    }
  }, []);

  const handleColorSelect = (color: string) => {
    onChange(color);
    setHexInput(color);
    setRecentColors((prev) => {
      const filtered = prev.filter((c) => c !== color);
      const updated = [color, ...filtered].slice(0, MAX_RECENT_COLORS);
      try {
        localStorage.setItem("cover-design-recent-colors", JSON.stringify(updated));
      } catch (error) {
        console.error("Failed to save recent colors:", error);
      }
      return updated;
    });
  };

  const handleHexInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let input = e.target.value;
    input = input.replace(/[^0-9a-fA-F#]/g, "");
    if (!input.startsWith("#")) {
      input = "#" + input;
    }
    input = input.slice(0, 7);
    setHexInput(input);
    if (/^#[0-9a-fA-F]{6}$/.test(input)) {
      handleColorSelect(input);
    }
  };

  const handleOpacityChange = (values: number[]) => {
    setOpacity(values[0]);
  };

  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) } : null;
  };

  const currentColorStyle = showOpacity && opacity < 100
    ? (() => { const rgb = hexToRgb(value); return rgb ? `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity / 100})` : value; })()
    : value;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" className="w-full justify-start gap-2">
          <div className="h-5 w-5 rounded border border-border shrink-0" style={{ backgroundColor: currentColorStyle }} />
          <span className="font-mono text-sm">{value.toUpperCase()}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px]" align="start">
        <Tabs defaultValue="swatches" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="swatches">Swatches</TabsTrigger>
            <TabsTrigger value="palettes">Palettes</TabsTrigger>
          </TabsList>
          <TabsContent value="swatches" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="hex-input">Hex Color</Label>
              <div className="flex gap-2">
                <Input id="hex-input" value={hexInput} onChange={handleHexInputChange} placeholder="#000000" className="font-mono" />
                <div className="h-10 w-10 rounded border border-border shrink-0" style={{ backgroundColor: value }} />
              </div>
            </div>
            {showOpacity && (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label htmlFor="opacity-slider">Opacity</Label>
                  <span className="text-sm text-muted-foreground">{opacity}%</span>
                </div>
                <Slider id="opacity-slider" min={0} max={100} step={1} value={[opacity]} onValueChange={handleOpacityChange} />
              </div>
            )}
            {recentColors.length > 0 && (
              <div className="space-y-2">
                <Label>Recent Colors</Label>
                <div className="grid grid-cols-8 gap-2">
                  {recentColors.map((color, index) => (
                    <button key={index} onClick={() => handleColorSelect(color)}
                      className={cn("h-8 w-8 rounded border-2 transition-all hover:scale-110", color === value ? "border-primary" : "border-border")}
                      style={{ backgroundColor: color }} title={color} />
                  ))}
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Label>Common Colors</Label>
              <div className="grid grid-cols-6 gap-2">
                {PRESET_COLORS.map((color) => (
                  <button key={color} onClick={() => handleColorSelect(color)}
                    className={cn("h-8 w-8 rounded border-2 transition-all hover:scale-110", color === value ? "border-primary" : "border-border")}
                    style={{ backgroundColor: color }} title={color} />
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="palettes" className="space-y-4 mt-4">
            {COLOR_PALETTES.map((palette) => (
              <div key={palette.name} className="space-y-2">
                <Label>{palette.name}</Label>
                <div className="grid grid-cols-6 gap-2">
                  {palette.colors.map((color) => (
                    <button key={color} onClick={() => handleColorSelect(color)}
                      className={cn("h-10 w-full rounded border-2 transition-all hover:scale-105", color === value ? "border-primary" : "border-border")}
                      style={{ backgroundColor: color }} title={color} />
                  ))}
                </div>
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </PopoverContent>
    </Popover>
  );
}
