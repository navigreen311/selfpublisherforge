"use client";

import * as React from "react";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

interface FontPickerProps {
  value: string;
  onChange: (font: string) => void;
}

interface Font {
  name: string;
  category: "serif" | "sans-serif" | "script" | "display";
  fontFamily: string;
}

const FONTS: Font[] = [
  { name: "Playfair Display", category: "serif", fontFamily: "'Playfair Display', serif" },
  { name: "Merriweather", category: "serif", fontFamily: "'Merriweather', serif" },
  { name: "Lora", category: "serif", fontFamily: "'Lora', serif" },
  { name: "Georgia", category: "serif", fontFamily: "Georgia, serif" },
  { name: "Garamond", category: "serif", fontFamily: "Garamond, serif" },
  { name: "Libre Baskerville", category: "serif", fontFamily: "'Libre Baskerville', serif" },
  { name: "Source Serif Pro", category: "serif", fontFamily: "'Source Serif Pro', serif" },
  { name: "Crimson Text", category: "serif", fontFamily: "'Crimson Text', serif" },
  { name: "Cormorant", category: "serif", fontFamily: "'Cormorant', serif" },
  { name: "EB Garamond", category: "serif", fontFamily: "'EB Garamond', serif" },
  { name: "Bitter", category: "serif", fontFamily: "'Bitter', serif" },
  { name: "Cardo", category: "serif", fontFamily: "'Cardo', serif" },
  { name: "Spectral", category: "serif", fontFamily: "'Spectral', serif" },
  { name: "Montserrat", category: "sans-serif", fontFamily: "'Montserrat', sans-serif" },
  { name: "Roboto", category: "sans-serif", fontFamily: "'Roboto', sans-serif" },
  { name: "Raleway", category: "sans-serif", fontFamily: "'Raleway', sans-serif" },
  { name: "Open Sans", category: "sans-serif", fontFamily: "'Open Sans', sans-serif" },
  { name: "Poppins", category: "sans-serif", fontFamily: "'Poppins', sans-serif" },
  { name: "Oswald", category: "sans-serif", fontFamily: "'Oswald', sans-serif" },
  { name: "Lato", category: "sans-serif", fontFamily: "'Lato', sans-serif" },
  { name: "Nunito", category: "sans-serif", fontFamily: "'Nunito', sans-serif" },
  { name: "Work Sans", category: "sans-serif", fontFamily: "'Work Sans', sans-serif" },
  { name: "Inter", category: "sans-serif", fontFamily: "'Inter', sans-serif" },
  { name: "Quicksand", category: "sans-serif", fontFamily: "'Quicksand', sans-serif" },
  { name: "Barlow", category: "sans-serif", fontFamily: "'Barlow', sans-serif" },
  { name: "Dancing Script", category: "script", fontFamily: "'Dancing Script', cursive" },
  { name: "Great Vibes", category: "script", fontFamily: "'Great Vibes', cursive" },
  { name: "Pacifico", category: "script", fontFamily: "'Pacifico', cursive" },
  { name: "Satisfy", category: "script", fontFamily: "'Satisfy', cursive" },
  { name: "Allura", category: "script", fontFamily: "'Allura', cursive" },
  { name: "Alex Brush", category: "script", fontFamily: "'Alex Brush', cursive" },
  { name: "Bebas Neue", category: "display", fontFamily: "'Bebas Neue', display" },
  { name: "Cinzel", category: "display", fontFamily: "'Cinzel', display" },
  { name: "Abril Fatface", category: "display", fontFamily: "'Abril Fatface', display" },
  { name: "Righteous", category: "display", fontFamily: "'Righteous', display" },
  { name: "Anton", category: "display", fontFamily: "'Anton', display" },
  { name: "Permanent Marker", category: "display", fontFamily: "'Permanent Marker', display" },
  { name: "Lobster", category: "display", fontFamily: "'Lobster', display" },
  { name: "Bungee", category: "display", fontFamily: "'Bungee', display" },
];

const CATEGORY_LABELS = {
  serif: "Serif",
  "sans-serif": "Sans-Serif",
  script: "Script",
  display: "Display",
};

export function FontPicker({ value, onChange }: FontPickerProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const selectedFont = FONTS.find((font) => font.name === value);
  const filteredFonts = React.useMemo(() => {
    const searchLower = search.toLowerCase();
    return FONTS.filter(
      (font) =>
        font.name.toLowerCase().includes(searchLower) ||
        font.category.toLowerCase().includes(searchLower)
    );
  }, [search]);
  const fontsByCategory = React.useMemo(() => {
    const grouped: Record<string, Font[]> = {
      serif: [],
      "sans-serif": [],
      script: [],
      display: [],
    };
    filteredFonts.forEach((font) => {
      grouped[font.category].push(font);
    });
    return grouped;
  }, [filteredFonts]);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between">
          <span style={{ fontFamily: selectedFont?.fontFamily || "inherit" }}>
            {selectedFont?.name || "Select font..."}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] p-0" align="start">
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search fonts..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
          </div>
        </div>
        <ScrollArea className="h-[400px]">
          <div className="p-2">
            {Object.entries(fontsByCategory).map(([category, fonts]) => {
              if (fonts.length === 0) return null;
              return (
                <div key={category} className="mb-4">
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase">
                    {CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]}
                  </div>
                  <div className="space-y-1">
                    {fonts.map((font) => (
                      <button key={font.name} onClick={() => { onChange(font.name); setOpen(false); }}
                        className={cn("w-full flex items-center justify-between px-2 py-2 rounded-sm text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors", value === font.name && "bg-accent")}>
                        <span style={{ fontFamily: font.fontFamily, fontSize: "16px" }}>{font.name}</span>
                        {value === font.name && <Check className="h-4 w-4 shrink-0" />}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
            {filteredFonts.length === 0 && (
              <div className="text-center py-6 text-sm text-muted-foreground">No fonts found</div>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
