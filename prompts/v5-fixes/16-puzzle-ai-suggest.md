cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-puzzle-ai-suggest

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify/implement AI Suggest button for Puzzle subtitle. Generate subtitle from title+types+difficulty using template: '{count} {types} Puzzles with Answers — {difficulty}'. If button does nothing, implement it.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify/implement AI Suggest button for Puzzle subtitle. Generate subtitl" && git push origin ai-feature/fix-puzzle-ai-suggest
