# W20: KDP Failure-Proofing System (Module #18)
**Branch:** `ai-feature/kdp-validation`
**Scope:** api

## Mission
Build the KDP Failure-Proofing System: pre-flight validation that catches formatting errors, compliance issues, and policy violations before Amazon KDP submission. Goal: catch 95%+ of common rejection reasons.

## API Endpoints
- POST /api/v1/publishing/validate — Run full pre-flight validation
- POST /api/v1/publishing/validate/print — Print file validation (margins, bleed, spine)
- POST /api/v1/publishing/validate/ebook — Ebook validation (TOC, images, links)
- POST /api/v1/publishing/validate/cover — Cover validation (resolution, safe zones, dimensions)
- GET /api/v1/publishing/validate/{id}/results — Get validation results
- POST /api/v1/publishing/compliance-scan — Content compliance scan (policy violations, trademarks)

## Validation Rules

### Print Validation
- Margins: verify minimum margins per trim size (e.g., 6x9: 0.5" inside, 0.25" outside)
- Bleed: 0.125" bleed on all sides for full-bleed covers
- Spine width calculation based on page count and paper type
- Font embedding check
- Image resolution >= 300 DPI
- Color space (CMYK for covers, RGB for interior)
- Page count within KDP limits

### Ebook Validation
- Valid Table of Contents (NCX + HTML TOC)
- Image format (JPG/PNG, max 5MB per image)
- Internal links functional
- No JavaScript or external resources
- Font size recommendations
- File size within limits

### Cover Validation
- Resolution >= 300 DPI (print), >= 72 DPI (ebook)
- Dimensions match trim size + bleed
- Safe zones (no text in bleed area)
- File format (TIFF/PNG for print, JPG for ebook)
- Color space compliance

### Compliance
- Content policy keywords/patterns
- Trademark detection (e.g., "Kindle Unlimited" in title)
- Category appropriateness
- Description HTML compliance

## What to Build

### Backend
1. **backend/app/modules/kdp_validation/__init__.py**
2. **backend/app/modules/kdp_validation/router.py** — All endpoints
3. **backend/app/modules/kdp_validation/schemas.py** — ValidationRequest, ValidationResult, ValidationIssue(severity: error/warning/info, rule, message, location)
4. **backend/app/modules/kdp_validation/service.py** — Orchestrate validation pipeline, aggregate results
5. **backend/app/modules/kdp_validation/print_validator.py** — Print file validation rules
6. **backend/app/modules/kdp_validation/ebook_validator.py** — Ebook validation rules
7. **backend/app/modules/kdp_validation/cover_validator.py** — Cover validation rules
8. **backend/app/modules/kdp_validation/compliance_scanner.py** — Content compliance scanning (policy keywords, trademarks)
9. **backend/app/modules/kdp_validation/rules.py** — Validation rule definitions (trim sizes, margin specs, etc.)

### Tests
10. **backend/tests/unit/test_print_validator.py** — Test margin, bleed, spine calculations
11. **backend/tests/unit/test_ebook_validator.py** — Test TOC, image, link validation
12. **backend/tests/unit/test_cover_validator.py** — Test resolution, dimension, safe zone checks
13. **backend/tests/integration/test_validation_api.py**

## Database Tables (from W02, read-only)
upload_validations, compliance_scans

## Commit Convention
`feat(kdp): implement KDP failure-proofing with print, ebook, cover, and compliance validation`
