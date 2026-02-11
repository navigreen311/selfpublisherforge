import { test, expect } from "@playwright/test";

/**
 * Smoke Tests (@smoke)
 *
 * Lightweight end-to-end checks that verify the core surfaces of the app are
 * reachable and not returning server errors. These run on every CI push after
 * unit tests pass, acting as a fast gate before heavier E2E suites.
 *
 * Each test targets a different critical path:
 *   - API health endpoint (backend is alive)
 *   - Login page (primary entry point for users)
 *   - Registration page (onboarding funnel)
 *   - Dashboard page (authenticated landing, may redirect to login)
 */
test.describe("Smoke Tests @smoke", () => {
  // ---------------------------------------------------------------------------
  // API health check
  // ---------------------------------------------------------------------------

  test("API health check endpoint responds", async ({ request }) => {
    // The backend health endpoint may live at different paths depending on
    // configuration. Try all known variants with retry logic to tolerate slow
    // startup in CI environments.
    let response;
    let lastError: unknown;

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        response = await request.get("http://localhost:8000/api/health");
        if (response.ok()) break;

        response = await request.get("http://localhost:8000/health");
        if (response.ok()) break;

        response = await request.get("http://localhost:8000/docs");
        if (response.ok()) break;
      } catch (e) {
        lastError = e;
      }

      if (attempt < 3) {
        console.log(
          `Health check attempt ${attempt}/3 failed, retrying in 5s...`
        );
        await new Promise((r) => setTimeout(r, 5000));
      }
    }

    expect(response).toBeDefined();
    expect(response!.status()).toBeLessThan(500);
  });

  // ---------------------------------------------------------------------------
  // Login page
  // ---------------------------------------------------------------------------

  test("Login page loads", async ({ page }) => {
    // Verify the login page returns a successful HTTP status and the URL
    // resolves to /login (no unexpected redirect).
    const response = await page.goto("http://localhost:3000/login", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    expect(response).not.toBeNull();
    expect(response!.status()).toBeLessThan(400);
    await expect(page).toHaveURL(/login/);

    await page.screenshot({ path: "test-results/login-page.png" });
  });

  // ---------------------------------------------------------------------------
  // Registration page
  // ---------------------------------------------------------------------------

  test("Registration page loads", async ({ page }) => {
    // Verify the registration page returns a successful HTTP status and the
    // URL resolves to /register.
    const response = await page.goto("http://localhost:3000/register", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    expect(response).not.toBeNull();
    expect(response!.status()).toBeLessThan(400);
    await expect(page).toHaveURL(/register/);

    await page.screenshot({ path: "test-results/register-page.png" });
  });

  // ---------------------------------------------------------------------------
  // Dashboard page
  // ---------------------------------------------------------------------------

  test("Dashboard page loads (redirects to auth if needed)", async ({
    page,
  }) => {
    // The dashboard is behind authentication. A successful smoke test means
    // the page either renders the dashboard or redirects to /login -- both
    // indicate the app is functioning. A 5xx would signal a real problem.
    const response = await page.goto("http://localhost:3000/dashboard", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    expect(response).not.toBeNull();
    expect(response!.status()).toBeLessThan(500);

    // Dashboard should either load or redirect to login -- both are valid
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|login)/);

    await page.screenshot({ path: "test-results/dashboard-page.png" });
  });
});
