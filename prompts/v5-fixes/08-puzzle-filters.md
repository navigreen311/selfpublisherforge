cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-puzzle-filters

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Add/fix filter bar on Puzzle Books landing page. If missing, add search + status dropdown + sort dropdown. Wire up filtering.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Add/fix filter bar on Puzzle Books landing page. If missing, add search " && git push origin ai-feature/fix-puzzle-filters
