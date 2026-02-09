# /test-suite — Create or Extend Automated Test Suite

Create or extend an automated test suite (unit, integration, e2e) and wire it into CI if requested.

## Arguments

- **target**: `$ARGUMENTS` (file path, module, or "all" for full project)
- **coverage_goal**: percentage target (e.g., "80%")
- **test_kinds**: unit | integration | e2e | all (comma-separated)
- **ci_provider**: (optional) github-actions | gitlab-ci | circleci | none
- **seed_data**: (optional) path to fixtures or description of test data needed

## Process

### Step 1: Inventory Existing Tests
- Scan the project for existing test files, frameworks, and configurations.
- List what is currently tested and what is not.
- Identify the test runner and assertion library in use.

### Step 2: Identify Gaps
- Compare existing tests against the target modules/features.
- Identify untested code paths, edge cases, and error scenarios.
- Prioritize gaps by risk and impact.

### Step 3: Add Tests
- Write new test files following existing project conventions.
- Cover: happy paths, error cases, edge cases, boundary conditions.
- For **unit tests**: isolate with mocks/stubs where appropriate.
- For **integration tests**: test real interactions between components.
- For **e2e tests**: simulate user workflows end-to-end.

### Step 4: Fixtures & Teardown
- Create or update test fixtures and seed data.
- Ensure proper setup/teardown to avoid test pollution.
- Use factories or builders for complex test data.

### Step 5: Test Scripts
- Add or update npm scripts (or equivalent) for running tests:
  - `test` — run all tests
  - `test:unit` — unit tests only
  - `test:integration` — integration tests only
  - `test:e2e` — e2e tests only
  - `test:coverage` — run with coverage reporting
- Ensure scripts are idempotent and can run in any environment.

### Step 6: CI Configuration (if ci_provider specified)
- Generate or update CI config for the chosen provider.
- Include: install deps, run linter, run tests, upload coverage.
- Add caching for dependencies to speed up builds.

### Step 7: Run & Summarize
- Execute the full test suite.
- Report: total tests, passed, failed, skipped, coverage percentage.
- List any failing tests with root cause analysis.

## Output

```
## TEST INVENTORY
- [existing test count and coverage before changes]

## NEW TESTS ADDED
- [list of new test files and what they cover]

## RESULTS
- Total: X | Passed: X | Failed: X | Skipped: X
- Coverage: X%

## COMMANDS
- Run all tests: `<command>`
- Run with coverage: `<command>`
- Run specific suite: `<command>`

## CI STATUS
- [CI config file path if created]
- [How to trigger / verify CI runs]
```

## Example Invocation

```
/test-suite src/services/

coverage_goal: 85%
test_kinds: unit, integration
ci_provider: github-actions
seed_data: Use factory functions for User, Product, Order models
```
