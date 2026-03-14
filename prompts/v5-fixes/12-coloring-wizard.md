cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-coloring-wizard-steps

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify/complete Coloring wizard Steps 2 (Page Count/Trim/6 Line Art styles/Line Weight/Uniformity/Complexity/Page Options) and 3 (Theme/Generation Method/Include checkboxes: title page, belongs-to, color test, progress tracker, certificate, difficulty).

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify/complete Coloring wizard Steps 2 (Page Count/Trim/6 Line Art styl" && git push origin ai-feature/fix-coloring-wizard-steps
