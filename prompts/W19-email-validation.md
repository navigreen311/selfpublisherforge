# W19: Add Email Validation to EmailSequenceBuilder

## Branch: `fix/w19-email-validation`

## Files YOU Own (only modify these):
- `frontend/src/modules/marketing/components/EmailSequenceBuilder.tsx`

## Task

### Fix 1: Add email validation for recipient input (line ~230-234)

The comma-separated email list input has no validation.

1. Add a validation helper:
```tsx
const isValidEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
};

const validateEmails = (input: string): { valid: string[]; invalid: string[] } => {
  const emails = input.split(",").map(e => e.trim()).filter(Boolean);
  const valid = emails.filter(isValidEmail);
  const invalid = emails.filter(e => !isValidEmail(e));
  return { valid, invalid };
};
```

2. Add validation on form submit or on blur:
```tsx
const handleRecipientsChange = (value: string) => {
  setRecipients(value);
  if (value) {
    const { invalid } = validateEmails(value);
    if (invalid.length > 0) {
      setEmailError(`Invalid email(s): ${invalid.join(", ")}`);
    } else {
      setEmailError("");
    }
  }
};
```

3. Show validation error below the input:
```tsx
{emailError && (
  <p className="text-sm text-destructive mt-1">{emailError}</p>
)}
```

4. Prevent form submission if there are invalid emails.

### Fix 2: Add aria-current to status badges (line ~96-103)

```tsx
<span aria-current={isActive ? "step" : undefined}>
  {status}
</span>
```

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "EmailSequence" || echo "No type errors"
```
