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

/**
 * Supported namespaces for per-namespace message files
 * These can have their own files in messages/{locale}/ directory
 */
export const supportedNamespaces = [
  "common",
  "auth",
  "navigation",
  "errors",
  "validation",
  "dashboard",
  "analytics",
  "billing",
  "projects",
  "content",
  "metadata",
  "publications",
  "settings",
  "pricing",
  "product-page",
  "home",
  "market",
  "marketing",
  "pipeline",
] as const;

export type Namespace = (typeof supportedNamespaces)[number];

/**
 * Deep merge utility for combining translation objects
 * Namespace files override/extend the main file
 */
export function deepMerge<T extends Record<string, any>>(
  target: T,
  source: Partial<T>
): T {
  const result = { ...target };

  for (const key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      const sourceValue = source[key];
      const targetValue = result[key];

      if (
        sourceValue &&
        typeof sourceValue === "object" &&
        !Array.isArray(sourceValue) &&
        targetValue &&
        typeof targetValue === "object" &&
        !Array.isArray(targetValue)
      ) {
        result[key] = deepMerge(targetValue, sourceValue);
      } else if (sourceValue !== undefined) {
        result[key] = sourceValue;
      }
    }
  }

  return result;
}
