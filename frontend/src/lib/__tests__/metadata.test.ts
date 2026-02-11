import { createMetadata, defaultMetadata } from "../metadata";
import type { Metadata } from "next";

// ─── createMetadata ─────────────────────────────────────────────────────────

describe("createMetadata", () => {
  it("creates basic metadata with title and description", () => {
    const result = createMetadata({
      title: "Test Page",
      description: "This is a test page",
    });

    expect(result.title).toBe("Test Page | SelfPublisherForge");
    expect(result.description).toBe("This is a test page");
  });

  it("includes Open Graph metadata", () => {
    const result = createMetadata({
      title: "Dashboard",
      description: "View your analytics",
    });

    expect(result.openGraph).toBeDefined();
    expect(result.openGraph?.type).toBe("website");
    expect(result.openGraph?.title).toBe("Dashboard | SelfPublisherForge");
    expect(result.openGraph?.description).toBe("View your analytics");
    expect(result.openGraph?.siteName).toBe("SelfPublisherForge");
  });

  it("includes Twitter Card metadata", () => {
    const result = createMetadata({
      title: "Analytics",
      description: "Track your performance",
    });

    expect(result.twitter).toBeDefined();
    expect(result.twitter?.card).toBe("summary_large_image");
    expect(result.twitter?.title).toBe("Analytics | SelfPublisherForge");
    expect(result.twitter?.description).toBe("Track your performance");
    expect(result.twitter?.creator).toBe("@selfpubforge");
  });

  it("adds noindex robots meta when noindex is true", () => {
    const result = createMetadata({
      title: "Private Page",
      description: "This is private",
      noindex: true,
    });

    expect(result.robots).toBeDefined();
    expect(result.robots).toEqual({
      index: false,
      follow: false,
      nocache: true,
    });
  });

  it("does not add robots meta when noindex is false", () => {
    const result = createMetadata({
      title: "Public Page",
      description: "This is public",
      noindex: false,
    });

    expect(result.robots).toBeUndefined();
  });

  it("does not add robots meta when noindex is undefined", () => {
    const result = createMetadata({
      title: "Default Page",
      description: "Default behavior",
    });

    expect(result.robots).toBeUndefined();
  });

  it("uses custom Open Graph image when provided", () => {
    const result = createMetadata({
      title: "Custom Image Page",
      description: "Has custom OG image",
      ogImage: "/custom-og.png",
    });

    expect(result.openGraph?.images).toBeDefined();
    const images = Array.isArray(result.openGraph?.images)
      ? result.openGraph?.images
      : [result.openGraph?.images];

    expect(images[0]).toMatchObject({
      url: expect.stringContaining("/custom-og.png"),
      width: 1200,
      height: 630,
      alt: "Custom Image Page",
    });
  });

  it("uses default Open Graph image when not provided", () => {
    const result = createMetadata({
      title: "Default Image Page",
      description: "Uses default OG image",
    });

    expect(result.openGraph?.images).toBeDefined();
    const images = Array.isArray(result.openGraph?.images)
      ? result.openGraph?.images
      : [result.openGraph?.images];

    expect(images[0]).toMatchObject({
      url: expect.stringContaining("/og-image.png"),
    });
  });

  it("handles absolute URL for custom OG image", () => {
    const result = createMetadata({
      title: "Absolute Image",
      description: "Has absolute URL OG image",
      ogImage: "https://example.com/custom.png",
    });

    const images = Array.isArray(result.openGraph?.images)
      ? result.openGraph?.images
      : [result.openGraph?.images];

    expect(images[0]).toMatchObject({
      url: "https://example.com/custom.png",
    });
  });

  it("adds canonical URL when provided", () => {
    const result = createMetadata({
      title: "Canonical Page",
      description: "Has canonical URL",
      canonical: "https://example.com/page",
    });

    expect(result.alternates).toBeDefined();
    expect(result.alternates?.canonical).toBe("https://example.com/page");
  });

  it("does not add canonical URL when not provided", () => {
    const result = createMetadata({
      title: "No Canonical",
      description: "No canonical URL",
    });

    expect(result.alternates).toBeUndefined();
  });

  it("uses canonical URL in Open Graph metadata when provided", () => {
    const result = createMetadata({
      title: "Test",
      description: "Test",
      canonical: "https://example.com/test",
    });

    expect(result.openGraph?.url).toBe("https://example.com/test");
  });

  it("handles very long titles correctly", () => {
    const longTitle = "A".repeat(200);
    const result = createMetadata({
      title: longTitle,
      description: "Description",
    });

    expect(result.title).toBe(`${longTitle} | SelfPublisherForge`);
  });

  it("handles special characters in title and description", () => {
    const result = createMetadata({
      title: "Test & <Special> \"Characters\"",
      description: "Description with 'quotes' and <tags>",
    });

    expect(result.title).toContain("Test & <Special> \"Characters\"");
    expect(result.description).toBe("Description with 'quotes' and <tags>");
  });

  it("includes Twitter image with absolute URL", () => {
    const result = createMetadata({
      title: "Twitter Test",
      description: "Test Twitter Card",
      ogImage: "/custom.png",
    });

    expect(result.twitter?.images).toBeDefined();
    expect(Array.isArray(result.twitter?.images)).toBe(true);
    if (Array.isArray(result.twitter?.images)) {
      expect(result.twitter.images[0]).toMatch(/^https?:\/\/.+\/custom\.png$/);
    }
  });

  it("creates metadata for auth pages (indexable)", () => {
    const result = createMetadata({
      title: "Login",
      description: "Sign in to your account",
      noindex: false,
    });

    expect(result.title).toBe("Login | SelfPublisherForge");
    expect(result.robots).toBeUndefined(); // Should be indexable
  });

  it("creates metadata for dashboard pages (not indexable)", () => {
    const result = createMetadata({
      title: "Dashboard",
      description: "Your private dashboard",
      noindex: true,
    });

    expect(result.title).toBe("Dashboard | SelfPublisherForge");
    expect(result.robots).toEqual({
      index: false,
      follow: false,
      nocache: true,
    });
  });
});

// ─── defaultMetadata ────────────────────────────────────────────────────────

describe("defaultMetadata", () => {
  it("has correct site name", () => {
    expect(defaultMetadata.title).toMatchObject({
      default: "SelfPublisherForge",
      template: "%s | SelfPublisherForge",
    });
  });

  it("has site description", () => {
    expect(defaultMetadata.description).toBe(
      "AI-powered self-publishing platform for authors and publishers"
    );
  });

  it("has metadata base URL", () => {
    expect(defaultMetadata.metadataBase).toBeDefined();
    expect(defaultMetadata.metadataBase?.toString()).toMatch(/^https?:\/\//);
  });

  it("includes SEO keywords", () => {
    expect(defaultMetadata.keywords).toBeDefined();
    expect(Array.isArray(defaultMetadata.keywords)).toBe(true);
    expect((defaultMetadata.keywords as string[]).length).toBeGreaterThan(0);
  });

  it("includes self-publishing in keywords", () => {
    expect(defaultMetadata.keywords).toContain("self-publishing");
  });

  it("has Open Graph configuration", () => {
    expect(defaultMetadata.openGraph).toBeDefined();
    expect(defaultMetadata.openGraph?.type).toBe("website");
    expect(defaultMetadata.openGraph?.locale).toBe("en_US");
    expect(defaultMetadata.openGraph?.siteName).toBe("SelfPublisherForge");
  });

  it("has Twitter Card configuration", () => {
    expect(defaultMetadata.twitter).toBeDefined();
    expect(defaultMetadata.twitter?.card).toBe("summary_large_image");
    expect(defaultMetadata.twitter?.creator).toBe("@selfpubforge");
  });

  it("has robot configuration allowing indexing", () => {
    expect(defaultMetadata.robots).toBeDefined();
    expect(defaultMetadata.robots).toMatchObject({
      index: true,
      follow: true,
    });
  });

  it("has Google Bot specific configuration", () => {
    expect(defaultMetadata.robots?.googleBot).toBeDefined();
    expect(defaultMetadata.robots?.googleBot).toMatchObject({
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    });
  });

  it("disables format detection", () => {
    expect(defaultMetadata.formatDetection).toEqual({
      email: false,
      address: false,
      telephone: false,
    });
  });

  it("has creator and publisher information", () => {
    expect(defaultMetadata.creator).toBe("SelfPublisherForge");
    expect(defaultMetadata.publisher).toBe("SelfPublisherForge");
  });

  it("has authors information", () => {
    expect(defaultMetadata.authors).toBeDefined();
    expect(Array.isArray(defaultMetadata.authors)).toBe(true);
    expect((defaultMetadata.authors as Array<{ name: string }>).length).toBeGreaterThan(0);
  });

  it("includes Open Graph image with correct dimensions", () => {
    expect(defaultMetadata.openGraph?.images).toBeDefined();
    const images = Array.isArray(defaultMetadata.openGraph?.images)
      ? defaultMetadata.openGraph?.images
      : [defaultMetadata.openGraph?.images];

    expect(images[0]).toMatchObject({
      width: 1200,
      height: 630,
      alt: "SelfPublisherForge",
    });
  });
});
