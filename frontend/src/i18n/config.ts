/**
 * i18n Configuration
 *
 * Defines supported locales, default locale, and other internationalization settings.
 */

export type Locale = "en" | "es" | "de";

export const locales: readonly Locale[] = ["en", "es", "de"] as const;

export const defaultLocale: Locale = "en";

export const localeNames: Record<Locale, string> = {
  en: "English",
  es: "Español",
  de: "Deutsch",
};

export const localeFlags: Record<Locale, string> = {
  en: "🇺🇸",
  es: "🇪🇸",
  de: "🇩🇪",
};

/**
 * Check if a string is a valid locale
 */
export function isValidLocale(locale: string): locale is Locale {
  return locales.includes(locale as Locale);
}

/**
 * Get locale from browser or fallback to default
 */
export function getLocaleFromNavigator(): Locale {
  if (typeof window === "undefined") return defaultLocale;

  const browserLocale = window.navigator.language.split("-")[0];
  return isValidLocale(browserLocale) ? browserLocale : defaultLocale;
}
