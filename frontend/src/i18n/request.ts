/**
 * i18n Request Handler
 *
 * Provides the next-intl request configuration for Next.js App Router.
 * This is used to set up the locale context for server components.
 */

import { getRequestConfig } from "next-intl/server";
import { defaultLocale, isValidLocale, type Locale } from "./config";

export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming `locale` parameter is valid
  const validatedLocale: Locale = isValidLocale(locale)
    ? (locale as Locale)
    : defaultLocale;

  return {
    locale: validatedLocale,
    messages: (await import(`../messages/${validatedLocale}.json`)).default,
  };
});
