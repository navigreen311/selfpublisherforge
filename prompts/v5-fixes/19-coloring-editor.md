cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-coloring-editor

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify/enhance Coloring Books editor at [id]/page.tsx. Must have: left panel (page thumbnails), center (page preview), right panel (illustration prompt, generate/upload, quality pipeline, post-processing controls, simulation preview, border/difficulty/caption).

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify/enhance Coloring Books editor at [id]/page.tsx. Must have: left p" && git push origin ai-feature/fix-coloring-editor
