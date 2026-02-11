import { test, expect } from "@playwright/test";

/**
 * New Module Pages Smoke Tests (@smoke)
 *
 * Lightweight E2E checks that verify all newly added module pages are reachable
 * and render without server errors. These tests ensure that:
 *   - Each page route is correctly configured
 *   - Pages don't return 5xx errors
 *   - Basic page structure loads (visible body content)
 *   - Auth redirects work properly for protected routes
 *
 * All tests tolerate auth redirects (redirecting to /login is expected for
 * unauthenticated requests and should not be treated as a failure).
 *
 * New module pages tested:
 *   - /admin                      - Admin dashboard
 *   - /cover-design              - Cover design tool
 *   - /reviews                   - Review management
 *   - /competitors               - Competitor analysis
 *   - /style-profiles            - Writing style profiles
 *   - /pricing                   - Pricing optimizer
 *   - /analytics/portfolio       - Portfolio analytics
 *   - /publishing/validation     - Publishing validation
 */
test.describe("New Module Pages @smoke", () => {
  const newPages = [
    {
      path: "/admin",
      title: "Admin",
      description: "Admin dashboard and system management",
    },
    {
      path: "/cover-design",
      title: "Cover Design",
      description: "AI-powered cover design tool",
    },
    {
      path: "/reviews",
      title: "Review",
      description: "Review management and analysis",
    },
    {
      path: "/competitors",
      title: "Competitor",
      description: "Competitor analysis dashboard",
    },
    {
      path: "/style-profiles",
      title: "Style",
      description: "Writing style profiles and templates",
    },
    {
      path: "/pricing",
      title: "Pricing",
      description: "Pricing optimizer and market analysis",
    },
    {
      path: "/analytics/portfolio",
      title: "Portfolio",
      description: "Portfolio analytics and insights",
    },
    {
      path: "/publishing/validation",
      title: "Validation",
      description: "Publishing validation and quality checks",
    },
  ];

  // ---------------------------------------------------------------------------
  // Test each new module page
  // ---------------------------------------------------------------------------

  for (const pageInfo of newPages) {
    test(`${pageInfo.path} renders without errors`, async ({ page }) => {
      // Navigate to the page and wait for DOM content to load
      const response = await page.goto(
        `http://localhost:3000${pageInfo.path}`,
        {
          waitUntil: "domcontentloaded",
          timeout: 30_000,
        }
      );

      // Verify the response was received (not null)
      expect(response).not.toBeNull();

      // Verify no 5xx server errors (4xx like 401/403 are acceptable for
      // protected routes that redirect to login)
      expect(response!.status()).toBeLessThan(500);

      // The page may redirect to /login for auth - this is expected and valid.
      // What matters is that the server didn't crash with a 500 error.
      const finalUrl = page.url();

      // If we're still on the target page (not redirected), verify it has
      // visible content. If redirected to login, that's also acceptable.
      if (finalUrl.includes(pageInfo.path)) {
        // On the target page - verify body is visible
        await expect(page.locator("body")).toBeVisible();

        // Optional: verify the page title contains relevant keywords
        const title = await page.title();
        expect(title).toBeTruthy();
        expect(title.toLowerCase()).not.toMatch(/error|not found|404/);
      } else if (finalUrl.includes("/login")) {
        // Redirected to login - this is acceptable for protected routes
        console.log(
          `✓ ${pageInfo.path} redirected to login (auth required - expected)`
        );
      } else {
        // Unexpected redirect - log but don't fail (could be other valid
        // redirects like onboarding, etc.)
        console.log(
          `⚠ ${pageInfo.path} redirected to ${finalUrl} (unexpected but not necessarily an error)`
        );
      }

      // Capture screenshot for visual verification in case of failures
      await page.screenshot({
        path: `test-results/${pageInfo.path.replace(/\//g, "-")}-page.png`,
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Batch verification: all pages accessible
  // ---------------------------------------------------------------------------

  test("All new module pages are accessible (batch check)", async ({
    page,
  }) => {
    // Quick batch verification that all pages return < 500 status
    // This test runs after individual tests and provides a summary check
    const results: Array<{ path: string; status: number; ok: boolean }> = [];

    for (const pageInfo of newPages) {
      try {
        const response = await page.goto(
          `http://localhost:3000${pageInfo.path}`,
          {
            waitUntil: "domcontentloaded",
            timeout: 15_000,
          }
        );

        results.push({
          path: pageInfo.path,
          status: response?.status() ?? 0,
          ok: (response?.status() ?? 500) < 500,
        });
      } catch (error) {
        // Mark as failed but don't throw - we want to check all pages
        results.push({
          path: pageInfo.path,
          status: 0,
          ok: false,
        });
        console.error(`Failed to load ${pageInfo.path}:`, error);
      }
    }

    // Log summary
    console.log("\n=== New Module Pages Status Summary ===");
    results.forEach((r) => {
      const emoji = r.ok ? "✓" : "✗";
      console.log(`${emoji} ${r.path.padEnd(30)} → HTTP ${r.status}`);
    });
    console.log("======================================\n");

    // All pages should have returned < 500
    const failedPages = results.filter((r) => !r.ok);
    expect(failedPages).toHaveLength(0);
  });
});
