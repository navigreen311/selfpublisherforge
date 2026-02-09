# /code-review — Structured Code Review

Perform a structured, example-driven code review covering architecture, correctness, security, performance, and maintainability.

## Arguments

- **paths**: `$ARGUMENTS` (file paths or directories to review, space-separated)
- **style_examples**: (optional) paths to exemplary files that represent the desired code style
- **severity_threshold**: info | warning | error (minimum severity to report, default: warning)

## Process

### Step 1: Learn Style from Examples
- If `style_examples` provided, read those files first.
- Identify: naming conventions, architecture patterns, error handling style, module structure, documentation patterns, test patterns.
- If no examples provided, infer style from the existing codebase.

### Step 2: Review Against Checklist

For each file in `paths`, evaluate against:

**Architecture & Design**
- [ ] Single Responsibility — does each module/function do one thing?
- [ ] Proper abstractions — are boundaries clean?
- [ ] Dependency direction — do dependencies flow correctly?
- [ ] No circular dependencies

**Correctness**
- [ ] Logic errors or off-by-one bugs
- [ ] Null/undefined handling
- [ ] Error handling completeness
- [ ] Race conditions or concurrency issues
- [ ] Edge cases covered

**Security**
- [ ] Input validation and sanitization
- [ ] No hardcoded secrets or credentials
- [ ] SQL injection / XSS / CSRF protection
- [ ] Authentication and authorization checks
- [ ] Sensitive data exposure

**Performance**
- [ ] N+1 queries or unnecessary DB calls
- [ ] Memory leaks or unbounded growth
- [ ] Missing indexes (if DB-related)
- [ ] Unnecessary re-renders (if UI)
- [ ] Efficient data structures and algorithms

**Maintainability**
- [ ] Clear naming (variables, functions, files)
- [ ] Appropriate comments (why, not what)
- [ ] Consistent formatting and style
- [ ] Test coverage for new/changed code
- [ ] No dead code or unused imports

### Step 3: Produce Issues with Suggested Patches
For each finding:
- State the issue clearly.
- Classify severity: `ERROR` | `WARNING` | `INFO`.
- Show the current code snippet.
- Provide a suggested fix (diff-style or replacement).
- Explain why the change matters.

### Step 4: Summarize by Severity
Group findings: Errors first, then Warnings, then Info.
Include counts per category.

### Step 5: Output PR Comment

```
## Code Review Summary

**Files reviewed:** X
**Findings:** X errors, X warnings, X info

### Errors (must fix)
1. [file:line] — description + suggested fix

### Warnings (should fix)
1. [file:line] — description + suggested fix

### Info (consider)
1. [file:line] — description + suggested fix

### Positive Highlights
- [things done well worth noting]

### Overall Assessment
[1-2 sentence summary: ship / fix errors first / needs rework]
```

## Example Invocation

```
/code-review src/services/ src/routes/

style_examples: src/services/user-service.ts, src/routes/health.ts
severity_threshold: warning
```
