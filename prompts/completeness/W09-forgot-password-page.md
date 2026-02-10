# W09: Forgot Password + Reset Password Pages

## Files to create
- `frontend/src/app/(auth)/forgot-password/page.tsx` — NEW
- `frontend/src/app/(auth)/reset-password/page.tsx` — NEW

## Context
Backend endpoints already exist:
- POST `/api/v1/auth/forgot-password` — body: `{ "email": "..." }` — Returns 200 always (no email enumeration)
- POST `/api/v1/auth/reset-password` — body: `{ "token": "...", "new_password": "..." }`

The login page at `frontend/src/app/(auth)/login/page.tsx` already has a `<Link href="/forgot-password">` link.

Follow the same patterns as login/register pages for styling (Card, Input, Button from shadcn/ui).

## Task

### 1. Create forgot-password/page.tsx

```tsx
"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/v1/auth/forgot-password", { email });
      setSubmitted(true);
    } catch {
      // Always show success to prevent email enumeration
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (/* Success message: "Check your email for a reset link" with link back to login */);
  }

  return (/* Form with email input, submit button, and back to login link */);
}
```

### 2. Create reset-password/page.tsx

Takes `?token=xxx` from URL query params. Shows a form with new password + confirm password fields. On submit, calls `/api/v1/auth/reset-password`. On success, redirects to login with success message.

```tsx
"use client";
import { useSearchParams, useRouter } from "next/navigation";
// ... form with password, confirmPassword, validation, submit
```

Add password strength validation (min 8 chars, uppercase, lowercase, number). Show validation errors inline.

### 3. Style consistency

Match the visual style of the existing login and register pages. Use the same Card layout, spacing, and color scheme.
