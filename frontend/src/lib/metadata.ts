import type { Metadata } from "next";

/**
 * Default site configuration for SEO metadata
 */
const SITE_CONFIG = {
  name: "SelfPublisherForge",
  description: "AI-powered self-publishing platform for authors and publishers",
  url: process.env.NEXT_PUBLIC_APP_URL || "https://selfpublisherforge.com",
  ogImage: "/og-image.png",
  twitterHandle: "@selfpubforge",
} as const;

export interface MetadataOptions {
  title: string;
  description: string;
  /**
   * If true, adds robots: { index: false, follow: false } to prevent search engine indexing.
   * Use this for dashboard/private pages.
   * @default false
   */
  noindex?: boolean;
  /**
   * Custom Open Graph image URL (optional)
   */
  ogImage?: string;
  /**
   * Custom canonical URL (optional)
   */
  canonical?: string;
}

/**
 * Creates consistent metadata for Next.js pages with SEO best practices.
 *
 * @param options - Metadata configuration options
 * @returns Next.js Metadata object with title, description, Open Graph, Twitter Card, and robots tags
 *
 * @example
 * ```tsx
 * // For a public page
 * export const metadata = createMetadata({
 *   title: "Login",
 *   description: "Sign in to your SelfPublisherForge account"
 * });
 *
 * // For a private dashboard page
 * export const metadata = createMetadata({
 *   title: "Dashboard",
 *   description: "View your publishing analytics and activity",
 *   noindex: true
 * });
 * ```
 */
export function createMetadata(options: MetadataOptions): Metadata {
  const { title, description, noindex = false, ogImage, canonical } = options;

  const fullTitle = `${title} | ${SITE_CONFIG.name}`;
  const imageUrl = ogImage || SITE_CONFIG.ogImage;
  const absoluteImageUrl = imageUrl.startsWith("http")
    ? imageUrl
    : `${SITE_CONFIG.url}${imageUrl}`;

  return {
    title: fullTitle,
    description,
    ...(canonical && { alternates: { canonical } }),
    ...(noindex && {
      robots: {
        index: false,
        follow: false,
        nocache: true,
      },
    }),
    openGraph: {
      type: "website",
      title: fullTitle,
      description,
      siteName: SITE_CONFIG.name,
      url: canonical || SITE_CONFIG.url,
      images: [
        {
          url: absoluteImageUrl,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      images: [absoluteImageUrl],
      creator: SITE_CONFIG.twitterHandle,
    },
  };
}

/**
 * Default metadata for the root layout.
 * Individual pages should override with their own specific metadata.
 */
export const defaultMetadata: Metadata = {
  metadataBase: new URL(SITE_CONFIG.url),
  title: {
    default: SITE_CONFIG.name,
    template: `%s | ${SITE_CONFIG.name}`,
  },
  description: SITE_CONFIG.description,
  keywords: [
    "self-publishing",
    "publishing platform",
    "author tools",
    "book publishing",
    "AI writing assistant",
    "royalty tracking",
    "book analytics",
    "publishing automation",
  ],
  authors: [{ name: "SelfPublisherForge Team" }],
  creator: "SelfPublisherForge",
  publisher: "SelfPublisherForge",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_CONFIG.url,
    siteName: SITE_CONFIG.name,
    title: SITE_CONFIG.name,
    description: SITE_CONFIG.description,
    images: [
      {
        url: `${SITE_CONFIG.url}${SITE_CONFIG.ogImage}`,
        width: 1200,
        height: 630,
        alt: SITE_CONFIG.name,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_CONFIG.name,
    description: SITE_CONFIG.description,
    creator: SITE_CONFIG.twitterHandle,
    images: [`${SITE_CONFIG.url}${SITE_CONFIG.ogImage}`],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};
