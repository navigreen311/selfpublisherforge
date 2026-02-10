# E2E Tests (Playwright)

End-to-end tests for the SelfPublisherForge frontend using [Playwright](https://playwright.dev/).

## Prerequisites

Playwright is already listed as a dev dependency (`@playwright/test`) in `frontend/package.json`. After running `npm install` you only need to install the browser binaries:

```bash
npx playwright install
```

To install Chromium with all OS-level dependencies (useful on CI or fresh machines):

```bash
npx playwright install --with-deps chromium
```

## Running Tests

Run all E2E tests:

```bash
npx playwright test
```

Run a specific test file:

```bash
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/dashboard.spec.ts
```

Run in headed mode (see the browser):

```bash
npx playwright test --headed
```

Run in interactive UI mode:

```bash
npx playwright test --ui
```

## Viewing Reports

After a test run, open the HTML report:

```bash
npx playwright show-report
```

## Configuration

The Playwright configuration lives at `frontend/e2e/playwright.config.ts`. Key settings:

| Setting        | Value                               |
| -------------- | ----------------------------------- |
| Base URL       | `http://localhost:3000`             |
| Browser        | Chromium only (for speed)           |
| Retries        | 2                                   |
| Test timeout   | 30 seconds                          |
| Screenshots    | On failure only                     |
| Output dir     | `frontend/e2e/test-results/`        |

When running locally, the config automatically starts the dev server (`npm run dev`) if it is not already running. In CI, the server is managed by the GitHub Actions workflow.

## Gitignore

The following directories should be added to `.gitignore` to avoid committing test artifacts:

```
# Playwright
test-results/
playwright-report/
```

These directories contain screenshots, traces, and HTML reports generated during test runs.

## Test Structure

```
frontend/e2e/
  playwright.config.ts   # Playwright configuration
  auth.spec.ts           # Authentication page tests (login, register, forgot password)
  dashboard.spec.ts      # Dashboard page tests (sections, sidebar navigation)
  test-results/          # Generated test artifacts (gitignored)
  README.md              # This file
```

## CI Integration

E2E tests run automatically in the CI pipeline via the `e2e-smoke` job in `.github/workflows/ci.yml`. The CI workflow:

1. Starts the backend (Python/FastAPI) and frontend (Next.js) servers
2. Installs Chromium with dependencies
3. Runs Playwright tests against `http://localhost:3000`
4. Uploads screenshots and reports as artifacts on failure
