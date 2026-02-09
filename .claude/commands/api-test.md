# /api-test — Generate API Contract & Integration Tests

Generate API contract and integration tests from OpenAPI/GraphQL specs or live endpoints.

## Arguments

- **spec_path_or_url**: `$ARGUMENTS` (path to OpenAPI/GraphQL spec file, or base URL of live API)
- **auth_mode**: none | bearer | api-key | basic | oauth2
- **env**: local | staging | production (target environment)
- **test_style**: jest | vitest | pytest | mocha (test framework)
- **load_smoke**: (optional) true | false — generate basic load/smoke tests

## Process

### Step 1: Parse Spec or Discover Endpoints
- If spec file: parse OpenAPI/Swagger YAML/JSON or GraphQL schema.
- If live URL: probe common endpoints, read any available docs or spec endpoints (`/docs`, `/openapi.json`, `/graphql`).
- Build a complete inventory of endpoints: method, path, params, request body, response schema.

### Step 2: Generate Success & Error Tests
For each endpoint, generate tests covering:

**Success Cases (2xx)**
- Valid request with all required fields.
- Valid request with optional fields.
- Valid request with minimum payload.
- Pagination, filtering, sorting (if applicable).

**Error Cases (4xx/5xx)**
- Missing required fields (400).
- Invalid field types/formats (400).
- Unauthorized access (401).
- Forbidden access (403).
- Resource not found (404).
- Duplicate/conflict (409).
- Rate limiting (429) — if applicable.

**Edge Cases**
- Empty arrays/objects.
- Maximum length strings.
- Special characters and Unicode.
- Concurrent requests (if relevant).

### Step 3: Create Reusable Client & Helpers
- Build a test HTTP client wrapper with:
  - Base URL configuration per environment.
  - Auth header injection based on `auth_mode`.
  - Response assertion helpers (status, schema, headers).
  - Request/response logging for debugging.
- Create shared fixtures: test users, sample payloads, expected responses.

### Step 4: CLI for Environments
- Create a test runner script that accepts environment as a parameter.
- Support: `npm run test:api -- --env=local` (or equivalent).
- Include environment-specific config (base URLs, auth tokens placeholder).

### Step 5: Load Smoke Tests (if load_smoke = true)
- Generate basic load tests using k6, artillery, or autocannon.
- Target: key endpoints with realistic payloads.
- Metrics: requests/sec, p50/p95/p99 latency, error rate.
- Include a reasonable baseline config (10 VUs, 30s duration).

### Step 6: Run & Summarize
- Execute the full API test suite against the specified environment.
- Report: total tests, passed, failed, skipped.
- For failures: show request, expected response, actual response.

## Output

```
## ENDPOINTS DISCOVERED
- [method] [path] — [description]

## TESTS GENERATED
- tests/api/
  - [list of test files]
- tests/api/helpers/
  - [client, fixtures, assertions]

## RESULTS
- Total: X | Passed: X | Failed: X | Skipped: X
- Failing endpoints: [list with reason]

## COMMANDS
- Run API tests: `<command>`
- Run against staging: `<command>`
- Run load smoke: `<command>`

## REPORT
- [path to test report if generated]
```

## Example Invocation

```
/api-test ./openapi.yaml

auth_mode: bearer
env: local
test_style: vitest
load_smoke: true
```

Or with a live URL:

```
/api-test http://localhost:3000/api

auth_mode: api-key
env: local
test_style: jest
load_smoke: false
```
