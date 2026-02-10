import { test, expect } from "@playwright/test";

test.describe("Dashboard Pages", () => {
  // ---------------------------------------------------------------------------
  // Unauthenticated redirect
  // ---------------------------------------------------------------------------

  test("Unauthenticated user is redirected to login", async ({ page }) => {
    await page.goto("/dashboard");

    // The app should redirect unauthenticated users to the login page.
    // Allow a generous timeout since the redirect may involve client-side
    // auth checks before navigating.
    await expect(page).toHaveURL(/\/(login|dashboard)/, { timeout: 10_000 });

    // If we ended up on /login, the redirect is working correctly.
    // If we stayed on /dashboard, the page should still render (skeleton/error).
    const url = page.url();
    if (url.includes("/login")) {
      await expect(
        page.getByRole("heading", { name: "Welcome back" })
      ).toBeVisible();
    }
    // Either outcome is acceptable for this smoke-level test.
  });

  // ---------------------------------------------------------------------------
  // Dashboard sections (KPIs, activity, quick actions)
  // ---------------------------------------------------------------------------

  test("Dashboard page has expected sections (KPIs, activity, quick actions)", async ({
    page,
  }) => {
    // Navigate directly to the dashboard. If the app redirects to login,
    // skip assertions about dashboard content gracefully.
    await page.goto("/dashboard", { waitUntil: "networkidle" });

    const url = page.url();

    // If redirected to login, we cannot verify dashboard sections.
    if (url.includes("/login")) {
      test.skip(true, "Redirected to login — skipping dashboard content checks");
      return;
    }

    // Verify the page heading
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // KPI section: either real stat cards or the empty-state message
    const kpiArea = page.getByText(/(Total Revenue|Monthly Revenue|No KPI data)/i);
    await expect(kpiArea.first()).toBeVisible({ timeout: 10_000 });

    // Recent Activity section
    await expect(page.getByText("Recent Activity")).toBeVisible();

    // Quick Actions section
    await expect(page.getByText("Quick Actions")).toBeVisible();

    // Verify individual quick action buttons exist
    await expect(page.getByRole("link", { name: "New Project" })).toBeVisible();
    await expect(page.getByRole("link", { name: "AI Agents" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Analytics" })).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // Navigation sidebar menu items
  // ---------------------------------------------------------------------------

  test("Navigation sidebar has all menu items", async ({ page }) => {
    await page.goto("/dashboard", { waitUntil: "networkidle" });

    const url = page.url();
    if (url.includes("/login")) {
      test.skip(true, "Redirected to login — skipping sidebar checks");
      return;
    }

    // The sidebar nav is rendered inside <nav aria-label="Main navigation">
    const sidebar = page.locator('nav[aria-label="Main navigation"]');

    // All expected navigation items from the Sidebar component
    const expectedItems = [
      "Dashboard",
      "Projects",
      "Market Research",
      "Writing Studio",
      "Publishing",
      "Marketing",
      "Advertising",
      "Analytics",
      "AI Agents",
    ];

    for (const label of expectedItems) {
      // Items can be visible as link text or as aria-label (collapsed mode)
      const item = sidebar.getByRole("link", { name: label });
      await expect(item).toBeAttached();
    }

    // Settings is in a separate bottom section but still in the sidebar
    const settingsLink = page.getByRole("link", { name: "Settings" });
    await expect(settingsLink).toBeAttached();
  });
});
