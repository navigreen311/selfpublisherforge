cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-puzzle-verify

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Fix Puzzle Books: verify skeleton works, change Kids age '4-8' to '5-10' in all puzzle files. Search and replace across page.tsx, new/page.tsx, types, hooks.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Fix Puzzle Books: verify skeleton works, change Kids age '4-8' to '5-10'" && git push origin ai-feature/fix-puzzle-verify
