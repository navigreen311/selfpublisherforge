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

  // Load main messages file
  const mainMessages = (await import(`../messages/${validatedLocale}.json`)).default;

  // Load namespace-specific messages
  const dashboardMessages = (await import(`../messages/${validatedLocale}/dashboard.json`)).default;
  const projectsMessages = (await import(`../messages/${validatedLocale}/projects.json`)).default;
  const writingMessages = (await import(`../messages/${validatedLocale}/writing.json`)).default;
  const analyticsMessages = (await import(`../messages/${validatedLocale}/analytics.json`)).default;
  const publishingMessages = (await import(`../messages/${validatedLocale}/publishing.json`)).default;
  const marketingMessages = (await import(`../messages/${validatedLocale}/marketing.json`)).default;

  return {
    locale: validatedLocale,
    messages: {
      ...mainMessages,
      dashboard: dashboardMessages,
      projects: projectsMessages,
      writing: writingMessages,
      analytics: analyticsMessages,
      publishing: publishingMessages,
      marketing: marketingMessages,
    },
  };
});
