cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-coloring-series

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify Coloring wizard Step 1 series toggle. When ON, must show Series Name input and Volume Number dropdown. If missing, add.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify Coloring wizard Step 1 series toggle. When ON, must show Series N" && git push origin ai-feature/fix-coloring-series
