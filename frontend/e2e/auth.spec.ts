import { test, expect } from "@playwright/test";

test.describe("Authentication Pages", () => {
  // ---------------------------------------------------------------------------
  // Login page
  // ---------------------------------------------------------------------------

  test("Login page renders with email and password fields", async ({ page }) => {
    await page.goto("/login");

    // Page title / heading
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();

    // Email input
    await expect(page.getByPlaceholder("you@example.com")).toBeVisible();

    // Password input
    await expect(page.getByPlaceholder("Enter your password")).toBeVisible();

    // Sign in button
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // Register page
  // ---------------------------------------------------------------------------

  test("Register page renders with all required fields", async ({ page }) => {
    await page.goto("/register");

    // Page title / heading
    await expect(
      page.getByRole("heading", { name: "Create your account" })
    ).toBeVisible();

    // Full Name
    await expect(page.getByPlaceholder("John Doe")).toBeVisible();

    // Email
    await expect(page.getByPlaceholder("you@example.com")).toBeVisible();

    // Password
    await expect(page.getByPlaceholder("Create a password")).toBeVisible();

    // Organization Name (optional but present)
    await expect(
      page.getByPlaceholder("My Publishing House (optional)")
    ).toBeVisible();

    // Plan selector
    await expect(page.getByText("Free")).toBeVisible();

    // Submit button
    await expect(
      page.getByRole("button", { name: "Create account" })
    ).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // Login with invalid credentials
  // ---------------------------------------------------------------------------

  test("Login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");

    // Fill in bogus credentials
    await page.getByPlaceholder("you@example.com").fill("invalid@test.com");
    await page.getByPlaceholder("Enter your password").fill("WrongPassword123!");

    // Submit the form
    await page.getByRole("button", { name: "Sign in" }).click();

    // Expect an error alert to appear (the app shows a destructive Alert)
    const alert = page.locator('[role="alert"], [data-destructive]');
    await expect(alert.first()).toBeVisible({ timeout: 10_000 });
  });

  // ---------------------------------------------------------------------------
  // Navigation between login and register
  // ---------------------------------------------------------------------------

  test("Navigation between login and register works", async ({ page }) => {
    // Start on login
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login/);

    // Click "Create account" link to go to register
    await page.getByRole("link", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/register/);

    // Verify we are on the register page
    await expect(
      page.getByRole("heading", { name: "Create your account" })
    ).toBeVisible();

    // Click "Sign in" link to go back to login
    await page.getByRole("link", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/login/);

    // Verify we are back on the login page
    await expect(
      page.getByRole("heading", { name: "Welcome back" })
    ).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // Forgot password page
  // ---------------------------------------------------------------------------

  test("Forgot password page is accessible", async ({ page }) => {
    // Navigate from login page via the "Forgot password?" link
    await page.goto("/login");
    await page.getByRole("link", { name: "Forgot password?" }).click();
    await expect(page).toHaveURL(/\/forgot-password/);

    // Verify heading
    await expect(
      page.getByRole("heading", { name: "Forgot your password?" })
    ).toBeVisible();

    // Email field should be present
    await expect(page.getByPlaceholder("you@example.com")).toBeVisible();

    // Submit button
    await expect(
      page.getByRole("button", { name: "Send reset link" })
    ).toBeVisible();

    // "Sign in" link back to login
    await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();
  });
});
