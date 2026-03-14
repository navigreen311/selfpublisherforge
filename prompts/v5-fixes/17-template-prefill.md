cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-template-prefill

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify all Use Template buttons on Coloring (8 templates) and Puzzle (8 templates) landing pages pre-fill the wizard. Templates should navigate to /new?template=NAME and wizard reads query param to pre-fill. Fix if broken.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify all Use Template buttons on Coloring (8 templates) and Puzzle (8 " && git push origin ai-feature/fix-template-prefill
