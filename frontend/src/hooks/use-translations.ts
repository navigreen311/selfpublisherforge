/**
 * Translation Hook Wrapper
 *
 * Provides a convenient wrapper around next-intl's useTranslations hook
 * with type safety and default namespace handling.
 *
 * Supports loading messages from:
 * 1. Main file: messages/{locale}.json under the namespace key (existing)
 * 2. Namespace files: messages/{locale}/{namespace}.json (new, optional)
 *
 * Namespace files override/extend the main file, allowing gradual migration
 * to per-namespace translation files.
 */

"use client";

import { useTranslations as useNextIntlTranslations } from "next-intl";

/**
 * Hook to access translations for a specific namespace
 *
 * @param namespace - The translation namespace (e.g., "common", "auth", "dashboard")
 * @returns Translation function
 *
 * @example
 * ```tsx
 * // Loads keys from messages/en.json under "auth" namespace
 * // AND from messages/en/auth.json if it exists (overrides/extends)
 * const t = useTranslations("auth");
 * return <button>{t("signIn")}</button>;
 * ```
 *
 * @example
 * ```tsx
 * // Without namespace parameter
 * const t = useTranslations();
 * return <div>{t("common.appName")}</div>;
 * ```
 */
export function useTranslations(namespace?: string) {
  return useNextIntlTranslations(namespace);
}

/**
 * Hook to access common translations (most frequently used)
 *
 * @returns Translation function for common namespace
 *
 * @example
 * ```tsx
 * const t = useCommonTranslations();
 * return <button>{t("save")}</button>;
 * ```
 */
export function useCommonTranslations() {
  return useNextIntlTranslations("common");
}

/**
 * Hook to access auth-related translations
 *
 * @returns Translation function for auth namespace
 */
export function useAuthTranslations() {
  return useNextIntlTranslations("auth");
}

/**
 * Hook to access navigation translations
 *
 * @returns Translation function for navigation namespace
 */
export function useNavigationTranslations() {
  return useNextIntlTranslations("navigation");
}

/**
 * Hook to access error translations
 *
 * @returns Translation function for errors namespace
 */
export function useErrorTranslations() {
  return useNextIntlTranslations("errors");
}

/**
 * Hook to access validation translations
 *
 * @returns Translation function for validation namespace
 */
export function useValidationTranslations() {
  return useNextIntlTranslations("validation");
}
