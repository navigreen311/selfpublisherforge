// ---------------------------------------------------------------------------
// Platform Constants
// ---------------------------------------------------------------------------
// Centralised source of truth for platform names, display labels, marketplace
// codes, and related string literals used throughout the frontend.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Amazon Marketplaces
// ---------------------------------------------------------------------------

/**
 * An Amazon marketplace entry with its two-letter code, human-readable label,
 * and the domain used for product URLs.
 */
export interface AmazonMarketplace {
  /** ISO-style two-letter marketplace code (e.g. "US", "UK"). */
  readonly code: string;
  /** Human-readable marketplace name for display. */
  readonly label: string;
  /** Amazon domain for this marketplace (e.g. "amazon.com"). */
  readonly domain: string;
}

/**
 * The 10 Amazon marketplaces supported by KDP and the Chrome extension.
 *
 * Order follows the backend `AmazonMarketplace` enum defined in
 * `backend/app/modules/chrome_extension/schemas.py`.
 */
export const AMAZON_MARKETPLACES: readonly AmazonMarketplace[] = [
  { code: "US", label: "United States", domain: "amazon.com" },
  { code: "UK", label: "United Kingdom", domain: "amazon.co.uk" },
  { code: "DE", label: "Germany", domain: "amazon.de" },
  { code: "FR", label: "France", domain: "amazon.fr" },
  { code: "CA", label: "Canada", domain: "amazon.ca" },
  { code: "AU", label: "Australia", domain: "amazon.com.au" },
  { code: "JP", label: "Japan", domain: "amazon.co.jp" },
  { code: "IT", label: "Italy", domain: "amazon.it" },
  { code: "ES", label: "Spain", domain: "amazon.es" },
  { code: "IN", label: "India", domain: "amazon.in" },
] as const;

/** Default marketplace used when none is specified. */
export const DEFAULT_MARKETPLACE = "US" as const;

// ---------------------------------------------------------------------------
// Publishing Platforms
// ---------------------------------------------------------------------------

/**
 * A value/label pair used to populate `<select>` dropdowns and display badges.
 */
export interface PlatformOption {
  /** Machine-readable key persisted to the backend (e.g. "kdp"). */
  readonly value: string;
  /** Human-readable display name (e.g. "Amazon KDP"). */
  readonly label: string;
}

/**
 * Publishing platforms available for account connections and listing management.
 *
 * The `value` keys match the backend `platform` column values used in
 * publishing accounts, listings, and royalty records.
 */
export const PUBLISHING_PLATFORMS: readonly PlatformOption[] = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "draft2digital", label: "Draft2Digital" },
  { value: "smashwords", label: "Smashwords" },
  { value: "acx", label: "ACX" },
  { value: "apple_books", label: "Apple Books" },
  { value: "barnes_noble", label: "Barnes & Noble" },
  { value: "kobo", label: "Kobo" },
  { value: "google_play", label: "Google Play Books" },
] as const;

/**
 * Map from publishing-platform key to its display label.
 *
 * Useful for quick look-ups in tables and badges without iterating the array.
 *
 * @example
 * ```ts
 * PUBLISHING_PLATFORM_LABELS["kdp"] // "Amazon KDP"
 * ```
 */
export const PUBLISHING_PLATFORM_LABELS: Readonly<Record<string, string>> =
  Object.fromEntries(PUBLISHING_PLATFORMS.map((p) => [p.value, p.label]));

/**
 * Tailwind CSS colour classes for publishing platform badges.
 *
 * Each key corresponds to a `PUBLISHING_PLATFORMS[].value` entry.
 */
export const PUBLISHING_PLATFORM_COLORS: Readonly<Record<string, string>> = {
  kdp: "bg-orange-100 text-orange-800",
  ingram_spark: "bg-blue-100 text-blue-800",
  draft2digital: "bg-green-100 text-green-800",
  smashwords: "bg-purple-100 text-purple-800",
  acx: "bg-indigo-100 text-indigo-800",
  apple_books: "bg-gray-100 text-gray-800",
  barnes_noble: "bg-emerald-100 text-emerald-800",
  kobo: "bg-red-100 text-red-800",
  google_play: "bg-sky-100 text-sky-800",
} as const;

// ---------------------------------------------------------------------------
// Advertising Platforms
// ---------------------------------------------------------------------------

/**
 * Metadata for a single advertising platform.
 */
export interface AdPlatformEntry {
  /** Human-readable display name (e.g. "Amazon Ads"). */
  readonly displayName: string;
  /** Short abbreviation shown in compact UI contexts. */
  readonly shortName: string;
}

/**
 * Advertising platforms keyed by their backend identifier.
 *
 * Used in campaign creation forms, performance breakdowns, and filter dropdowns.
 */
export const AD_PLATFORMS: Readonly<Record<string, AdPlatformEntry>> = {
  amazon: { displayName: "Amazon Ads", shortName: "AMZ" },
  facebook: { displayName: "Facebook Ads", shortName: "FB" },
} as const;

/** The default advertising platform pre-selected in new campaign forms. */
export const DEFAULT_AD_PLATFORM = "amazon" as const;

/**
 * Campaign types available for each advertising platform.
 *
 * Amazon campaign types correspond to Sponsored Ads product lines;
 * Facebook types map to placement options.
 */
export const AD_CAMPAIGN_TYPES: Readonly<Record<string, readonly PlatformOption[]>> = {
  amazon: [
    { value: "sponsored_products", label: "Sponsored Products" },
    { value: "sponsored_brands", label: "Sponsored Brands" },
    { value: "sponsored_display", label: "Sponsored Display" },
    { value: "lockscreen", label: "Lockscreen" },
  ],
  facebook: [
    { value: "facebook_feed", label: "Facebook Feed" },
    { value: "facebook_stories", label: "Facebook Stories" },
  ],
} as const;

/**
 * Flat array of all campaign types across every advertising platform.
 *
 * Handy for populating a single `<select>` without grouping by platform.
 */
export const ALL_AD_CAMPAIGN_TYPES: readonly PlatformOption[] = Object.values(
  AD_CAMPAIGN_TYPES,
).flat();

/**
 * Bid strategies available when creating or editing a campaign.
 */
export const BID_STRATEGIES: readonly PlatformOption[] = [
  { value: "manual", label: "Manual" },
  { value: "auto_low", label: "Auto (Low)" },
  { value: "auto_high", label: "Auto (High)" },
  { value: "rule_based", label: "Rule-based" },
] as const;

// ---------------------------------------------------------------------------
// Advertising Platform Validation Values
// ---------------------------------------------------------------------------

/**
 * All valid platform values accepted by the campaign validation schema.
 *
 * Kept in sync with `campaignSchema` in `lib/validation.ts`.
 */
export const CAMPAIGN_PLATFORM_VALUES = [
  "amazon",
  "facebook",
  "google",
  "bookbub",
  "other",
] as const;

export type CampaignPlatformValue = (typeof CAMPAIGN_PLATFORM_VALUES)[number];

// ---------------------------------------------------------------------------
// Royalty / Analytics Platforms
// ---------------------------------------------------------------------------

/**
 * Platforms available as royalty import sources.
 *
 * Matches the `RoyaltyImportRequest["platform"]` union type from the
 * analytics hooks.
 */
export const ROYALTY_PLATFORMS: readonly PlatformOption[] = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "draft2digital", label: "Draft2Digital" },
  { value: "other", label: "Other" },
] as const;

/**
 * Revenue filter options including an "All Platforms" entry.
 *
 * Used on the analytics revenue page to filter royalty data by source.
 */
export const REVENUE_PLATFORM_OPTIONS: readonly PlatformOption[] = [
  { value: "", label: "All Platforms" },
  ...ROYALTY_PLATFORMS.filter((p) => p.value !== "other"),
] as const;

// ---------------------------------------------------------------------------
// Social / Marketing Platforms
// ---------------------------------------------------------------------------

/**
 * Social media platforms supported for marketing content scheduling.
 *
 * Matches the `SocialPost["platform"]` union type from marketing hooks.
 */
export const SOCIAL_PLATFORMS = ["twitter", "facebook", "instagram", "tiktok", "linkedin"] as const;

export type SocialPlatformValue = (typeof SOCIAL_PLATFORMS)[number];

/**
 * Short icon-style abbreviations displayed in compact calendar views.
 */
export const SOCIAL_PLATFORM_ICONS: Readonly<Record<string, string>> = {
  twitter: "X",
  facebook: "FB",
  instagram: "IG",
  tiktok: "TT",
  linkedin: "LI",
} as const;

/**
 * Tailwind CSS colour classes for social platform badges.
 */
export const SOCIAL_PLATFORM_COLORS: Readonly<Record<string, string>> = {
  twitter: "bg-black text-white",
  facebook: "bg-blue-600 text-white",
  instagram: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
  tiktok: "bg-gray-900 text-white",
  linkedin: "bg-blue-700 text-white",
} as const;

// ---------------------------------------------------------------------------
// Listing Statuses
// ---------------------------------------------------------------------------

/**
 * Possible statuses for a book listing and their Tailwind badge classes.
 */
export const LISTING_STATUS_STYLES: Readonly<Record<string, string>> = {
  draft: "bg-gray-100 text-gray-700",
  pending: "bg-yellow-100 text-yellow-700",
  live: "bg-green-100 text-green-700",
  paused: "bg-orange-100 text-orange-700",
  rejected: "bg-red-100 text-red-700",
  archived: "bg-gray-200 text-gray-500",
} as const;

// ---------------------------------------------------------------------------
// Campaign Statuses
// ---------------------------------------------------------------------------

/**
 * Possible statuses for an advertising campaign and their Tailwind badge classes.
 */
export const CAMPAIGN_STATUS_STYLES: Readonly<Record<string, string>> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  draft: "bg-gray-100 text-gray-800",
  ended: "bg-red-100 text-red-800",
  archived: "bg-slate-100 text-slate-800",
} as const;

// ---------------------------------------------------------------------------
// OAuth / Auth Providers
// ---------------------------------------------------------------------------

/**
 * OAuth providers supported for account sign-in.
 */
export const OAUTH_PROVIDERS = ["google", "github"] as const;

export type OAuthProvider = (typeof OAUTH_PROVIDERS)[number];

// ---------------------------------------------------------------------------
// Publishing Export Formats
// ---------------------------------------------------------------------------

/**
 * Manuscript export format identifiers referenced in the export wizard.
 */
export const EXPORT_FORMATS = ["epub", "pdf", "docx"] as const;

export type ExportFormat = (typeof EXPORT_FORMATS)[number];

// ---------------------------------------------------------------------------
// Aggregate options (analytics)
// ---------------------------------------------------------------------------

/**
 * Aggregation period options for revenue charts.
 */
export const AGGREGATION_OPTIONS: readonly PlatformOption[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "yearly", label: "Yearly" },
] as const;

/** Default aggregation period. */
export const DEFAULT_AGGREGATION = "monthly" as const;
