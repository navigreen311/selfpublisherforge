# /impl-feature — Plan & Implement a Complete Feature

Plan and implement a complete feature end-to-end (design -> code -> tests -> docs -> demo) in its own branch.

## Arguments

- **feature_name**: `$ARGUMENTS` (kebab-case short name, e.g., `user-auth`)
- **scope**: ui | api | fullstack | agent | infra
- **acceptance_criteria**: bullet list or Gherkin-style text
- **tech_constraints**: (optional) stack limits, required integrations
- **priority**: p0 | p1 | p2
- **perf_targets**: (optional) performance goals (e.g., "<200ms p95 latency")
- **security_notes**: (optional) security/compliance requirements

## Process

### Step 1: Understand & Plan
- Summarize the inputs and any ambiguities.
- Write a **mini-PRD**: problem statement, target users, success metrics, constraints, risks.
- Outline the architecture: components, data model, APIs, sequence flows.
- Define acceptance tests from the criteria provided.
- If critical info is missing, make a labeled `ASSUMPTION` and proceed.

### Step 2: Branch & Optional Worktree
- Create and checkout branch: `ai-feature/${feature_name}`
- If parallel work would help, create a git worktree and work inside it.
- Explain which git commands you run.

### Step 3: Implementation
- Modify all necessary layers according to scope (ui, api, fullstack, agent, infra).
- Keep **atomic Conventional Commits** (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- Follow SOLID principles and project conventions.
- Prefer cohesive, well-named modules with clear boundaries.

### Step 4: Tests
- Create or extend unit + integration tests covering acceptance criteria.
- Ensure the test command passes. Provide the exact command.
- Target meaningful coverage of the new/changed code.

### Step 5: Verification
- Build and run the app locally.
- Perform local smoke tests.
- Write a short demo script: commands to run + URLs to visit.

### Step 6: Docs
- Update `README.md` with the new feature.
- Add `docs/${feature_name}.md` with: overview, architecture, endpoints, env vars.
- Add a CHANGELOG entry (Added / Changed / Removed).

### Step 7: Deliverables
Provide a summary block:

```
## IMPLEMENTED
- [list of changes made]

## TESTED
- [test results, pass/fail, coverage]

## HOW TO RUN
- [commands to start the app]
- [commands to run tests]
- [demo steps / URLs]

## TRADEOFFS & FOLLOW-UPS
- [known limitations, future work]
```

## Error Handling
- On build/test failures: show logs, propose fixes, retry.
- On missing info: make clearly labeled `ASSUMPTION`s and explain how to change them later.

## Example Invocation

```
/impl-feature user-auth

scope: fullstack
acceptance_criteria:
  - Users can register with email/password
  - Users can log in and receive a JWT
  - Protected routes require valid JWT
  - Passwords are hashed with bcrypt
tech_constraints: Node.js, Express, PostgreSQL
priority: p0
security_notes: OWASP top 10 compliance, rate limiting on auth endpoints
```
