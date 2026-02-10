# W12: Product Page Lab — Replace Placeholder Data with Real DB Logic

## Files to modify
- `backend/app/modules/product_page_lab/service.py` — Wire to real DB queries

## Context
The Product Page Lab handles A/B testing for book listings (titles, descriptions, covers). The service may use placeholder/hardcoded data for test results. The DB model `ABTest` exists in the module.

## Task

### 1. Read the current service

Read `backend/app/modules/product_page_lab/service.py` and identify any placeholder data, hardcoded results, or in-memory stores.

### 2. Replace with real DB queries

If any methods return hardcoded/synthetic data, replace them with proper SQLAlchemy queries against the ABTest model and related tables.

Ensure:
- `create_test()` — Creates a real ABTest record in DB
- `list_tests()` — Queries DB with proper filtering by org_id
- `get_test()` — Fetches single test by ID
- `update_test()` — Updates test record
- `get_test_results()` — Returns real test metrics (or computed from tracked events)

### 3. If the service already uses DB properly

If the service already uses the database correctly, look for other gaps:
- Are all service methods passing through to DB?
- Are there any TODO comments that need implementing?
- Is the statistical significance calculation implemented?
- Does the blurb generation integrate with the AI writing module?

### 4. Fix any issues found

Address whatever placeholder data or incomplete logic you find in the service layer.
