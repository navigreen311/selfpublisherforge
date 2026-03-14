"use client";

import { useState } from "react";
import { Palette, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStyleClones } from "../hooks";
import type { StyleCloneProfile } from "@/modules/specialty/types/style-clone";

interface StyleClonePickerProps {
  value?: string;
  onChange: (profileId: string | undefined) => void;
  bookType?: string;
}

export function StyleClonePicker({ value, onChange, bookType }: StyleClonePickerProps) {
  const [open, setOpen] = useState(false);

  const { data } = useStyleClones(1, 50, {
    ...(bookType && { book_type: bookType }),
    active_only: true,
  });

  const profiles = data?.items ?? [];
  const selected = profiles.find((p) => p.id === value);

  const handleSelect = (profile: StyleCloneProfile | null) => {
    onChange(profile?.id ?? undefined);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          <span className="flex items-center gap-2 truncate">
            <Palette className="h-4 w-4 shrink-0 text-muted-foreground" />
            {selected ? selected.name : "Select Style..."}
          </span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0" align="start">
        <ScrollArea className="max-h-[280px]">
          <button
            type="button"
            className="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-accent transition-colors"
            onClick={() => handleSelect(null)}
          >
            <span className="h-8 w-8 rounded bg-muted flex items-center justify-center text-muted-foreground">
              <Palette className="h-4 w-4" />
            </span>
            <span className="flex-1 text-left text-muted-foreground">None</span>
            {!value && <Check className="h-4 w-4 text-primary" />}
          </button>

          {profiles.map((profile) => (
            <button
              key={profile.id}
              type="button"
              className="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-accent transition-colors"
              onClick={() => handleSelect(profile)}
            >
              <span className="h-8 w-8 rounded overflow-hidden bg-muted shrink-0">
                {profile.reference_image_urls?.[0] ? (
                  <img
                    src={profile.reference_image_urls[0]}
                    alt={profile.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="h-full w-full flex items-center justify-center text-muted-foreground">
                    <Palette className="h-4 w-4" />
                  </span>
                )}
              </span>

              <span className="flex-1 text-left min-w-0">
                <span className="flex items-center gap-1.5">
                  <span className="truncate font-medium">{profile.name}</span>
                  {profile.is_default && (
                    <Badge variant="secondary" className="text-[9px] px-1 py-0">
                      Default
                    </Badge>
                  )}
                </span>
                <span className="text-xs text-muted-foreground">
                  Used {profile.times_used}x
                </span>
              </span>

              {value === profile.id && (
                <Check className="h-4 w-4 text-primary shrink-0" />
              )}
            </button>
          ))}

          {profiles.length === 0 && (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">
              No style profiles found
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
