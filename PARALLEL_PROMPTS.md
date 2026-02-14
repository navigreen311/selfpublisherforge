# 60 Parallel Claude Code Prompts
# Style Profiles + Knowledge Vault + Publishing Enhancements

Each prompt is self-contained. Workers 01-30 use existing worktrees fix01-fix30.
Workers 31-60 need new worktrees (or run sequentially after merge of 01-30).

All paths relative to repo root. Frontend: Next.js + React + TanStack Query + shadcn/ui + sonner toasts + `useTranslations()` i18n hook. Backend: FastAPI + SQLAlchemy async + Pydantic schemas.

---

## STYLE PROFILES — Frontend Components (Prompts 01-12)

### PROMPT-01: Style Profile Landing — ProfileCard Enhancement
**Branch:** `feat/sp-01-profile-card`
**File:** `frontend/src/modules/style-profiles/components/ProfileCard.tsx`

Read the existing `ProfileCard.tsx`. Rewrite it to show:
- Profile name with green dot active indicator if `style_card` exists
- Genre tag (badge)
- `style_card.summary` as the voice fingerprint description (2-line clamp)
- Key metrics row: readability (from `style_card.key_metrics.reading_level`), formality %, warmth %
- Sample count and total word count (`sample_count`, `word_count` from `ProfileResponse`)
- Three action buttons: "View Profile" (Link to `/style-profiles/{id}`), "Test Style" (Link to `/style-profiles/{id}?tab=test`), "..." menu (Edit, Duplicate, Delete via `onDelete` prop)

Use shadcn `Card`, `Badge`, `Button`, `DropdownMenu`. Import types from `../types`. Keep existing props interface compatible. Add `onDelete?: (id: string) => void` prop.

### PROMPT-02: Style Profile Landing — ProfileList Rewrite
**Branch:** `feat/sp-02-profile-list`
**File:** `frontend/src/modules/style-profiles/components/ProfileList.tsx`

Read existing `ProfileList.tsx`. Rewrite to:
- Accept `profiles: ProfileResponse[]`, `isLoading: boolean`, `onDelete?: (id: string) => void`
- Add sort dropdown: "Recent" (default by `updated_at`), "Name A-Z", "Oldest"
- Show profile count text: `"{n} profiles"`
- Grid layout: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
- Loading: 6 skeleton cards
- Empty state: Sparkles icon, "No style profiles yet", "Create your first style profile...", CTA button linking to `/style-profiles/new`
- Render `ProfileCard` for each profile, passing `onDelete`

### PROMPT-03: Style Profiles — Wizard Step 1 Presets
**Branch:** `feat/sp-03-wizard-presets`
**File:** `frontend/src/modules/style-profiles/components/PresetPicker.tsx` (NEW)

Create a new component `PresetPicker` that shows 5 style preset cards:
1. "Conversational Nonfiction" — "Warm, accessible, second person"
2. "Academic/Formal" — "Structured, evidence-based, third person"
3. "Storyteller Fiction" — "Vivid, sensory, past tense narrative"
4. "Journalistic" — "Clear, punchy, inverted pyramid"
5. "Technical" — "Precise, step-by-step, imperative mood"

Props: `selectedPreset: string | null`, `onSelect: (preset: string | null) => void`
Each card is a selectable button with ring-2 when selected. Display name + description. Clicking a selected card deselects it.

### PROMPT-04: Style Profiles — Wizard Step 1 Enhancement
**Branch:** `feat/sp-04-wizard-step1`
**File:** `frontend/src/app/(dashboard)/style-profiles/new/page.tsx`

Read the existing `new/page.tsx`. Enhance it:
- Change progress indicator from 2 steps to 3 steps (add "Analysis Results" as step 3)
- After the existing Genre field, add a "Quick Start" section:
  - Import and render `PresetPicker` (from `../../../modules/style-profiles/components/PresetPicker`)
  - Track `preset` state
- Add "Or describe your ideal voice" textarea (`voiceDescription` state) below the presets
- Pass `preset` and `voiceDescription` to Step 2 (store in component state)
- Update step 2 → step 3 flow: after samples, show analysis (step 3)

### PROMPT-05: Style Profiles — Wizard Step 2 Samples Enhancement
**Branch:** `feat/sp-05-wizard-samples`
**File:** `frontend/src/modules/style-profiles/components/TextIngestion.tsx`

Read existing `TextIngestion.tsx`. Enhance to support 3 input modes:
- **Upload Files** button: `<input type="file" accept=".docx,.txt,.md,.epub" multiple>`. On file select, read via FileReader, extract text, add to samples array.
- **Paste Text** button: Opens a textarea modal for direct paste. On submit, add text to samples array.
- **From Manuscript** button: Import `useBooks` from `@/modules/writing/hooks` and `useChapters`. Show a dropdown to pick a book, then a chapter list with checkboxes. On confirm, add chapter content to samples.

Show each sample as a card: label, word count, "Preview" button (expands text), "Remove" button.
Show totals: "N samples, X words (minimum: 1,000 words)" with green checkmark if >= 1000.
The `onSubmit` prop should receive `string[]` (the sample texts).

### PROMPT-06: Style Profiles — Analysis Results Component
**Branch:** `feat/sp-06-analysis-results`
**File:** `frontend/src/modules/style-profiles/components/AnalysisResults.tsx` (NEW)

Create `AnalysisResults` component. Props: `profileId: string`, `onBack: () => void`, `onSave: () => void`.

Use `useStyleProfile(profileId)` and `useStyleFingerprint(profileId)` hooks.

Show loading state: "Analyzing your writing style... This takes about 30 seconds" with spinner (poll profile until `status === 'ready'`).

When ready, display:
1. **Voice Fingerprint** card: `style_card.summary` in a bordered box with "Edit Description" button (no-op for now)
2. **Style Metrics** card: Import and render `StyleMetrics` component
3. **Voice Characteristics** card: Import and render `VoiceCharacteristics` component
4. **Sample Comparison** card: Import and render `SampleComparison` component
5. Footer: "Back to Samples" button, "Save Profile" button, "Save & Test More" button

### PROMPT-07: Style Profiles — StyleMetrics Component
**Branch:** `feat/sp-07-style-metrics`
**File:** `frontend/src/modules/style-profiles/components/StyleMetrics.tsx` (NEW)

Create `StyleMetrics`. Props: `fingerprint: VoiceFingerprint` (from `../types`).

Display 8 metric bars using shadcn `Progress`:
1. Readability: `fingerprint.vocabulary.reading_level` (scale 1-16, show as "Grade X")
2. Formality: derive from `fingerprint.vocabulary.rare_word_frequency` (0-100%)
3. Warmth: derive from `fingerprint.rhetorical.emotional_intensity` (0-100%)
4. Complexity: derive from `fingerprint.vocabulary.lexical_density` (0-100%)
5. Sentence Length: `fingerprint.sentence.avg_length` (words, show raw number)
6. Paragraph Length: `fingerprint.paragraph.avg_length` (sentences, show raw number)
7. Active Voice: derive as `100 - (fingerprint.sentence.complex_ratio * 100)` (0-100%)
8. Dialogue Use: `fingerprint.dialogue.dialogue_ratio` (0-100%)

Each bar: label on left, bar in middle, value + descriptor on right (e.g., "Easy", "Casual", "Warm").

### PROMPT-08: Style Profiles — VoiceCharacteristics Component
**Branch:** `feat/sp-08-voice-characteristics`
**File:** `frontend/src/modules/style-profiles/components/VoiceCharacteristics.tsx` (NEW)

Create `VoiceCharacteristics`. Props: `styleCard: StyleCard` (from `../types`).

Display as a definition list (dl/dt/dd) with rows:
- **POV:** Extract from `styleCard.summary` or show "See summary"
- **Tense:** Extract from `styleCard.summary` or show "See summary"
- **Tone:** `styleCard.tone`
- **Vocabulary:** `styleCard.vocabulary_level`
- **Sentence Style:** `styleCard.sentence_style`
- **Paragraph Style:** `styleCard.paragraph_style`
- **Rhetorical Style:** `styleCard.rhetorical_style`
- **Dialogue Style:** `styleCard.dialogue_style`

Style with border rounded-lg, alternating row backgrounds.

### PROMPT-09: Style Profiles — SampleComparison Component
**Branch:** `feat/sp-09-sample-comparison`
**File:** `frontend/src/modules/style-profiles/components/SampleComparison.tsx` (NEW)

Create `SampleComparison`. Props: `profileId: string`.

Use `useGenerateSample(profileId)` hook. On mount, auto-generate a comparison with prompt "Write a short passage demonstrating this style." (200 words).

Display:
- "Original (your sample):" — placeholder text: "Sample text from your uploaded writing..."
- "AI-generated in this style:" — the generated text from the mutation
- Similarity Score: use `useConformityCheck(profileId)` on the generated text to get `overall_score`. Show as "X/100" with green/yellow/red badge.
- "Generate Another Comparison" button to re-trigger generation

Show loading state while generating.

### PROMPT-10: Style Profiles — TestRefine Component
**Branch:** `feat/sp-10-test-refine`
**File:** `frontend/src/modules/style-profiles/components/TestRefine.tsx` (NEW)

Create `TestRefine`. Props: `profileId: string`.

UI:
- Topic textarea: "Give AI a topic and see how it writes in this style"
- Length toggle: Short (100 words) / Medium (300) / Long (600) — use radio buttons
- "Generate" button
- Generated text display with "Style Match" score (from conformity check)
- "Regenerate" and "Adjust Profile" buttons
- Fine-Tune section: 4 sliders using `<input type="range">`
  - Formality (0-100, default 50)
  - Warmth (0-100, default 50)
  - Sentence Length (0-100, default 50)
  - Complexity (0-100, default 50)
- "Apply Adjustments" button (logs slider values for now — backend tune endpoint to be wired later)

Use `useGenerateSample(profileId)` for text generation, `useConformityCheck(profileId)` for scoring.

### PROMPT-11: Style Profiles — Detail Page with Tabs
**Branch:** `feat/sp-11-detail-page`
**File:** `frontend/src/app/(dashboard)/style-profiles/[id]/page.tsx`

Read existing file. Rewrite as a tabbed detail page:
- Back link: "← Back to Profiles" → `/style-profiles`
- Header: profile name, genre badge, created date, sample count, active indicator
- Action buttons: "Edit Profile", "Test Style", "..." dropdown (Delete)
- 4 tabs using URL search params (`?tab=overview|samples|test|usage`):
  - **Overview** (default): Render `AnalysisResults`-like content inline (voice fingerprint, `StyleMetrics`, `VoiceCharacteristics`)
  - **Samples**: Show list of samples (word count, preview). "Add More Samples" button. "Re-Analyze" button.
  - **Test & Refine**: Render `TestRefine` component
  - **Usage**: Placeholder text "Coming soon — will show which manuscripts use this profile"

Use `useStyleProfile(id)`, `useStyleFingerprint(id)` hooks. Use `useSearchParams` for tab state.

### PROMPT-12: Style Profiles — i18n Messages
**Branch:** `feat/sp-12-i18n`
**File:** `frontend/messages/en/style-profiles.json` (NEW or update existing)

Check if `frontend/messages/en/style-profiles.json` exists. If not, create it. If `frontend/messages/en.json` has a `style-profiles` section, use that as base.

Add ALL the i18n keys from the spec's "i18n ADDITIONS" section under `styleProfiles`. Include keys for:
- Landing page: title, subtitle, newProfile, noProfiles, viewProfile, testStyle, activeIn, notInUse, samples, wordsAnalyzed
- Create wizard: all step labels, field labels, preset names, button labels
- Analysis: all section titles, metric labels, button labels
- Test & Refine: all labels, slider labels

---

## KNOWLEDGE VAULT — Frontend Components (Prompts 13-22)

### PROMPT-13: Knowledge Vault — EntryCard Enhancement
**Branch:** `feat/kv-13-entry-card`
**File:** `frontend/src/modules/knowledge/components/EntryCard.tsx`

Read existing `EntryCard.tsx`. Enhance to show:
- Entry type icon based on `source_type` or category in `metadata`:
  - "manual" → FileText icon, "url" → Globe icon, "file" → FileIcon, "clip" → Clipboard icon
- Title (font-semibold, line-clamp-1)
- Category tag if present in `metadata.category` (Badge)
- "Last modified" relative date (e.g., "3 days ago") — use `new Date(entry.updated_at || entry.created_at)`
- Tags as small chips (max 3 shown)
- Click navigates to `/knowledge/{entry.id}`

Use shadcn `Card`, `Badge`. Keep existing props interface.

### PROMPT-14: Knowledge Vault — Category Filter Enhancement
**Branch:** `feat/kv-14-category-filter`
**File:** `frontend/src/modules/knowledge/components/CategoryFilter.tsx` (NEW)

Create `CategoryFilter` component. Props:
- `categories: { name: string; count: number }[]`
- `selectedCategory: string | null`
- `onSelect: (category: string | null) => void`

Render pill buttons: "All (total)", then one per category with count.
Categories: Notes, Research, Characters, World-Building, References, Outlines.
Use horizontal scrollable flex container for mobile.
Selected pill gets primary bg color, others get secondary.

### PROMPT-15: Knowledge Vault — Landing Page Rewrite
**Branch:** `feat/kv-15-landing-page`
**File:** `frontend/src/app/(dashboard)/knowledge/page.tsx`

Read existing file. Enhance:
- Keep existing header with Import and New Entry buttons
- Replace `TagFilter` with `CategoryFilter` (import from `../../../modules/knowledge/components/CategoryFilter`)
- Derive categories from entries: group by `metadata.category` or `source_type`, count each
- Keep the existing `SearchBar` and search results display
- In the entry grid, pass entries filtered by selectedCategory
- Fix empty state: BookOpen icon, "Your Knowledge Vault is empty. Start building your research library.", two CTA buttons: "Create First Entry" and "Import Files"
- Keep existing delete dialog and import modal

### PROMPT-16: Knowledge Vault — New Entry Editor Page
**Branch:** `feat/kv-16-entry-editor`
**File:** `frontend/src/app/(dashboard)/knowledge/new/page.tsx` (NEW)

Create a full entry editor page:
- Back link: "← Knowledge Vault" → `/knowledge`
- Title input (large, no border, placeholder "Untitled Entry")
- Category dropdown: Notes, Research, Characters, World-Building, References, Outlines, Custom
- Tags chip input: text input, on Enter add tag chip, click X to remove
- Linked Project dropdown (optional): Use `useBooks()` from `@/modules/writing/hooks` to list projects
- Content textarea (large, min-height 300px) — plain textarea for now (rich editor in separate prompt)
- Auto-save using debounce (save 1.5s after last keystroke via `useCreateEntry` or `useUpdateEntry`)
- Save button in header

Use `useCreateEntry()` from `@/modules/knowledge/hooks`.

### PROMPT-17: Knowledge Vault — Entry Detail/Edit Page
**Branch:** `feat/kv-17-entry-detail`
**File:** `frontend/src/app/(dashboard)/knowledge/[id]/page.tsx`

Read existing file. Rewrite as a full editor:
- Use `useKnowledgeEntry(id)` to load entry
- Same layout as the "new" page but pre-populated
- Title, Category (from `metadata.category`), Tags, Linked Project, Content
- Use `useUpdateEntry(id)` for saves
- Add "Delete" button in header "..." menu (with confirmation dialog)
- Add "Attachments" section at bottom: list existing attachments (from `metadata.attachments` if any), "Add Attachment" button (file input, upload as base64 via `useUpdateEntry`)
- Show created/updated dates in header

### PROMPT-18: Knowledge Vault — Import Modal Enhancement
**Branch:** `feat/kv-18-import-modal`
**File:** `frontend/src/modules/knowledge/components/ImportModal.tsx`

Read existing `ImportModal.tsx`. Enhance to show 4 import options as cards:
1. **Upload Files**: DOCX, PDF, TXT, MD, EPUB. File input with drag-drop zone. On select, read file as base64, call `useImportEntry({ file_name, file_content_base64 })`.
2. **Import from URL**: Text input for URL. On submit, call `useImportEntry({ url })`.
3. **Paste Clipboard**: Textarea. On submit, call `useCreateEntry({ title: "Pasted content", content: text, source_type: "clip" })`.
4. **From Manuscript**: Use `useBooks()` + `useChapters(bookId)`. Select book → select chapter → import chapter content.

Show success toast with entry title after import. Close modal on success.
Use shadcn `Dialog`, `DialogContent`.

### PROMPT-19: Knowledge Vault — SearchBar Enhancement
**Branch:** `feat/kv-19-search-bar`
**File:** `frontend/src/modules/knowledge/components/SearchBar.tsx`

Read existing `SearchBar.tsx`. Enhance:
- Add placeholder: "Search your knowledge vault... (AI-powered)"
- Add search icon (Search from lucide)
- Show loading spinner inside input while searching
- Add keyboard shortcut: Ctrl+K / Cmd+K to focus search
- Debounce input by 300ms before triggering search
- Show "Press Enter to search" hint text when focused but not yet searched

### PROMPT-20: Knowledge Vault — Types Enhancement
**Branch:** `feat/kv-20-types`
**File:** `frontend/src/modules/knowledge/types.ts`

Read existing types.ts. Add new types:
```typescript
export type KnowledgeCategory = "notes" | "research" | "characters" | "world-building" | "references" | "outlines" | "custom";

export interface KnowledgeAttachment {
  id: string;
  file_name: string;
  file_url: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

export interface CreateEntryPayload {
  title: string;
  content: string;
  category?: KnowledgeCategory;
  tags?: string[];
  source_type?: string;
  project_id?: string;
  source_url?: string;
}

export interface UpdateEntryPayload {
  title?: string;
  content?: string;
  category?: KnowledgeCategory;
  tags?: string[];
  project_id?: string;
}
```

Keep all existing types. Don't break existing imports.

### PROMPT-21: Knowledge Vault — Hooks Enhancement
**Branch:** `feat/kv-21-hooks`
**File:** `frontend/src/modules/knowledge/hooks.ts`

Read existing hooks.ts. Add new hooks:
- `useCreateEntryFull()` — mutation using the new `CreateEntryPayload` type (with category, project_id)
- `useAttachments(entryId)` — query to `GET /api/v1/knowledge/{id}/attachments`
- `useUploadAttachment(entryId)` — mutation to `POST /api/v1/knowledge/{id}/attachments` (FormData)
- `useDeleteAttachment(entryId)` — mutation to `DELETE /api/v1/knowledge/{id}/attachments/{attId}`

Keep ALL existing hooks unchanged. Add new ones below.

### PROMPT-22: Knowledge Vault — i18n Messages
**Branch:** `feat/kv-22-i18n`
**File:** `frontend/messages/en/knowledge.json` (NEW or update existing)

Add all i18n keys from the spec for Knowledge Vault. Include:
- title, search placeholder, import, newEntry, noEntries, createFirst, importFiles
- Category labels: all, notes, research, characters, worldBuilding, references, outlines
- Entry editor: title, category, tags, linkedProject, attachments, addAttachment
- Import options: uploadFiles, fromUrl, pasteClipboard, fromManuscript

---

## PUBLISHING — Frontend Components (Prompts 23-34)

### PROMPT-23: Publishing — Stats Cards Component
**Branch:** `feat/pub-23-stats-cards`
**File:** `frontend/src/modules/publishing/components/StatsCards.tsx` (NEW)

Create `StatsCards`. Props:
- `accountCount: number`
- `activeListingCount: number`
- `pendingExportCount: number`
- `totalRevenue: number`

Display 4 stat cards in a `grid-cols-2 md:grid-cols-4` layout. Each card: label, large number, icon. Use shadcn `Card`. Revenue formatted as `$X,XXX`.

### PROMPT-24: Publishing — Tab Layout
**Branch:** `feat/pub-24-tab-layout`
**File:** `frontend/src/modules/publishing/components/PublishingTabs.tsx` (NEW)

Create `PublishingTabs` component using shadcn `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`.

5 tabs: Accounts, Exports, Listings, ISBNs, Pricing.
Props: `defaultTab?: string`. Use URL search params for tab state.
Each tab content renders a slot via children pattern or direct import:
- Accounts → `<AccountsTab />`
- Exports → `<ExportsTab />`
- Listings → `<ListingsTab />`
- ISBNs → `<ISBNsTab />`
- Pricing → `<PricingTab />`

Import these as lazy/dynamic components. Each tab is a placeholder `<div>Tab content coming soon</div>` — other prompts fill them in.

### PROMPT-25: Publishing — Landing Page Rewrite
**Branch:** `feat/pub-25-landing-page`
**File:** `frontend/src/app/(dashboard)/publishing/page.tsx`

Read existing file. Rewrite to:
- Header: "Publishing Operations" title + subtitle + "New Export" button (→ `/publishing/export`)
- `StatsCards` component with data from `usePublishingAccounts()` and `useListings()`
- `PublishingTabs` component below stats
- Remove the old flat layout (accounts section, connect form, listings section)

### PROMPT-26: Publishing — AccountsTab Component
**Branch:** `feat/pub-26-accounts-tab`
**File:** `frontend/src/modules/publishing/components/AccountsTab.tsx` (NEW)

Create `AccountsTab`. Refactor the existing account management from `page.tsx`:
- "Publishing Accounts" header + "Connect Account" button
- Connected accounts list using `AccountCard`
- Connect form (reuse existing logic from page.tsx)
- "Available Platforms" section: Show platform cards for unconnected platforms. Each with "Connect" button.
- Use `usePublishingAccounts()`, `useCreateAccount()`, `useDeleteAccount()`.

### PROMPT-27: Publishing — AccountCard Enhancement
**Branch:** `feat/pub-27-account-card`
**File:** `frontend/src/modules/publishing/components/AccountCard.tsx`

Read existing `AccountCard.tsx`. Enhance to show:
- Green/red status dot based on `is_active`
- Platform name (large, bold)
- Account name, email, region (if in metadata)
- Connected date
- Listing count (accept as prop or derive)
- "Manage" button and "Disconnect" button (with confirm dialog using `useDeleteAccount`)

### PROMPT-28: Publishing — ExportsTab Component
**Branch:** `feat/pub-28-exports-tab`
**File:** `frontend/src/modules/publishing/components/ExportsTab.tsx` (NEW)

Create `ExportsTab` with the full export workflow:
- Step 1: Book selector dropdown using `useBooks()` from `@/modules/writing/hooks`
- Step 2: Format cards — EPUB, Print PDF, DOCX, KPF (radio-style selection)
- Step 3: Configuration panel (changes per format):
  - EPUB: font, font size, line spacing, chapter breaks, TOC toggle, cover toggle, ISBN
  - Print PDF: trim size dropdown (5x8, 5.5x8.5, 6x9, 8.5x11), margins, font/size, page numbers, ISBN
  - DOCX: formatting style (manuscript, galley, clean)
  - KPF: same as EPUB
- Step 4: "Preview First 3 Chapters" button (no-op for now), "Export Manuscript" button
- Use `useExportEpub()` and `useExportPdf()` hooks. Toast on success.
- Export History section at bottom: placeholder list "Export history coming soon"

### PROMPT-29: Publishing — ListingsTab Component
**Branch:** `feat/pub-29-listings-tab`
**File:** `frontend/src/modules/publishing/components/ListingsTab.tsx` (NEW)

Create `ListingsTab`:
- Use `useListings()` hook
- Group listings by `book_id` (or `title`)
- Per book: card showing book title, then row per platform listing:
  - Platform name, status dot (green=live, yellow=pending, gray=not published), platform ID (ASIN/ISBN), price, reviews count, BSR
- Action buttons per book: "View All Platforms", "Update Pricing", "View Analytics" (all no-op for now)
- Empty state: "No listings yet. Publish your first book to see it here."

### PROMPT-30: Publishing — ISBNsTab Component
**Branch:** `feat/pub-30-isbns-tab`
**File:** `frontend/src/modules/publishing/components/ISBNsTab.tsx` (NEW)

Create `ISBNsTab`:
- "ISBN Management" header + "Add ISBN" button
- Table: ISBN, Format, Assigned To, Status (Available/In Use/Retired)
- "Add ISBN" dialog: ISBN input (validated as 13 digits), Format dropdown (Print/Ebook/Audiobook), optional Book assignment dropdown
- Unassigned count info: "You have N unassigned ISBNs"
- Barcode Generator section: ISBN dropdown, Price input, "Generate Barcode" button, Download PNG/SVG buttons (placeholder — just UI)
- Store ISBNs in local state for now (no backend hook yet — add `useISBNs` placeholder)

### PROMPT-31: Publishing — PricingTab Component
**Branch:** `feat/pub-31-pricing-tab`
**File:** `frontend/src/modules/publishing/components/PricingTab.tsx` (NEW)

Create `PricingTab`:
- Book selector dropdown using `useBooks()`
- Royalty Calculator table: Format | Price | Print Cost | Royalty % | Your Royalty
  - Kindle: price input, 70% royalty (or 35% if <$2.99 or >$9.99)
  - Paperback: price input, print cost estimate (based on page count × $0.012 + $0.85), 60% of (price - print cost)
  - Hardcover: price input, print cost ($0.012 × pages + $5.50), 60% of (price - print cost)
  - Audiobook: price input, 40% royalty
- Revenue projection: "At 100 sales/month: $X/mo across all formats"
- Competitor Price Comparison section: placeholder text "Competitor data from Market Research module"
- "Update Prices" button (no-op), "Price History" button (no-op)

### PROMPT-32: Publishing — Types Enhancement
**Branch:** `feat/pub-32-types`
**File:** `frontend/src/modules/publishing/types.ts`

Read existing types.ts. Add new types:
```typescript
export interface ISBN {
  id: string;
  isbn: string;
  format: string | null;
  book_id: string | null;
  book_title?: string;
  status: "available" | "in_use" | "retired";
  barcode_url: string | null;
  created_at: string;
}

export interface BookPricing {
  id: string;
  book_id: string;
  kindle_price: number | null;
  paperback_price: number | null;
  hardcover_price: number | null;
  audiobook_price: number | null;
  currency: string;
  updated_at: string;
}

export interface PricingHistory {
  id: string;
  book_id: string;
  format: string;
  old_price: number;
  new_price: number;
  changed_at: string;
}

export interface RoyaltyCalculation {
  print_cost: number;
  royalty_rate: number;
  royalty_amount: number;
}

export type ExportFormat = "epub" | "pdf" | "docx" | "kpf";

export interface ExportConfig {
  font_family?: string;
  font_size?: number;
  line_spacing?: number;
  trim_size?: string;
  chapter_breaks?: "page" | "section";
  include_toc?: boolean;
  include_cover?: boolean;
  cover_image_url?: string;
  isbn?: string;
  include_front_matter?: boolean;
  include_back_matter?: boolean;
}
```

Keep ALL existing types unchanged.

### PROMPT-33: Publishing — Hooks Enhancement
**Branch:** `feat/pub-33-hooks`
**File:** `frontend/src/modules/publishing/hooks.ts`

Read existing hooks.ts. Add new hooks below existing ones:
- `useISBNs()` — query `GET /api/v1/publishing/isbns`, returns `ISBN[]`
- `useCreateISBN()` — mutation `POST /api/v1/publishing/isbns`, body `{ isbn, format?, book_id? }`
- `useUpdateISBN(id)` — mutation `PATCH /api/v1/publishing/isbns/{id}`
- `useDeleteISBN()` — mutation `DELETE /api/v1/publishing/isbns/{id}`
- `useGenerateBarcode(id)` — mutation `POST /api/v1/publishing/isbns/{id}/generate-barcode`
- `useBookPricing(bookId)` — query `GET /api/v1/publishing/pricing/{bookId}`
- `useUpdatePricing(bookId)` — mutation `PATCH /api/v1/publishing/pricing/{bookId}`
- `useCalculateRoyalty()` — mutation `POST /api/v1/publishing/pricing/calculate-royalty`
- `useExportHistory()` — query `GET /api/v1/publishing/exports`

Use existing `publishingKeys` pattern. Add new keys. Keep ALL existing hooks unchanged.

### PROMPT-34: Publishing — i18n Messages
**Branch:** `feat/pub-34-i18n`
**File:** `frontend/messages/en/publishing.json` (NEW or update existing)

Add ALL i18n keys from the spec for Publishing. Include:
- title, subtitle, newExport
- Tab labels: accounts, exports, listings, isbns, pricing
- Stats labels: connectedAccounts, activeListings, pendingExports, totalRevenue
- Account labels: title, connectAccount, platform, accountName, email, connect, disconnect, manage
- Export labels: title, selectBook, format names, configuration fields, preview, export, history
- Listing labels: title, status values, action buttons
- ISBN labels: title, addIsbn, fields, status values, barcode labels
- Pricing labels: title, royaltyCalculator, field names, competitorComparison, buttons

---

## BACKEND — Database & Migrations (Prompts 35-38)

### PROMPT-35: Backend — Style Profiles DB Enhancement
**Branch:** `feat/be-35-sp-migration`
**File:** `backend/migrations_style_profiles.sql` (NEW)

Create a SQL migration file with:
```sql
-- Add columns to existing style_profiles table if they don't exist
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS preset VARCHAR(100);
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS voice_description TEXT;
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS tuning_adjustments JSONB DEFAULT '{}';
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS total_sample_words INTEGER DEFAULT 0;

-- Create style_profile_samples table
CREATE TABLE IF NOT EXISTS style_profile_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES style_profiles(id) ON DELETE CASCADE,
    label VARCHAR(255),
    source_type VARCHAR(50),
    source_reference UUID,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    file_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_style_profile_samples_profile ON style_profile_samples(profile_id);
```

### PROMPT-36: Backend — Knowledge Vault DB Enhancement
**Branch:** `feat/be-36-kv-migration`
**File:** `backend/migrations_knowledge_vault.sql` (NEW)

Create SQL migration:
```sql
-- Enhance knowledge_entries table
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'notes';
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS project_id UUID;
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS content_plain TEXT;
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category);

-- Create knowledge_attachments table
CREATE TABLE IF NOT EXISTS knowledge_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id UUID NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    file_name VARCHAR(500),
    file_url TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_attachments_entry ON knowledge_attachments(entry_id);
```

### PROMPT-37: Backend — Publishing DB Enhancement
**Branch:** `feat/be-37-pub-migration`
**File:** `backend/migrations_publishing.sql` (NEW)

Create SQL migration for all new publishing tables:
```sql
-- ISBNs table
CREATE TABLE IF NOT EXISTS isbns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    isbn VARCHAR(17) NOT NULL UNIQUE,
    format VARCHAR(50),
    book_id UUID,
    status VARCHAR(50) DEFAULT 'available',
    barcode_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_isbns_org ON isbns(org_id);

-- Book pricing
CREATE TABLE IF NOT EXISTS book_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    book_id UUID NOT NULL,
    kindle_price DECIMAL(10,2),
    paperback_price DECIMAL(10,2),
    hardcover_price DECIMAL(10,2),
    audiobook_price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_book_pricing_book ON book_pricing(book_id);

-- Pricing history
CREATE TABLE IF NOT EXISTS pricing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL,
    format VARCHAR(50),
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Manuscript exports enhancement
ALTER TABLE manuscript_exports ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';
ALTER TABLE manuscript_exports ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
```

### PROMPT-38: Backend — Publishing Accounts DB Enhancement
**Branch:** `feat/be-38-pub-accounts-migration`
**File:** `backend/migrations_publishing_accounts.sql` (NEW)

Create SQL migration:
```sql
-- Enhance publishing_accounts
ALTER TABLE publishing_accounts ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE publishing_accounts ADD COLUMN IF NOT EXISTS api_key_encrypted TEXT;

-- Enhance book_listings
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS format VARCHAR(50);
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS avg_rating FLOAT;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS bsr INTEGER;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_book_listings_book ON book_listings(book_id);
```

---

## BACKEND — API Routes (Prompts 39-48)

### PROMPT-39: Backend — Style Profiles Samples API
**Branch:** `feat/be-39-sp-samples-api`
**File:** `backend/app/modules/style_cloning/router.py`

Read existing router.py. Add 3 new endpoints (after existing ones):

```python
@router.post("/{profile_id}/samples", status_code=201)
async def add_sample(profile_id: uuid.UUID, body: AddSampleRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Add a text sample to a profile."""
    # Insert into style_profile_samples, update total_sample_words
    ...

@router.get("/{profile_id}/samples")
async def list_samples(profile_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    """List samples for a profile."""
    ...

@router.delete("/{profile_id}/samples/{sample_id}", status_code=204)
async def delete_sample(profile_id: uuid.UUID, sample_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Delete a sample."""
    ...
```

Add `AddSampleRequest` schema to `schemas.py`: `{ text: str, label: str | None, source_type: str = "paste", source_reference: uuid.UUID | None }`.
Add `SampleResponse` schema: `{ id, profile_id, label, source_type, word_count, file_name, created_at }`.

### PROMPT-40: Backend — Style Profiles Tune API
**Branch:** `feat/be-40-sp-tune-api`
**File:** `backend/app/modules/style_cloning/router.py`

Add endpoint to existing router:

```python
@router.patch("/{profile_id}/tune")
async def tune_profile(profile_id: uuid.UUID, body: TuneRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Adjust style tuning parameters."""
    # Update tuning_adjustments JSONB column
    ...
```

Add `TuneRequest` schema to `schemas.py`: `{ formality_adjust: float = 0, warmth_adjust: float = 0, sentence_length_adjust: float = 0, complexity_adjust: float = 0 }`.

Also add PATCH endpoint to update profile basic info (name, description, genre).

### PROMPT-41: Backend — Knowledge Vault Attachments API
**Branch:** `feat/be-41-kv-attachments-api`
**File:** `backend/app/modules/knowledge_vault/router.py`

Read existing router.py. Add 3 new endpoints:

```python
@router.post("/{entry_id}/attachments", status_code=201)
async def upload_attachment(entry_id: uuid.UUID, file: UploadFile, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Upload a file attachment to a knowledge entry."""
    # Save file (local or S3), insert into knowledge_attachments
    ...

@router.get("/{entry_id}/attachments")
async def list_attachments(entry_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.delete("/{entry_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(entry_id: uuid.UUID, attachment_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...
```

Add schemas: `AttachmentResponse` with `{ id, entry_id, file_name, file_url, file_size, mime_type, created_at }`.

### PROMPT-42: Backend — Knowledge Vault Category & URL Import
**Branch:** `feat/be-42-kv-category-import`
**File:** `backend/app/modules/knowledge_vault/router.py`

Add to existing router:

1. Endpoint to get entries filtered by category:
   - Add `category` query param to existing list endpoint
2. New endpoint for URL import:
```python
@router.post("/import-url")
async def import_from_url(body: ImportURLRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Import a web article as a knowledge entry."""
    # Use httpx to fetch URL, extract text (strip HTML), create entry
    ...
```

Add `ImportURLRequest` schema: `{ url: str }`.
Also update the existing entry creation to support `category` and `project_id` fields.

### PROMPT-43: Backend — Publishing ISBNs API
**Branch:** `feat/be-43-pub-isbns-api`
**File:** `backend/app/modules/publishing_ops/router.py`

Read existing router.py. Add ISBN endpoints:

```python
@router.get("/isbns")
async def list_isbns(db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.post("/isbns", status_code=201)
async def create_isbn(body: CreateISBNRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.patch("/isbns/{isbn_id}")
async def update_isbn(isbn_id: uuid.UUID, body: UpdateISBNRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.delete("/isbns/{isbn_id}", status_code=204)
async def delete_isbn(isbn_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.post("/isbns/{isbn_id}/generate-barcode")
async def generate_barcode(isbn_id: uuid.UUID, body: GenerateBarcodeRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Return placeholder URL for now
    return {"barcode_url": f"/api/v1/publishing/isbns/{isbn_id}/barcode.png"}
```

Add schemas to `schemas.py`: `CreateISBNRequest`, `UpdateISBNRequest`, `ISBNResponse`, `GenerateBarcodeRequest`.

### PROMPT-44: Backend — Publishing Pricing API
**Branch:** `feat/be-44-pub-pricing-api`
**File:** `backend/app/modules/publishing_ops/router.py`

Add pricing endpoints to existing router:

```python
@router.get("/pricing/{book_id}")
async def get_pricing(book_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.patch("/pricing/{book_id}")
async def update_pricing(book_id: uuid.UUID, body: UpdatePricingRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.post("/pricing/calculate-royalty")
async def calculate_royalty(body: RoyaltyCalcRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Calculate royalty for a given price/format/platform combo."""
    # KDP Kindle: 70% if $2.99-9.99, else 35%
    # KDP Print: 60% of (price - printing_cost)
    # Printing cost = page_count * 0.012 + 0.85
    ...
```

Add schemas: `UpdatePricingRequest`, `PricingResponse`, `RoyaltyCalcRequest`, `RoyaltyCalcResponse`.

### PROMPT-45: Backend — Publishing Export History API
**Branch:** `feat/be-45-pub-export-history`
**File:** `backend/app/modules/publishing_ops/router.py`

Add export history endpoints:

```python
@router.get("/exports")
async def list_exports(db=Depends(get_db), current_user=Depends(get_current_user)):
    """List all manuscript exports for the org."""
    ...

@router.get("/exports/{export_id}")
async def get_export(export_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    ...

@router.get("/exports/{export_id}/download")
async def download_export(export_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Return the download URL for a completed export."""
    ...
```

Add schemas: `ExportListResponse`, `ExportDetailResponse`.

### PROMPT-46: Backend — Publishing Schemas Enhancement
**Branch:** `feat/be-46-pub-schemas`
**File:** `backend/app/modules/publishing_ops/schemas.py`

Read existing schemas.py. Add ALL new Pydantic schemas needed:

```python
class CreateISBNRequest(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=17)
    format: str | None = None
    book_id: uuid.UUID | None = None

class UpdateISBNRequest(BaseModel):
    format: str | None = None
    book_id: uuid.UUID | None = None
    status: str | None = None

class ISBNResponse(BaseModel):
    id: uuid.UUID
    isbn: str
    format: str | None
    book_id: uuid.UUID | None
    status: str
    barcode_url: str | None
    created_at: datetime

class GenerateBarcodeRequest(BaseModel):
    price: float | None = None
    format: str = "png"  # png or svg

class UpdatePricingRequest(BaseModel):
    kindle_price: float | None = None
    paperback_price: float | None = None
    hardcover_price: float | None = None
    audiobook_price: float | None = None

class PricingResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    kindle_price: float | None
    paperback_price: float | None
    hardcover_price: float | None
    audiobook_price: float | None
    currency: str
    updated_at: datetime

class RoyaltyCalcRequest(BaseModel):
    price: float
    format: str
    platform: str
    page_count: int | None = None
    print_type: str | None = None

class RoyaltyCalcResponse(BaseModel):
    print_cost: float
    royalty_rate: float
    royalty_amount: float
```

Keep ALL existing schemas.

### PROMPT-47: Backend — Style Cloning Schemas Enhancement
**Branch:** `feat/be-47-sp-schemas`
**File:** `backend/app/modules/style_cloning/schemas.py`

Read existing schemas.py. Add:
```python
class AddSampleRequest(BaseModel):
    text: str = Field(..., min_length=1)
    label: str | None = None
    source_type: str = "paste"  # paste, upload, chapter
    source_reference: uuid.UUID | None = None

class SampleResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    label: str | None
    source_type: str | None
    word_count: int
    file_name: str | None
    created_at: datetime

class TuneRequest(BaseModel):
    formality_adjust: float = Field(0, ge=-1, le=1)
    warmth_adjust: float = Field(0, ge=-1, le=1)
    sentence_length_adjust: float = Field(0, ge=-1, le=1)
    complexity_adjust: float = Field(0, ge=-1, le=1)

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    genre: str | None = None
    preset: str | None = None
    voice_description: str | None = None
```

Keep ALL existing schemas.

### PROMPT-48: Backend — Knowledge Vault Schemas Enhancement
**Branch:** `feat/be-48-kv-schemas`
**File:** `backend/app/modules/knowledge_vault/schemas.py`

Read existing schemas.py. Add:
```python
class AttachmentResponse(BaseModel):
    id: uuid.UUID
    entry_id: uuid.UUID
    file_name: str | None
    file_url: str
    file_size: int | None
    mime_type: str | None
    created_at: datetime

class ImportURLRequest(BaseModel):
    url: str = Field(..., min_length=1)

class CreateEntryRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = ""
    category: str = "notes"
    tags: list[str] = Field(default_factory=list)
    source_type: str = "manual"
    project_id: uuid.UUID | None = None
    source_url: str | None = None
```

Keep ALL existing schemas.

---

## BACKEND — Services & Models (Prompts 49-54)

### PROMPT-49: Backend — Style Cloning Service Enhancement
**Branch:** `feat/be-49-sp-service`
**File:** `backend/app/modules/style_cloning/service.py`

Read existing service.py. Add functions:
- `add_sample(db, profile_id, org_id, text, label, source_type, source_reference)` — Insert into `style_profile_samples`, update `total_sample_words` on profile
- `list_samples(db, profile_id, org_id)` — Return list of `SampleResponse`
- `delete_sample(db, profile_id, sample_id, org_id)` — Delete sample, update word count
- `tune_profile(db, profile_id, org_id, adjustments)` — Update `tuning_adjustments` JSONB
- `update_profile(db, profile_id, org_id, updates)` — Update name, description, genre, preset, voice_description

Use existing patterns from the file (async SQLAlchemy, org_id scoping).

### PROMPT-50: Backend — Knowledge Vault Service Enhancement
**Branch:** `feat/be-50-kv-service`
**File:** `backend/app/modules/knowledge_vault/service.py`

Read existing service.py. Add functions:
- `create_entry_full(db, org_id, payload)` — Create entry with category, project_id, word_count calculation
- `update_entry(db, entry_id, org_id, payload)` — Update all fields
- `upload_attachment(db, entry_id, org_id, file_name, file_url, file_size, mime_type)` — Insert into knowledge_attachments
- `list_attachments(db, entry_id, org_id)` — Return list of attachments
- `delete_attachment(db, entry_id, attachment_id, org_id)` — Delete attachment
- `import_from_url(db, org_id, url)` — Fetch URL via httpx, strip HTML, create entry with content

### PROMPT-51: Backend — Publishing ISBN Service
**Branch:** `feat/be-51-pub-isbn-service`
**File:** `backend/app/modules/publishing_ops/service.py`

Read existing service.py. Add ISBN CRUD functions:
- `list_isbns(db, org_id)` — SELECT from isbns WHERE org_id
- `create_isbn(db, org_id, isbn, format, book_id)` — INSERT, validate ISBN format
- `update_isbn(db, isbn_id, org_id, updates)` — PATCH
- `delete_isbn(db, isbn_id, org_id)` — DELETE
- `generate_barcode(db, isbn_id, org_id, price, format)` — Return placeholder URL

### PROMPT-52: Backend — Publishing Pricing Service
**Branch:** `feat/be-52-pub-pricing-service`
**File:** `backend/app/modules/publishing_ops/service.py`

Add pricing functions to existing service:
- `get_pricing(db, book_id, org_id)` — SELECT from book_pricing
- `update_pricing(db, book_id, org_id, updates)` — UPSERT book_pricing, INSERT into pricing_history for changed fields
- `calculate_royalty(price, format, platform, page_count, print_type)` — Pure function:
  - KDP Kindle: 70% if $2.99-9.99, else 35%
  - KDP Print: 60% of (price - printing_cost). Printing cost = page_count * 0.012 + 0.85
  - IngramSpark: 40% wholesale discount. Royalty = price * 0.55 - printing_cost
  - ACX: 40% royalty share, 25% exclusive

### PROMPT-53: Backend — Publishing Export History Service
**Branch:** `feat/be-53-pub-export-service`
**File:** `backend/app/modules/publishing_ops/service.py`

Add export history functions:
- `list_exports(db, org_id)` — SELECT from manuscript_exports WHERE org_id, ORDER BY created_at DESC
- `get_export(db, export_id, org_id)` — Single export
- `get_export_download_url(db, export_id, org_id)` — Return file_url if status=complete

### PROMPT-54: Backend — Publishing Models Enhancement
**Branch:** `feat/be-54-pub-models`
**File:** `backend/app/modules/publishing_ops/models.py`

Read existing models.py. Add SQLAlchemy models:
```python
class ISBN(Base):
    __tablename__ = "isbns"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID, nullable=False)
    isbn = Column(String(17), unique=True, nullable=False)
    format = Column(String(50))
    book_id = Column(UUID)
    status = Column(String(50), default="available")
    barcode_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BookPricing(Base):
    __tablename__ = "book_pricing"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID, nullable=False)
    book_id = Column(UUID, nullable=False)
    kindle_price = Column(Numeric(10, 2))
    paperback_price = Column(Numeric(10, 2))
    hardcover_price = Column(Numeric(10, 2))
    audiobook_price = Column(Numeric(10, 2))
    currency = Column(String(10), default="USD")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class PricingHistory(Base):
    __tablename__ = "pricing_history"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID, nullable=False)
    format = Column(String(50))
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
```

Match existing model patterns (imports, Base class, etc).

---

## INTEGRATION & TESTING (Prompts 55-60)

### PROMPT-55: Integration — Wire Style Profile Detail Tabs
**Branch:** `feat/int-55-sp-detail-tabs`
**Files:** `frontend/src/app/(dashboard)/style-profiles/[id]/page.tsx`

Ensure the [id] page imports and renders:
- `StyleMetrics` from `@/modules/style-profiles/components/StyleMetrics`
- `VoiceCharacteristics` from `@/modules/style-profiles/components/VoiceCharacteristics`
- `SampleComparison` from `@/modules/style-profiles/components/SampleComparison`
- `TestRefine` from `@/modules/style-profiles/components/TestRefine`

Wire the Overview tab to show fingerprint data. Wire Test tab to show TestRefine. Wire Samples tab to show sample list with add/remove. Ensure all imports resolve. Run `npm run build` and fix any type errors.

### PROMPT-56: Integration — Wire Publishing Tab Components
**Branch:** `feat/int-56-pub-tabs`
**File:** `frontend/src/modules/publishing/components/PublishingTabs.tsx`

Update PublishingTabs to import and render actual tab content:
- `AccountsTab` for Accounts tab
- `ExportsTab` for Exports tab
- `ListingsTab` for Listings tab
- `ISBNsTab` for ISBNs tab
- `PricingTab` for Pricing tab

Use dynamic imports (`next/dynamic`) for code splitting. Run `npm run build` and fix any type errors.

### PROMPT-57: Integration — Module Index Exports
**Branch:** `feat/int-57-module-exports`

Update barrel export files:
- `frontend/src/modules/style-profiles/components/index.ts` — if it exists, add exports for all new components (PresetPicker, AnalysisResults, StyleMetrics, VoiceCharacteristics, SampleComparison, TestRefine). If it doesn't exist, create it.
- `frontend/src/modules/knowledge/components/index.ts` — same pattern, export CategoryFilter and any new components
- `frontend/src/modules/publishing/components/index.ts` — same, export all new tab components (StatsCards, PublishingTabs, AccountsTab, ExportsTab, ListingsTab, ISBNsTab, PricingTab)

### PROMPT-58: Testing — Style Profiles Build Verification
**Branch:** `feat/test-58-sp-build`

Run `npm run build` in `frontend/`. Fix ALL TypeScript errors related to style-profiles. Common issues:
- Missing imports
- Type mismatches between hooks and components
- Missing props
- i18n key mismatches

Do NOT change business logic — only fix compilation errors. After fixing, run build again to verify clean.

### PROMPT-59: Testing — Knowledge Vault Build Verification
**Branch:** `feat/test-59-kv-build`

Run `npm run build` in `frontend/`. Fix ALL TypeScript errors related to knowledge vault. Common issues:
- Missing imports
- Type mismatches
- Missing props on components
- PaginatedResponse type issues

Do NOT change business logic — only fix compilation errors.

### PROMPT-60: Testing — Publishing Build Verification
**Branch:** `feat/test-60-pub-build`

Run `npm run build` in `frontend/`. Fix ALL TypeScript errors related to publishing. Common issues:
- Missing imports
- New type definitions not matching hook return types
- Tab component import issues
- Missing shadcn components

Do NOT change business logic — only fix compilation errors.

---

## EXECUTION INSTRUCTIONS

### Create worktrees (31-60):
```bash
cd /c/Users/Shadow/selfpublisherforge
for i in $(seq 31 60); do
  git worktree add ../spf-vfix-worktrees/fix$(printf '%02d' $i) -b feat/fix$(printf '%02d' $i) main
done
```

### Run workers:
Workers 01-30 use existing worktrees fix01-fix30.
Workers 31-60 use new worktrees fix31-fix60.

Each worker:
1. `cd` into their worktree
2. `git checkout -b <branch-name>` (from the prompt)
3. Make the changes described
4. `npm run build` (frontend workers) or `python -m py_compile <file>` (backend workers)
5. `git add . && git commit -m "feat: <description>"`
6. `git push origin <branch-name>`

### Merge order (after all 60 complete):
1. Types & schemas first: 20, 32, 46, 47, 48
2. Hooks: 21, 33
3. DB migrations: 35, 36, 37, 38
4. Backend services: 49, 50, 51, 52, 53, 54
5. Backend routes: 39, 40, 41, 42, 43, 44, 45
6. Frontend components: 01-19, 23-31
7. i18n: 12, 22, 34
8. Pages: 02, 04, 05, 11, 15, 16, 17, 25
9. Integration: 55, 56, 57
10. Build verification: 58, 59, 60
