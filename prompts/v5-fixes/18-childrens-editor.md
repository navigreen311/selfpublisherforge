cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-childrens-editor

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify/enhance Children's Books editor at [id]/page.tsx. Must have: left panel (page thumbnails), center (two-page spread), right panel (layout selector 7 options, text editor, illustration prompt, generate/upload buttons, character toggle). If placeholder, build it out.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify/enhance Children's Books editor at [id]/page.tsx. Must have: left" && git push origin ai-feature/fix-childrens-editor
