import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E test configuration for SelfPublisherForge frontend.
 *
 * Usage:
 *   npx playwright test              # run all E2E tests
 *   npx playwright test --ui         # open interactive UI mode
 *   npx playwright show-report       # view HTML report after a run
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: ".",
  testMatch: "**/*.spec.ts",

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry failed tests up to 2 times */
  retries: 2,

  /* Use a single worker in CI for stability, parallel locally */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter: list for CI, HTML for local development */
  reporter: process.env.CI ? "list" : "html",

  /* Global timeout: 30 seconds per test */
  timeout: 30_000,

  /* Shared settings for all projects below */
  use: {
    baseURL: "http://localhost:3000",

    /* Capture screenshot only on failure */
    screenshot: "only-on-failure",

    /* Collect trace on first retry for easier debugging */
    trace: "on-first-retry",

    /* Default navigation timeout */
    navigationTimeout: 15_000,
  },

  /* Output directory for test artifacts (screenshots, traces, etc.) */
  outputDir: "./test-results/",

  /* Run only Chromium for speed */
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /* Start the local dev server before running tests (disabled in CI where
     the server is managed separately by the workflow) */
  ...(process.env.CI
    ? {}
    : {
        webServer: {
          command: "npm run dev",
          url: "http://localhost:3000",
          reuseExistingServer: true,
          timeout: 120_000,
        },
      }),
});
