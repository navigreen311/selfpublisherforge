# W13: Fix Header Search + Notifications Button + Accessibility

## Branch: `fix/w13-header-search-notifications`

## Files YOU Own (only modify these):
- `frontend/src/components/layout/header.tsx`

## Task

### Fix 1: Non-functional search input (lines ~99-104)

The search input has no `onChange` handler. Implement basic search functionality:

1. Add state for search:
```tsx
const [searchQuery, setSearchQuery] = useState("");
const router = useRouter();
```

2. Add handler:
```tsx
const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
  if (e.key === "Enter" && searchQuery.trim()) {
    router.push(`/market?q=${encodeURIComponent(searchQuery.trim())}`);
    setSearchQuery("");
  }
};
```

3. Wire up the input:
```tsx
<Input
  placeholder="Search books, keywords, markets..."
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  onKeyDown={handleSearch}
  className="..."
  aria-label="Search"
/>
```

### Fix 2: Non-functional notifications button (line ~130)

The bell icon button has no onClick handler. Add basic notification dropdown or navigation:

```tsx
<Button
  variant="ghost"
  size="icon"
  onClick={() => router.push("/settings")}
  aria-label="Notifications"
>
  <Bell className="h-5 w-5" />
</Button>
```

### Fix 3: Accessibility — Add aria-labels

Add `aria-label` to:
- Search input: `aria-label="Search books, keywords, and markets"`
- Theme toggle button: `aria-label="Toggle theme"`
- Any other icon-only buttons missing labels

### Import Requirements
Make sure `useState` and `useRouter` are imported:
```tsx
import { useState } from "react";
import { useRouter } from "next/navigation";
```

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```
