/**
 * i18n Request Handler
 *
 * Provides the next-intl request configuration for Next.js App Router.
 * This is used to set up the locale context for server components.
 *
 * Supports loading messages from:
 * 1. Main file: messages/{locale}.json (existing translations)
 * 2. Namespace files: messages/{locale}/{namespace}.json (new translations)
 *
 * Namespace files override/extend the main file.
 */

import { getRequestConfig } from "next-intl/server";
import {
  defaultLocale,
  isValidLocale,
  type Locale,
  supportedNamespaces,
  deepMerge,
} from "./config";

/**
 * Load messages for a specific locale
 * Merges main locale file with any namespace-specific files
 */
async function loadMessages(locale: Locale): Promise<Record<string, any>> {
  // Load the main locale file (always exists, provides base translations)
  const mainMessages = (await import(`../messages/${locale}.json`)).default;

  // Clone the main messages to avoid mutations
  let mergedMessages = { ...mainMessages };

  // Attempt to load and merge namespace-specific files
  for (const namespace of supportedNamespaces) {
    try {
      // Try to load namespace file from messages/{locale}/{namespace}.json
      const namespaceMessages = await import(
        `../messages/${locale}/${namespace}.json`
      );

      // Merge namespace messages into the corresponding namespace in main messages
      if (namespaceMessages.default) {
        mergedMessages = deepMerge(mergedMessages, {
          [namespace]: namespaceMessages.default,
        });
      }
    } catch (error) {
      // Namespace file doesn't exist - that's OK, just skip it
      // This allows gradual migration to namespace files
      continue;
    }
  }

  return mergedMessages;
}

export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming `locale` parameter is valid
  const validatedLocale: Locale = isValidLocale(locale)
    ? (locale as Locale)
    : defaultLocale;

  return {
    locale: validatedLocale,
    messages: await loadMessages(validatedLocale),
  };
});
