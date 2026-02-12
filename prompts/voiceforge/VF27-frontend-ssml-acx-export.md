# VF27: Frontend — SSMLEditor, ACXValidator, AudiobookExport

## Task
Create three audiobook studio sub-components.

## Files to Create

### `frontend/src/modules/audiobook/components/SSMLEditor.tsx`

Visual SSML editor (advanced view toggle):
- Side-by-side: plain text (left) and SSML-annotated text (right)
- Click a sentence → show and edit its SSML tags
- Visual indicators: colored badges for breaks, emphasis, prosody, voice switches, phonemes
- "Auto-generate SSML" button → calls API to generate SSML from plain text
- "Preview" button → generates audio for selected SSML segment
- "Reset to Plain Text" button
- Syntax highlighting for SSML tags (use a simple tokenizer, don't need a full XML editor)
- Show dialogue segments with character labels
- Show emotion annotations inline

### `frontend/src/modules/audiobook/components/ACXValidator.tsx`

Pre-submission validation dashboard:
- Run validation button → calls POST /audiobooks/{id}/validate
- Checklist with pass/fail icons for each ACX requirement:
  - File format (MP3 CBR 192kbps)
  - Sample rate (44.1kHz)
  - Mono channel
  - Peak level ≤ -3dB
  - RMS between -23dB and -18dB
  - Noise floor < -60dB
  - Head room tone (0.5-1s)
  - Tail room tone (1-5s)
  - Per-chapter file length ≤ 120 min
  - Opening credits file present
  - Closing credits file present
- Overall score badge: "ACX Ready" (green) or "X issues to fix" (yellow/red)
- "Auto-Fix" button for fixable issues (normalize, add room tone, convert format)
- Per-chapter expandable results
- Export validated files button

### `frontend/src/modules/audiobook/components/AudiobookExport.tsx`

Export configuration modal/panel:
- Platform selector: ACX/Audible, Findaway Voices, Authors Republic, Google Play, Custom
- When platform selected, auto-configure settings (format, bitrate, sample rate, channels)
- Settings overrides: format dropdown, bitrate input, sample rate input
- Metadata editor: title, subtitle, author, narrator credits, copyright, description, genre (all text inputs)
- Include cover art checkbox + cover art preview
- Include retail sample checkbox (first 5 min)
- "Start Export" button → shows progress bar
- When complete: download button (ZIP of chapter files or single M4B)
- Export history list (previous exports with download links)

Build all three as complete, styled components using shadcn/ui and Tailwind.

```tsx
// ACXValidator example structure
interface ACXValidatorProps {
  projectId: string;
  validationResult?: ACXValidationResult;
  onValidate: () => void;
  onAutoFix: (issues: string[]) => void;
  isValidating: boolean;
}
```
