# W20: Add ISBN/ASIN Validation to MetadataForm

## Branch: `fix/w20-metadata-form-validation`

## Files YOU Own (only modify these):
- `frontend/src/modules/publishing/components/MetadataForm.tsx`

## Task

### Fix 1: Add ISBN format validation (line ~228)

Add ISBN-10 and ISBN-13 validation:

```tsx
const isValidISBN = (isbn: string): boolean => {
  const cleaned = isbn.replace(/[-\s]/g, "");
  if (cleaned.length === 10) {
    // ISBN-10: sum of (digit * position) mod 11 == 0
    let sum = 0;
    for (let i = 0; i < 10; i++) {
      const char = cleaned[i];
      const val = char === "X" && i === 9 ? 10 : parseInt(char, 10);
      if (isNaN(val)) return false;
      sum += val * (10 - i);
    }
    return sum % 11 === 0;
  }
  if (cleaned.length === 13) {
    // ISBN-13: alternating 1,3 weights, sum mod 10 == 0
    let sum = 0;
    for (let i = 0; i < 13; i++) {
      const val = parseInt(cleaned[i], 10);
      if (isNaN(val)) return false;
      sum += val * (i % 2 === 0 ? 1 : 3);
    }
    return sum % 10 === 0;
  }
  return false;
};
```

Wire validation to the ISBN input with error state.

### Fix 2: Add ASIN validation (line ~238)

```tsx
const isValidASIN = (asin: string): boolean => {
  // ASIN: 10 alphanumeric characters, typically starting with B
  return /^[A-Z0-9]{10}$/.test(asin.toUpperCase());
};
```

Show validation hint next to ASIN field.

### Fix 3: Enforce keyword max limit (lines ~189-201)

The form shows keyword count but doesn't prevent adding more than 7 (Amazon KDP limit):

```tsx
const MAX_KEYWORDS = 7;
// In the handler:
if (keywords.length >= MAX_KEYWORDS) {
  toast.error(`Maximum ${MAX_KEYWORDS} keywords allowed`);
  return;
}
```

Also add visual feedback showing `{keywords.length}/{MAX_KEYWORDS}`.

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "MetadataForm" || echo "No type errors"
```
