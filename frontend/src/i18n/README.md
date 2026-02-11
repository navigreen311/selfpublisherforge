# Internationalization (i18n) Setup

This directory contains the internationalization configuration for SelfPublisherForge using `next-intl`.

## Structure

```
frontend/src/
├── i18n/
│   ├── config.ts         # Locale configuration (supported locales, defaults)
│   ├── request.ts        # Next.js i18n request handler
│   └── __tests__/
│       └── config.test.ts
├── messages/
│   ├── en.json          # English translations (240+ strings)
│   ├── es.json          # Spanish translations (placeholder)
│   └── de.json          # German translations (placeholder)
├── hooks/
│   └── use-translations.ts  # Translation hook wrappers
└── components/shared/
    └── LanguageSwitcher.tsx # Language dropdown component
```

## Supported Locales

- **English (en)** - Default locale, complete translations
- **Spanish (es)** - Placeholder translations (machine-translated)
- **German (de)** - Placeholder translations (machine-translated)

## Usage

### Using Translations in Components

```tsx
import { useTranslations } from "@/hooks/use-translations";

export function MyComponent() {
  const t = useTranslations("common");

  return (
    <button>{t("save")}</button>
  );
}
```

### Namespace-Specific Hooks

For convenience, use the pre-defined namespace hooks:

```tsx
import {
  useCommonTranslations,
  useAuthTranslations,
  useNavigationTranslations,
  useErrorTranslations
} from "@/hooks/use-translations";

export function LoginForm() {
  const tAuth = useAuthTranslations();
  const tCommon = useCommonTranslations();

  return (
    <form>
      <h1>{tAuth("login")}</h1>
      <button>{tCommon("save")}</button>
    </form>
  );
}
```

### Language Switcher

Add the language switcher to your header or settings page:

```tsx
import { LanguageSwitcher } from "@/components/shared/LanguageSwitcher";

export function Header() {
  return (
    <header>
      <LanguageSwitcher />
    </header>
  );
}
```

#### LanguageSwitcher Props

- `currentLocale?: Locale` - Current active locale (default: "en")
- `onLocaleChange?: (locale: Locale) => void` - Callback when locale changes
- `className?: string` - Custom className for the trigger button
- `compact?: boolean` - Show only icon without text (default: false)

## Message Organization

Messages are organized by module/feature:

- `common` - Shared terms (save, cancel, delete, etc.)
- `navigation` - Navigation labels
- `auth` - Authentication and registration
- `dashboard` - Dashboard page
- `writing` - Writing Studio
- `projects` - Projects module
- `market` - Market Research
- `knowledge` - Knowledge Vault
- `publishing` - Publishing module
- `pipeline` - Production Pipeline
- `marketing` - Marketing module
- `productPage` - Product Page Lab
- `advertising` - Advertising module
- `analytics` - Analytics module
- `agents` - AI Agents module
- `settings` - Settings module
- `billing` - Billing module
- `errors` - Error messages
- `emptyStates` - Empty state messages
- `confirmDialog` - Confirmation dialog messages
- `validation` - Form validation messages
- `accessibility` - Accessibility labels

## Adding New Translations

### 1. Add to English messages (`messages/en.json`)

```json
{
  "myModule": {
    "title": "My Module",
    "description": "This is my module"
  }
}
```

### 2. Add corresponding translations to other locales

Update `es.json` and `de.json` with the same keys.

### 3. Use in components

```tsx
const t = useTranslations("myModule");
return <h1>{t("title")}</h1>;
```

## Translation Parameters

Use curly braces for dynamic values:

```json
{
  "welcome": "Welcome, {name}!",
  "itemCount": "You have {count} items"
}
```

```tsx
t("welcome", { name: user.name })
t("itemCount", { count: items.length })
```

## Pluralization

next-intl supports ICU message format for pluralization:

```json
{
  "itemCount": "{count, plural, =0 {No items} =1 {One item} other {# items}}"
}
```

## Integration with Next.js App Router

To fully enable next-intl with App Router routing:

1. Update `next.config.js` to add i18n routing
2. Create locale-specific layout wrappers
3. Update middleware for locale detection
4. Configure the `i18n/request.ts` handler

See [next-intl documentation](https://next-intl-docs.vercel.app/) for full integration guide.

## Testing

Tests are located in:
- `src/i18n/__tests__/config.test.ts` - Configuration tests
- `src/components/shared/__tests__/LanguageSwitcher.test.tsx` - Component tests

Run tests:
```bash
npm test -- i18n
npm test -- LanguageSwitcher
```

## Translation Status

| Locale | Status | Strings | Notes |
|--------|--------|---------|-------|
| en | ✅ Complete | 240+ | Extracted from codebase |
| es | ⚠️ Placeholder | 240+ | Machine-translated, needs review |
| de | ⚠️ Placeholder | 240+ | Machine-translated, needs review |

## Next Steps

1. **Professional Translation**: Replace machine-translated Spanish and German with professional translations
2. **Additional Locales**: Add more languages as needed (fr, pt, ja, etc.)
3. **RTL Support**: Add RTL language support (ar, he) if needed
4. **Date/Number Formatting**: Configure locale-specific formatting
5. **Integration**: Integrate with Next.js App Router for locale-based routing
