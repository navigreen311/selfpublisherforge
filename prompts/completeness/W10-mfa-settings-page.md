# W10: MFA Settings Page

## Files to create
- `frontend/src/app/(dashboard)/settings/security/page.tsx` — NEW

## Files to modify
- `frontend/src/app/(dashboard)/settings/page.tsx` — Add "Security" nav link

## Context
Backend MFA endpoints already exist:
- POST `/api/v1/auth/mfa/setup` — Returns `{ "secret": "...", "qr_code_url": "...", "backup_codes": [...] }`
- POST `/api/v1/auth/mfa/verify` — body: `{ "code": "123456" }` — Activates MFA
- POST `/api/v1/auth/mfa/disable` — body: `{ "password": "..." }` — Disables MFA

The settings section has existing pages: profile, api-keys, organization, billing.

## Task

### 1. Create security/page.tsx

Page with three states:
1. **MFA Not Enabled** — Show "Enable Two-Factor Authentication" button with description of benefits
2. **MFA Setup In Progress** — After clicking enable:
   - Call POST `/api/v1/auth/mfa/setup`
   - Display QR code (use the qr_code_url as an img src, or generate from secret using a QR library)
   - Show the secret key as text for manual entry
   - Show input for 6-digit TOTP code to verify
   - Display backup codes with "Copy" and "Download" buttons
   - On verify success, transition to "MFA Enabled" state
3. **MFA Enabled** — Show "Disable Two-Factor Authentication" button
   - Requires password confirmation dialog
   - On disable, revert to "MFA Not Enabled" state

```tsx
"use client";
import { useState } from "react";
import { useCurrentUser } from "@/modules/users/hooks";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
```

### 2. Add Security tab to settings navigation

The settings page at `frontend/src/app/(dashboard)/settings/page.tsx` redirects to /settings/profile. Check if there's a settings layout with tabs/sidebar navigation. Add a "Security" link pointing to `/settings/security`.

### 3. Backup codes display

Show backup codes in a grid with a "Copy All" button and a "Download as .txt" button. Warn users to save these codes securely.
