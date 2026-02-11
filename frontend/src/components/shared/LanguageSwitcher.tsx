"use client";

import * as React from "react";
import { Check, Globe } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { locales, localeNames, localeFlags, type Locale } from "@/i18n/config";
import { cn } from "@/lib/utils";

/**
 * LanguageSwitcher Component
 *
 * Dropdown menu that allows users to switch between supported languages.
 * Displays language names with flag icons and highlights the current selection.
 *
 * @example
 * ```tsx
 * <LanguageSwitcher />
 * ```
 */

interface LanguageSwitcherProps {
  /** Current locale */
  currentLocale?: Locale;
  /** Callback when locale changes */
  onLocaleChange?: (locale: Locale) => void;
  /** Optional className for the trigger button */
  className?: string;
  /** Show only icon (compact mode) */
  compact?: boolean;
}

export function LanguageSwitcher({
  currentLocale = "en",
  onLocaleChange,
  className,
  compact = false,
}: LanguageSwitcherProps) {
  const handleLocaleChange = React.useCallback(
    (locale: Locale) => {
      if (onLocaleChange) {
        onLocaleChange(locale);
      } else {
        // Default behavior: update URL or cookie when integrating with next-intl routing
        document.cookie = `NEXT_LOCALE=${locale};path=/;max-age=31536000`;
      }
    },
    [onLocaleChange]
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={compact ? "icon" : "sm"}
          className={cn("gap-2", className)}
          aria-label="Select language"
        >
          <Globe className="h-4 w-4" />
          {!compact && (
            <span className="hidden sm:inline-block">
              {localeNames[currentLocale]}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        {locales.map((locale) => (
          <DropdownMenuItem
            key={locale}
            onClick={() => handleLocaleChange(locale)}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg" aria-hidden="true">
                {localeFlags[locale]}
              </span>
              <span>{localeNames[locale]}</span>
            </div>
            {currentLocale === locale && (
              <Check className="h-4 w-4 text-primary" aria-label="Selected" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
